// Description: This script logs into Microsoft Teams and retrieves the bearer token for the Substrate API.
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
    try {
        // Launch the browser in incognito mode
        browser = await puppeteer.launch({
            // Useful for debugging
            headless: true, // Change to 'false' to see the browser actions for debugging

            // In case you have issues, you can try to use the following flags (often issues can occur from specific Chrome instances or profiles, sometimes clean ones help)
            // https://stackoverflow.com/questions/57623828/in-puppeteer-how-to-switch-to-chrome-window-from-default-profile-to-desired-prof/57662769#57662769

            // Use the default windows path for chrome exe - solves white window bug for windows
            executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            // Start the browser in incognito mode
            args: ['--incognito']
        });
    } catch(e) {
         // Launch the browser in full screen and incognito mode
         browser = await puppeteer.launch({
            // Useful for debugging
            headless: true, // Change to 'false' to see the browser actions for debugging

            // In case you have issues, you can try to use the following flags (often issues can occur from specific Chrome instances or profiles, sometimes clean ones help)
            // https://stackoverflow.com/questions/57623828/in-puppeteer-how-to-switch-to-chrome-window-from-default-profile-to-desired-prof/57662769#57662769

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
    await page.goto('https://teams.microsoft.com/_');
    console.log("Starting the login process");

    // Enter the test username
    await page.waitForSelector('#i0116');
    await page.type('#i0116', USER);

    // Click on the 'Next' button
    await page.waitForSelector('#idSIButton9', { visible: true });
    await page.evaluate(() => {
        document.querySelector('#idSIButton9').click();
    });

    // Wait for the password field to be visible and enter the password in it
    await page.waitForSelector('#i0118', { visible: true });
    await page.type('#i0118', PASSWORD);

    // Click on the 'Sign in' button
    await page.waitForSelector('#idSIButton9');
    await delay(2000); // Wait for 2 seconds to avoid sync issues
    await page.click('#idSIButton9');

    console.log("Logging in");

    // Click 'Yes' button to stay signed in
    await page.waitForSelector('#idSIButton9');
    await delay(2000); // Wait for 2 seconds to avoid sync issues
    await page.click('#idSIButton9');

    console.log("Completed logging in");

    await delay(10000); // Wait for 10 seconds to avoid sync issues

    console.log("Starting user journey to CoPilot");

    {
        const targetPage = page;
        const promises = [];
        const startWaitingForEvents = () => {
            promises.push(targetPage.waitForNavigation());
        }
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria([role=\\"dialog\\"]) >>>> ::-p-aria(Switch now)'),
            targetPage.locator('#ngdialog1 button'),
            targetPage.locator('::-p-xpath(//*[@id=\\"ngdialog1\\"]/div[2]/div/div/div/div[2]/div/div/button)'),
            targetPage.locator(':scope >>> #ngdialog1 button')
        ])
            .setTimeout(timeout)
            .on('action', () => startWaitingForEvents())
            .click({
                offset: {
                    x: 98,
                    y: 11.33331298828125,
                },
            });
        await Promise.all(promises);
    }

    await delay(10000);

    {
        const targetPage = page;
        await puppeteer.Locator.race([
            targetPage.locator('::-p-aria(Copilot)'),
            targetPage.locator('#title-chat-list-item_bizChatMetaOSChatListEntryPoint'),
            targetPage.locator('::-p-xpath(//*[@id=\\"title-chat-list-item_bizChatMetaOSChatListEntryPoint\\"])'),
            targetPage.locator(':scope >>> #title-chat-list-item_bizChatMetaOSChatListEntryPoint')
        ])
            .setTimeout(timeout)
            .click({
                offset: {
                    x: 25.333328247070312,
                    y: 10.333328247070312,
                },
            });
    }

    console.log("Completed user journey, grabbing substrate token from the headless browser's local storage key");

    await delay(10000); // Wait for 10 seconds to avoid sync issues

    // Retrieve the value of 'secret' from local storage if the key's value includes a reference to 'https://substrate.office.com/sydney/.default'
    // This is the bearer token for the Substrate API (also seen in the network tab WS under the access_token parameter)
    const secretValue = await page.evaluate(() => {
        const key = Object.keys(localStorage).find(k => {
            const value = localStorage.getItem(k);
            return value.includes('https://substrate.office.com/sydney/.default');
        });

        if (key) {
            const data = JSON.parse(localStorage.getItem(key));
            return data.secret;
        }
        return null;
    });

    // Print the bearer token to the console (change this to save it to a file or a secure location)
    console.log('access_token:%s', secretValue);

    await browser.close(); // Close the browser

    // Catch errors and log them to the console
})().catch(err => {
    console.error(err);
    process.exit(1);
});
