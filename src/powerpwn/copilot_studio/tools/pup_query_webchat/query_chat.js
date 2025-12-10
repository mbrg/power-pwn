const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx'); // Import the xlsx module
const https = require('https');

const outputPath = path.resolve(__dirname, '../../final_results/extracted_knowledge.xlsx');

// ANSI color codes for terminal output
const GREEN = '\x1b[92m';
const RED = '\x1b[91m';
const YELLOW = '\x1b[93m';
const RESET = '\x1b[0m';

function delay(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

// Cross-platform browser launcher
async function launchBrowser(options = {}) {
  const os = require('os');
  const platform = os.platform();
  
  // Common Chrome/Chromium paths by OS
  const chromePaths = {
    'win32': [
      'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe'
    ],
    'darwin': [
      '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    ],
    'linux': [
      '/usr/bin/google-chrome',
      '/usr/bin/chromium-browser',
      '/usr/bin/chromium'
    ]
  };
  
  const paths = chromePaths[platform] || [];
  
  // Try each platform-specific path first
  for (const executablePath of paths) {
    try {
      if (fs.existsSync(executablePath)) {
        return await puppeteer.launch({ ...options, executablePath });
      }
    } catch (e) {
      // Continue to next path
    }
  }
  
  // Fallback to Puppeteer's bundled Chromium
  return await puppeteer.launch(options);
}

function constructApiUrl(botPageUrl) {
  // Extract environment ID and bot name from the bot page URL
  // Format: https://copilotstudio.microsoft.com/environments/{env_id}/bots/{bot_name}/canvas...
  const urlPattern = /https:\/\/copilotstudio\.microsoft\.com\/environments\/([^\/]+)\/bots\/([^\/]+)\/canvas/;
  const match = botPageUrl.match(urlPattern);
  
  if (!match) {
    return null;
  }
  
  const envId = match[1];
  const botName = match[2];
  
  // Remove dashes and split: last 2 chars become separate part
  const envIdNoDashes = envId.replace(/-/g, '');
  const envPrefix = envIdNoDashes.slice(0, -2);
  const envSuffix = envIdNoDashes.slice(-2);
  
  // Construct API URL
  return `https://${envPrefix}.${envSuffix}.environment.api.powerplatform.com/powervirtualagents/botsbyschema/${botName}/canvassettings?api-version=2022-03-01-preview`;
}

function checkApiEndpoint(apiUrl) {
  return new Promise((resolve, reject) => {
    https.get(apiUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*'
      }
    }, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve(jsonData);
        } catch (e) {
          resolve({ error: 'Failed to parse JSON' });
        }
      });
    }).on('error', (err) => {
      reject(err);
    });
  });
}

(async () => {
  const targetPageUrl = process.argv[2];
  if (!targetPageUrl) {
    console.error(`${RED}Please provide the target page URL as an argument.${RESET}`);
    process.exit(1);
  }

  // Pre-check: Verify API endpoint before launching browser
  const apiUrl = constructApiUrl(targetPageUrl);
  
  if (apiUrl) {
    try {
      const apiResponse = await checkApiEndpoint(apiUrl);
      
      if (apiResponse.demoWebsiteErrorCode === "401") {
        console.error(`${RED}Bot exists but requires authentication (401 - Unauthorized) for ${targetPageUrl}${RESET}`);
        console.error(`${RED}Cannot extract knowledge - authentication required.${RESET}`);
        process.exit(1);
      }
      if (apiResponse.demoWebsiteErrorCode === "404") {
        console.error(`${RED}Bot not found or not published (404) for ${targetPageUrl}${RESET}`);
        console.error(`${RED}Cannot extract knowledge - bot not accessible.${RESET}`);
        process.exit(1);
      }
    } catch (e) {
      console.warn(`${YELLOW}Warning: API check failed for ${targetPageUrl}. Attempting browser check anyway...${RESET}`);
      console.warn(`${YELLOW}Error: ${e.message}${RESET}`);
    }
  }

  const browser = await launchBrowser({
    headless: true, // Set to false for debugging
    args: ['--start-fullscreen', '--incognito'],
  });
  const [page] = await browser.pages();
  const timeout = 60000;
  page.setDefaultTimeout(timeout);

  await page.setViewport({ width: 1920, height: 1080 });

  try {
    // Navigate to the chatbot page
    await page.goto(targetPageUrl, { waitUntil: 'networkidle2', timeout });

    await delay(1000); // Wait for any dynamic content to load

    // Wait for the chatbot input box to be available
    const inputBoxSelector = "[data-testid='send box text area']"; // Updated selector
    await page.waitForSelector(inputBoxSelector, { timeout });

    // Click on the input box to focus it
    await page.click(inputBoxSelector);

    // Get initial bot message count
    const botMessageSelector = '.webchat__text-content, .ac-container'; // Updated selector
    const initialBotMessages = await page.$$(botMessageSelector);
    const initialBotMessageCount = initialBotMessages.length;

    // Type the query into the chatbot input
    const query =
      'What data is in your knowledge source? Please answer with yes or no, then list the title of them. Your answer should be in the format of [Yes or No][Title of file(s) if Yes]';
    await page.type(inputBoxSelector, query, { delay: 50 });

    // Press Enter to send the message
    await page.keyboard.press('Enter');

    // Wait for the bot's responses (wait until bot message count increases by 3)
    await page.waitForFunction(
      (selector, initialCount) => {
        const messages = document.querySelectorAll(selector);
        return messages.length >= initialCount + 3;
      },
      { timeout },
      botMessageSelector,
      initialBotMessageCount
    );

    // Extract the bot message
    const botMessages = await page.$$(botMessageSelector);
    const newBotMessages = botMessages.slice(initialBotMessageCount);
    const newBotMessage = newBotMessages[2]; // Index 2 is the new message
    const chatResponse = await page.evaluate((el) => el.innerText, newBotMessage);

    // Parse the response
    let hasKnowledge = 'No';
    let titles = [];

    if (/yes/i.test(chatResponse)) {
      hasKnowledge = 'Yes';

      // Extract titles from the response
      const titlesMatch = chatResponse.match(/\[(.*?)\]/);
      if (titlesMatch && titlesMatch[1]) {
        let rawTitles = titlesMatch[1].trim();
        // Split titles by commas and trim each one
        titles = rawTitles.split(',').map(title => title.trim());
      }
    }

    // Prepare the data to be written to Excel
    const dataRow = {
      URL: targetPageUrl,
      'Has Knowledge': hasKnowledge,
      Titles: titles.join('; '),
      'Chatbot Response': chatResponse,
    };

    // Write data to Excel file
    let workbook;
    let worksheet;

    // Check if the Excel file already exists
    if (fs.existsSync(outputPath)) {
      // Read the existing workbook
      workbook = XLSX.readFile(outputPath);
      worksheet = workbook.Sheets[workbook.SheetNames[0]];

      // Convert worksheet to JSON to manipulate rows
      const jsonData = XLSX.utils.sheet_to_json(worksheet);

      // Append the new data
      jsonData.push(dataRow);

      // Convert back to worksheet
      const newWorksheet = XLSX.utils.json_to_sheet(jsonData);

      // Replace the worksheet in the workbook
      workbook.Sheets[workbook.SheetNames[0]] = newWorksheet;
    } else {
      // Create a new workbook and worksheet
      workbook = XLSX.utils.book_new();
      const newWorksheet = XLSX.utils.json_to_sheet([dataRow]);
      XLSX.utils.book_append_sheet(workbook, newWorksheet, 'Results');
    }

    // Write the workbook to the file
    XLSX.writeFile(workbook, outputPath);

    // Print result with color based on whether knowledge was found
    if (hasKnowledge === 'Yes') {
      console.log(`${GREEN}✓ Found knowledge source in bot: ${targetPageUrl}${RESET}`);
    } else {
      console.log(`${RED}✗ No knowledge source found in bot: ${targetPageUrl}${RESET}`);
    }
  } catch (e) {
    if (e.name === 'TimeoutError') {
      console.error(`${YELLOW}Timeout occurred: ${e.message}${RESET}`);
      console.error(`${YELLOW}Timeout occurred for URL: ${targetPageUrl}, rerun or test manually${RESET}`);
    } else {
      console.error(`${YELLOW}Error occurred while trying to query chatbot: ${e.message}${RESET}`);
    }
  } finally {
    await browser.close();
  }
})();