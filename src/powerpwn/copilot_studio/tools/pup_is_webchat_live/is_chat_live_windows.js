const puppeteer = require('puppeteer'); // v22.0.0 or later

const fs = require('fs').promises;
const path = require('path'); // Import the path module
const chalk = require('chalk'); // for colors in terminal texts
// todo: install chalk > 4

function delay(time) {
    return new Promise(function (resolve) {
        setTimeout(resolve, time)
    });
}

(async () => {
    const targetPageUrl = process.argv[2];
    if (!targetPageUrl) {
        console.error("Please provide the target page URL as an argument.");
        process.exit(1);
    }

    const orange = chalk.hex('#FFA500'); // Define a custom orange color
    const browser = await puppeteer.launch({ headless: true, args: ['--start-fullscreen', '--incognito']});
    const [page] = await browser.pages();
	
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

        await delay(5000); // Wait for 5 second to avoid sync issues
		await page.click('#root > div > div > div > div > div.content-102 > div.leftPane-103 > div > div.conversationStarters-120 > div:nth-child(1)');
        await page.waitForSelector('div.webchat__bubble__content > div', { timeout: timeout });
        const chatTexts = await page.evaluate(() => {
            const elements = document.querySelectorAll('div.webchat__bubble__content > div')
            return Array.from(elements).map(element => element.innerText);
        });

        const stringsToCheck = ["I’ll need you to sign in", "Error code:"];

        const allStringsAbsent = stringsToCheck.every(str => chatTexts.every(text => !text.includes(str)));

        if (allStringsAbsent) {
            process.stdout.write(chalk.red(`Found open chatbot at: ${targetPageUrl}\n`));
            const outputPath = path.resolve(__dirname, '../../final_results/chat_exists_output.txt');
            await fs.appendFile(outputPath, targetPageUrl + '\n');
        } else {
            process.stdout.write(chalk.green("Found inaccessible chatbot.\n"));
        }
    } catch (e) {
        if (e.name === 'TimeoutError') {
            process.stdout.write(chalk.yellow(`Timeout occurred for URL: ${targetPageUrl}, rerun or test manually\n`));
        } else {
            process.stdout.write(orange("Error occurred while trying to find chat texts:", e));
        }
    }

    await browser.close();
})().catch(err => {
    console.error(err);
    process.exit(1);
});
