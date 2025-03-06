const puppeteer = require('puppeteer'); // Ensure you have puppeteer installed
require('dotenv').config(); // Read environment variables from .env
let Utils = require("./utils.js");
const fs = require('fs');

const ARGS = Utils.getArguments();
const PASSWORD = ARGS["password"];
const USER = ARGS["user"];

// Create a network log file (clear previous logs)
const NETWORK_LOG_FILE = 'network_log.txt';
fs.writeFileSync(NETWORK_LOG_FILE, '', { encoding: 'utf8' });

function delay(time) {
  return new Promise(resolve => setTimeout(resolve, time));
}

function logMessage(message) {
  console.log(message);
}

(async () => {

  const windowWidth = 1920;
  const windowHeight = 1080;
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true, // Set to false if you want to see the browser actions
      executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
      args: ['--incognito']
    });
  } catch (e) {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--start-fullscreen', '--incognito']
    });
  }

  const [page] = await browser.pages();
  await page.setViewport({
    width: windowWidth,
    height: windowHeight
  });
  const timeout = 15000;
  page.setDefaultTimeout(timeout);

  // -----------------------------------------------------------
  // SET UP TOKEN CAPTURE PROMISE
  // -----------------------------------------------------------
  let bearerToken = null;
  let tokenCapturedResolver;
  const tokenCapturedPromise = new Promise(resolve => {
    tokenCapturedResolver = resolve;
  });

  // -----------------------------------------------------------
  // SET UP NETWORK RESPONSE INTERCEPTION WITH LOGGING AND FILTERING
  // -----------------------------------------------------------
  const tokenResponseHandler = async response => {
    try {
      const url = response.url();
      const status = response.status();
      let text = '';
      try {
        text = await response.text();
      } catch (e) {
        text = 'Could not read response body.';
      }
      const logEntry = `URL: ${url}\nStatus: ${status}\nResponse Snippet: ${text.substring(0,200)}\n--------------------------------\n`;
      fs.appendFileSync(NETWORK_LOG_FILE, logEntry, { encoding: 'utf8' });

      // Filter responses: process if the URL is the OAuth token endpoint,
      // the response contains a bearer token indicator, the "Pacman" keyword,
      // and the expected scope fragment.
      if (
        url.includes("/oauth2/v2.0/token") &&
        (text.includes('"token_type":"Bearer"') || text.includes('"tokenType":"Bearer"')) &&
        text.includes("sydney")
      ) {
        let json;
        try {
          json = JSON.parse(text);
        } catch (e) {
          // Fallback: attempt to extract the token using regex if JSON parsing fails.
        }
        if (json && json.access_token) {
          bearerToken = json.access_token;
          console.log("Bearer token captured: " + bearerToken);
          page.off('response', tokenResponseHandler);
          if (tokenCapturedResolver) {
            tokenCapturedResolver(bearerToken);
            tokenCapturedResolver = null;
          }
        } else {
          // Fallback using regex extraction for "access_token"
          const match = text.match(/"access_token"\s*:\s*"([^"]+)"/);
          if (match && match[1]) {
            bearerToken = match[1];
            console.log("Bearer token captured (via regex): " + bearerToken);
            page.off('response', tokenResponseHandler);
            if (tokenCapturedResolver) {
              tokenCapturedResolver(bearerToken);
              tokenCapturedResolver = null;
            }
          }
        }
      }
    } catch (err) {
      console.error("Error capturing network response: ", err);
    }
  };

  page.on('response', tokenResponseHandler);

  // -----------------------------------------------------------
  // ORIGINAL, WORKING UI/Journey for Login and Navigation
  // -----------------------------------------------------------
  await page.goto('https://www.office.com/');

  await page.waitForSelector('#mectrl_headerPicture', { timeout });
  await page.click('#mectrl_headerPicture');

  await page.waitForSelector('#i0116', { timeout });
  await page.type('#i0116', USER);
  await page.click('#idSIButton9');

  await delay(2000);
  await page.waitForSelector('#i0118', { timeout });
  await page.type('#i0118', PASSWORD);
  logMessage("Entering password...");
  await page.click('#idSIButton9');

  await delay(5000);
  await page.waitForSelector('#idSIButton9', { timeout });
  await page.click('#idSIButton9'); // Click "Stay signed in"

  logMessage("Successfully logged in.");
  await delay(10000);
  await delay(10000); // Extra delay to avoid sync issues

  console.log("Starting user journey to get the Pacman token");

  // Navigate to the CoPilot URL (this action should trigger the network request that contains the token)
  {
    const targetPage = page;
    await puppeteer.Locator.race([
      targetPage.locator('#d870f6cd-4aa5-4d42-9626-ab690c041429'),
    ])
      .setTimeout(timeout)
      .click();
  }
  await delay(10000); // Wait for network activity

  console.log("Completed user journey, capturing Pacman token from network responses");

  // -----------------------------------------------------------
  // WAIT FOR THE TOKEN OR TIMEOUT
  // -----------------------------------------------------------
  const token = await Promise.race([
    tokenCapturedPromise,
    delay(60000).then(() => null)  // timeout after 60 seconds
  ]);

  // -----------------------------------------------------------
  // OUTPUT THE CAPTURED TOKEN TO A FILE
  // -----------------------------------------------------------
  if (bearerToken) {
    fs.writeFileSync('token_output.txt', bearerToken, { encoding: 'utf8' });
    console.log('access_token: ' + bearerToken);
    await browser.close();
    return bearerToken;
    process.exit(0);
  } else {
    fs.writeFileSync('token_output.txt', '❌ No valid token captured from network responses.', { encoding: 'utf8' });
    console.log('❌ No valid token captured from network responses.');
    await browser.close();
    return null;
    process.exit(1);
  }

  return bearerToken;
  await browser.close();

})().catch(err => {
  console.error(err);
  process.exit(1);
});



/*
const puppeteer = require('puppeteer');
const fs = require('fs');
require('dotenv').config();
let Utils = require("./utils.js");

const ARGS = Utils.getArguments();
const PASSWORD = ARGS["password"];
const USER = ARGS["user"];

const LOG_FILE = 'new_debug_log.txt';
const LOCAL_STORAGE_DUMP = 'new_localStorageDump.json';

// Clear logs at the start
fs.writeFileSync(LOG_FILE, '', { encoding: 'utf8' });
fs.writeFileSync(LOCAL_STORAGE_DUMP, '', { encoding: 'utf8' });

function logMessage(message) {
    fs.appendFileSync(LOG_FILE, message + "\n", { encoding: 'utf8' });
    console.log(message);
}

function delay(time) {
    return new Promise(resolve => setTimeout(resolve, time));
}

(async () => {
    let browser;
    try {
        browser = await puppeteer.launch({
            headless: false, // Set to true if you want it to run silently
            executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            args: ['--incognito']
        });
    } catch (e) {
        logMessage("Primary launch failed, trying fallback...");
        browser = await puppeteer.launch({
            headless: false,
            args: ['--start-fullscreen', '--incognito']
        });
    }

    const [page] = await browser.pages();
    await page.setViewport({ width: 2020, height: 1280 });
    const timeout = 15000;
    page.setDefaultTimeout(timeout);

    // ==== STEP 1: Login Process ====
    logMessage("Starting the login process...");
    await page.goto('https://www.office.com/');

    await page.waitForSelector('#mectrl_headerPicture', { timeout });
    await page.click('#mectrl_headerPicture');

    await page.waitForSelector('#i0116', { timeout });
    await page.type('#i0116', USER);
    await page.click('#idSIButton9');

    await delay(2000);
    await page.waitForSelector('#i0118', { timeout });
    await page.type('#i0118', PASSWORD);
    logMessage("Entering password...");
    await page.click('#idSIButton9');

    await delay(5000);
    await page.waitForSelector('#idSIButton9', { timeout });
    await page.click('#idSIButton9'); // Click "Stay signed in"

    logMessage("Successfully logged in.");
    await delay(10000);

    await delay(10000); // Wait for 10 seconds to avoid sync issues

    console.log("Starting user journey to get the substrate token");

    // Go to the CoPilot URL
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('#d870f6cd-4aa5-4d42-9626-ab690c041429'),
        ])
            .setTimeout(timeout)
            .click();
    }

    await delay(10000); // Wait for 10 seconds to avoid sync issues

    await page.goto('https://outlook.office.com');

    await delay(10000);

    // ==== STEP 3: Extract LocalStorage ====
    logMessage("Extracting localStorage contents...");

    const localStorageContents = await page.evaluate(() => {
        const items = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            items[key] = localStorage.getItem(key);
        }
        return items;
    });

    // Save full localStorage contents for debugging
    fs.writeFileSync(LOCAL_STORAGE_DUMP, JSON.stringify(localStorageContents, null, 2), { encoding: 'utf8' });
    logMessage("✅ Saved localStorage dump to localStorageDump.json.");

    // ==== STEP 4: Extract the Bearer Token ====
    logMessage("Parsing tokens from localStorage...");

    let foundToken = null;
    for (const key of Object.keys(localStorageContents)) {
        let parsedData;
        try {
            parsedData = JSON.parse(localStorageContents[key]);
        } catch (e) {
            continue; // Skip non-JSON entries
        }

        if (parsedData && parsedData.secret && parsedData.tokenType === "Bearer") {
            if (key.includes("https://substrate.office.com/.default--")) {
                foundToken = parsedData.secret;
                return foundToken;
            }
        }
    }

    if (foundToken) {
        logMessage("✅ Extracted Bearer Token:");
        logMessage(foundToken);
        console.log("\n=== Bearer Token ===\n" + foundToken + "\n====================\n");
    } else {
        logMessage("❌ No valid token found.");
        console.log("❌ No valid token found.");
        return null;
    }

    await browser.close();

})().catch(err => {
    fs.appendFileSync(LOG_FILE, `Error: ${err}\n`, { encoding: 'utf8' });
    console.error(err);
    process.exit(1);
});
*/




