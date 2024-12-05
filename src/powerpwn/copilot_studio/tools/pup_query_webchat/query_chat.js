const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');
const XLSX = require('xlsx'); // Import the xlsx module

const outputPath = path.resolve(__dirname, '../../final_results/chat_exists_output.xlsx');

function delay(time) {
  return new Promise((resolve) => setTimeout(resolve, time));
}

(async () => {
  const targetPageUrl = process.argv[2];
  if (!targetPageUrl) {
    console.error('Please provide the target page URL as an argument.');
    process.exit(1);
  }

  const browser = await puppeteer.launch({
    headless: false, // Set to false for debugging
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
    const inputBoxSelector = '.webchat__send-box-text-box__input'; // Update if necessary
    await page.waitForSelector(inputBoxSelector, { timeout });

    // Click on the input box to focus it
    await page.click(inputBoxSelector);

    // Get initial bot message count
    const botMessageSelector = '[id^="webchat__stacked-layout__id--"] p'; // Updated selector
    const initialBotMessages = await page.$$(botMessageSelector);
    const initialBotMessageCount = initialBotMessages.length;

    // Type the query into the chatbot input
    const query =
      'Do you have any knowledge source files? Please answer with yes or no, then list the title of them. Your answer should be in the format of [Yes or No][Title of file(s) if Yes]';
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

    console.log(`Processed chatbot at: ${targetPageUrl}`);
  } catch (e) {
    if (e.name === 'TimeoutError') {
      console.error(`Timeout occurred: ${e.message}`);
      console.error(`Timeout occurred for URL: ${targetPageUrl}, rerun or test manually`);
    } else {
      console.error(`Error occurred while trying to query chatbot: ${e.message}`);
    }
  } finally {
    await browser.close();
  }
})();













