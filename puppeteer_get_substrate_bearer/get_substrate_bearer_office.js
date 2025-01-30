// Description: This script logs into Microsoft Office and retrieves the bearer token for the Substrate API.
// If you need the results faster, you can reduce the delays' values, but do so with caution (it's a clean-and-dirty way to make things work for this POC).

const puppeteer = require('puppeteer'); // Ensure you have puppeteer installed
require('dotenv').config(); // Include the dotenv package to read the .env file
let Utils = require("./utils.js");

const ARGS = Utils.getArguments()
const PASSWORD = ARGS["password"]
const USER = ARGS["user"]

function delay(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time)
    });
}

(async () => {

    const windowWidth = 1920;
    const windowHeight = 1080;

    let browser;
    // In case you have issues, you can try to use the following flags (often issues can occur from specific Chrome instances or profiles, sometimes clean ones help)
    // https://stackoverflow.com/questions/57623828/in-puppeteer-how-to-switch-to-chrome-window-from-default-profile-to-desired-prof/57662769#57662769

    try {
        // For windows the executable path is to open the existing chrome instead of the
        // "Chrome for testing" that is included with puppeteer - solves white screen bug
        browser = await puppeteer.launch({
            headless: true, // Change to 'false' to see the browser actions for debugging
            // Use the default windows path for chrome exe - solves white window bug for windows
            executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            // Start the browser in incognito mode
            args: ['--incognito']
        });
    } catch(e) {
         browser = await puppeteer.launch({
            headless: true, // Change to 'false' to see the browser actions for debugging
            // Start the browser in fullscreen and incognito mode
            args: ['--start-fullscreen', '--incognito']
        });
    }

    // Create a new page
    const [page] = await browser.pages(); // Get the only page opened by Puppeteer

    // Set the viewport size
    await page.setViewport({
        width: windowWidth,
        height: windowHeight
    });

    const timeout = 15000; // Set the timeout to 15 seconds
    page.setDefaultTimeout(timeout);

    // Go to a the Teams URL (will be changed with the dynamics URL in the future)
    await page.goto('https://www.office.com/');
    console.log("Starting the login process");

    // Enter the test username

    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }

        console.log("Locating sign in button");

        await puppeteer.Locator.race([
            targetPage.locator('#mectrl_headerPicture')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click();
        await Promise.all(promises);
    }
    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator(':scope >>> #i0116')
        ])
            .setTimeout(timeout)
            .fill(USER);
    }

    // Click on the 'Next' button

    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('#idSIButton9'),
        ])
            .setTimeout(timeout)
            .click();
    }

    // Wait for the password field and enter the password in it

    await delay(2000); // Wait for 2 seconds to avoid sync issues

    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('#i0118'),
        ])
            .setTimeout(timeout)
            .click();
    }

    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('#i0118'),
        ])
            .setTimeout(timeout)
            .fill(PASSWORD);
    }
    await delay(2000); // Wait for 2 seconds to avoid sync issues

    console.log("Logging in");

    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('#idSIButton9'),
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click();
        await Promise.all(promises);
    }

    // Click 'Yes' button to stay signed in

    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('#idSIButton9'),
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click();
        await Promise.all(promises);
    }

    //

    console.log("Completed logging in");

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

    // Go to the Outlook URL, since the local storage with the key containing the substrate token is for this subdomain
    await page.goto('https://outlook.office.com/mail/');

    console.log("Completed user journey, grabbing substrate token from the headless browser's local storage key");

    await delay(10000); // Wait for 10 seconds to avoid sync issues

    // Retrieve the value of 'secret' from local storage if the key's value includes a reference to 'https://substrate.office.com/sydney/.default'
    // This is the bearer token for the Substrate API (also seen in the network tab WS under the access_token parameter)
    const secretValue = await page.evaluate(() => {
    // Find the key with the specific URL pattern
    const key = Object.keys(localStorage).find(k => {
        const value = localStorage.getItem(k);
        return k.includes('https://substrate.office.com/sydney/.default');
    });

    if (key) {
        const data = JSON.parse(localStorage.getItem(key)); // Parse the JSON string
        return data.secret; // Return the 'secret' (bearer token)
    }

    print("Not found")
    return null; // If not found, return null

    });


    // Print the bearer token to the console (change this to save it to a file or a secure location)
    console.log('access_token:%s', secretValue);

    await browser.close(); // Close the browser

    // Catch errors and log them to the console
})().catch(err => {
    console.error(err);
    process.exit(1);
});
