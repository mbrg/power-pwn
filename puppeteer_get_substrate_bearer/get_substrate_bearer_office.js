const puppeteer = require('puppeteer'); // Ensure you have puppeteer installed
require('dotenv').config(); // Read environment variables from .env
let Utils = require("./utils.js");
const fs = require('fs');

const ARGS = Utils.getArguments();
const PASSWORD = ARGS["password"];
const USER = ARGS["user"];
const DEBUGMODE = ARGS["debugMode"]

// Create a network log file (clear previous logs) only if DEBUGMODE is 'true'
const NETWORK_LOG_FILE = 'network_log.txt';
if (DEBUGMODE === 'true') {
  fs.writeFileSync(NETWORK_LOG_FILE, '', { encoding: 'utf8' });
}

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

      // Log to file only if DEBUGMODE is 'true'
      if (DEBUGMODE === 'true') {
        const logEntry = `URL: ${url}\nStatus: ${status}\nResponse Snippet: ${text.substring(0,200)}\n--------------------------------\n`;
        fs.appendFileSync(NETWORK_LOG_FILE, logEntry, { encoding: 'utf8' });
      }

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
