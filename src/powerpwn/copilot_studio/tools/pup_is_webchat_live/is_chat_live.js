const puppeteer = require('puppeteer'); // v22.0.0 or later
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path'); // Import the path module
const chalk = require('chalk'); // for colors in terminal texts
const https = require('https');
const os = require('os');
// todo: install chalk > 4

function delay(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time)
    });
}

// Cross-platform browser launcher
async function launchBrowser(options = {}) {
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
      if (fsSync.existsSync(executablePath)) {
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
        console.error("Please provide the target page URL as an argument.");
        process.exit(1);
    }

    const orange = chalk.hex('#FFA500'); // Define a custom orange color
    const maxRetries = 2; // Total attempts: 1 initial + 1 retry
    
    // Pre-check: Verify API endpoint before launching browser
    const apiUrl = constructApiUrl(targetPageUrl);
    
    if (apiUrl) {
        try {
            const apiResponse = await checkApiEndpoint(apiUrl);

            if (apiResponse.demoWebsiteErrorCode === "401") {
                process.stdout.write(chalk.yellow(`Bot exists but requires authentication (401 - Unauthorized) for ${targetPageUrl}, skipping browser check.\n`));
                process.exit(0);
            }
            if (apiResponse.demoWebsiteErrorCode === "404") {
                process.stdout.write(chalk.yellow(`Bot not found or not published (404) for ${targetPageUrl}, skipping browser check.\n`));
                process.exit(0);
            }
        } catch (e) {
            process.stdout.write(orange(`Bot exists but is likely publicly inaccessible (API check failed) for ${targetPageUrl}, skipping browser check.\n`));
            process.exit(0);
        }
    }
    
    const browser = await launchBrowser({ 
        headless: true, 
        args: ['--start-fullscreen', '--incognito']
    });
    
    let attempt = 0;
    let success = false;
    
    while (attempt < maxRetries && !success) {
        attempt++;
        if (attempt > 1) {
            process.stdout.write(chalk.blue(`Retrying (attempt ${attempt}/${maxRetries}) after timeout...\n`));
            await delay(5000); // Wait 5 seconds before retry
        }
        
        const page = await browser.newPage();
        const timeout = 30000;
        page.setDefaultTimeout(timeout);

        await page.setViewport({
            width: 1920,
            height: 1080
        });

        try {
            await page.goto(targetPageUrl, {
                waitUntil: 'networkidle2'
            });

            await delay(1000); // Wait for 1 second to avoid sync issues
            await page.waitForSelector('div.webchat__bubble__content > div', { timeout: timeout });

            const chatTexts = await page.evaluate(() => {
                const elements = document.querySelectorAll('div.webchat__bubble__content > div')
                return Array.from(elements).map(element => element.innerText);
            });

            const stringsToCheck = ["I'll need you to sign in", "Error code:"];

            const allStringsAbsent = stringsToCheck.every(str => chatTexts.every(text => !text.includes(str)));

            if (allStringsAbsent) {
                process.stdout.write(chalk.green(`Found open chatbot at: ${targetPageUrl}\n`));
                const outputPath = path.resolve(__dirname, '../../final_results/chat_exists_output.txt');
                await fs.appendFile(outputPath, targetPageUrl + '\n');
            } else {
                process.stdout.write(chalk.red("Found inaccessible chatbot.\n"));
            }
            
            success = true; // Mark as successful if we reach here
            await page.close();
        } catch (e) {
            await page.close();
            
            if (e.name === 'TimeoutError') {
                if (attempt >= maxRetries) {
                    process.stdout.write(chalk.yellow(`Timeout occurred for URL: ${targetPageUrl} after ${maxRetries} attempts, rerun or test manually\n`));
                }
                // Continue to next iteration for retry
            } else {
                process.stdout.write(orange("Error occurred while trying to find chat texts:", e));
                break; // Don't retry on non-timeout errors
            }
        }
    }

    await browser.close();
})().catch(err => {
    console.error(err);
    process.exit(1);
});
