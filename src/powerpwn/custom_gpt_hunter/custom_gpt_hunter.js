const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const readlineSync = require('readline-sync');
const fs = require('fs');
const os = require('os');

puppeteer.use(StealthPlugin());

// ANSI Color Codes
const COLOR_GREEN = '\033[92m';
const COLOR_ORANGE = '\033[38;5;208m';
const COLOR_RESET = '\033[0m';

// Helper function to wait/delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

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

(async () => {
    console.log('=== ChatGPT Custom GPT Hunter ===\n');
    
    // Parse command line arguments
    const args = process.argv.slice(2);
    let searchQuery = 'a'; // default
    let seeMoreClicks = 0; // default
    
    // Check for help flag
    if (args.includes('--help') || args.includes('-h')) {
        console.log('Usage: node custom_gpt_hunter.js <search_query> [additional_pages]');
        console.log('\nArguments:');
        console.log('  search_query       The search term for GPTs (default: "a")');
        console.log('  additional_pages   Number of additional pages to fetch (default: 0)');
        console.log('                     Each page contains ~10 GPTs');
        console.log('\nExamples:');
        console.log('  node custom_gpt_hunter.js excel');
        console.log('    → Fetches first 10 GPTs for "excel"');
        console.log('  node custom_gpt_hunter.js "data analysis" 3');
        console.log('    → Fetches 40 GPTs (4 pages × 10) for "data analysis"');
        console.log('  node custom_gpt_hunter.js music 9');
        console.log('    → Fetches 100 GPTs (10 pages × 10) for "music"\n');
        process.exit(0);
    }
    
    // Parse arguments: node script.js <search_query> <additional_pages>
    if (args.length >= 1) {
        searchQuery = args[0];
    }
    if (args.length >= 2) {
        seeMoreClicks = parseInt(args[1], 10) || 0; // Still using old var name internally
    }
    
    console.log(`Search Query: "${searchQuery}"`);
    console.log(`Additional Pages: ${seeMoreClicks} (Total: ${seeMoreClicks + 1} pages)\n`);
    
    // Get credentials from user
    const email = readlineSync.question('Email: ');
    const password = readlineSync.question('Password: ', {
        hideEchoBack: true,
        mask: '*'
    });
    
    console.log('\nLaunching browser...');
    
    const browser = await launchBrowser({ 
        headless: true, 
        args: ['--start-maximized', '--incognito']
    });
    
    const page = await browser.newPage();
    const timeout = 30000;
    page.setDefaultTimeout(timeout);
    
    // Set up response interception for the search API
    const gptResults = [];
    let lastCursor = null; // Store the cursor for pagination
    let authToken = null; // Store the auth token
    let pluginsPrototypeCount = 0; // Track GPTs with plugins_prototype
    
    // Capture the Authorization header from requests
    page.on('request', (request) => {
        const url = request.url();
        if (url.includes('/backend-api/gizmos/search')) {
            const headers = request.headers();
            if (headers['authorization']) {
                authToken = headers['authorization'];
                console.log(`[DEBUG] Captured auth token: ${authToken.substring(0, 20)}...`);
            }
        }
    });
    
    page.on('response', async (response) => {
        const url = response.url();
        
        if (url.includes('/backend-api/gizmos/search')) {
            try {
                const data = await response.json();
                
                // Store the cursor for next page
                if (data.cursor) {
                    lastCursor = data.cursor;
                }
                
                console.log(`\n✓ API Response: Found ${data.items?.length || data.gizmos?.length || 0} GPTs`);
                if (data.cursor) {
                    console.log(`  Next cursor received: ${data.cursor}`);
                } else {
                    console.log(`  No cursor in response (last page)`);
                }
                
                // Try both 'items' and 'gizmos' for backward compatibility
                const items = data.items || data.gizmos;
                
                if (items && Array.isArray(items)) {
                    items.forEach((item) => {
                        // Handle both possible structures: items with nested gizmo, or direct gizmo objects
                        const gizmo = item.gizmo || item;
                        const shortUrl = gizmo.short_url;
                        const name = gizmo.display?.name || gizmo.name || 'Unknown';
                        
                        if (shortUrl) {
                            const fullUrl = `https://chatgpt.com/g/${shortUrl}`;
                            
                            // Extract tools list and deduplicate by type
                            const tools = item.tools || [];
                            const seenTypes = new Set();
                            const uniqueTools = tools.filter(tool => {
                                if (tool && tool.type && !seenTypes.has(tool.type)) {
                                    seenTypes.add(tool.type);
                                    return true;
                                }
                                return false;
                            });
                            
                            // Check if already added (avoid duplicates)
                            const alreadyExists = gptResults.some(r => r.url === fullUrl);
                            if (!alreadyExists) {
                                // Separate plugins_prototype from other tools
                                const pluginsPrototype = uniqueTools.filter(t => t.type === 'plugins_prototype');
                                const otherTools = uniqueTools.filter(t => t.type !== 'plugins_prototype');
                                
                                const resultObj = {
                                    name: name,
                                    url: fullUrl,
                                    description: gizmo.display?.description || gizmo.description || '',
                                    tools: uniqueTools.map(t => t.type)
                                };
                                
                                // Add full plugin data if plugins_prototype exists
                                if (pluginsPrototype.length > 0) {
                                    resultObj.plugins_prototype_data = pluginsPrototype;
                                    pluginsPrototypeCount++;
                                }
                                
                                gptResults.push(resultObj);
                                
                                // Display with color coding
                                if (uniqueTools.length > 0) {
                                    const toolsDisplay = uniqueTools.map(t => {
                                        if (t.type === 'plugins_prototype') {
                                            return `${COLOR_GREEN}${t.type}${COLOR_RESET}`;
                                        } else {
                                            return `${COLOR_ORANGE}${t.type}${COLOR_RESET}`;
                                        }
                                    }).join(', ');
                                    
                                    const checkMark = pluginsPrototype.length > 0 ? `${COLOR_GREEN}✓${COLOR_RESET}` : '';
                                    console.log(`  + ${name} ${checkMark} [${toolsDisplay}]`);
                                } else {
                                    console.log(`  + ${name}`);
                                }
                            }
                        }
                    });
                } else {
                    console.log('[WARNING] No gizmos/items array found in response');
                }
            } catch (error) {
                console.error(`✗ Error parsing API response: ${error.message}`);
            }
        }
    });
    
    console.log('Navigating to ChatGPT...');
    await page.goto('https://chatgpt.com/');
    
    // Wait a bit for the page to load
    await delay(2000);
    
    try {
        // Close the modal if it appears
        console.log('Checking for modal...');
        const closeButton = await page.$('[data-testid="close-button"]');
        if (closeButton) {
            await closeButton.click();
            console.log('Modal closed');
        }
    } catch (error) {
        console.log('No modal to close');
    }
    
    // Click login button
    console.log('Clicking login button...');
    await page.waitForSelector('[data-testid="login-button"]', { visible: true });
    
    // Click and wait for either navigation or email field to appear
    await Promise.all([
        page.click('[data-testid="login-button"]'),
        Promise.race([
            page.waitForNavigation({ waitUntil: 'domcontentloaded' }).catch(() => {}),
            page.waitForSelector('#email', { visible: true, timeout: 10000 })
        ])
    ]);
    
    console.log('On login page');
    
    // Enter email
    console.log('Entering email...');
    await page.waitForSelector('#email', { visible: true });
    await page.click('#email'); // Click first to ensure focus
    await delay(500);
    await page.type('#email', email, { delay: 100 }); // Add typing delay for more human-like behavior
    await delay(1000);
    await page.keyboard.press('Enter');
    
    // Wait for password page
    console.log('Waiting for password page...');
    await Promise.race([
        page.waitForNavigation({ waitUntil: 'domcontentloaded' }).catch(() => {}),
        page.waitForSelector('input[type="password"]', { visible: true, timeout: 15000 })
    ]);
    console.log('On password page');
    
    // Enter password
    console.log('Entering password...');
    await page.waitForSelector('input[type="password"]', { visible: true });
    await page.click('input[type="password"]'); // Click first to ensure focus
    await delay(500);
    await page.type('input[type="password"]', password, { delay: 100 });
    await delay(1000);
    await page.keyboard.press('Enter');
    
    // Wait for login to complete or email verification to appear
    console.log('Waiting for login to complete...');
    await delay(3000);
    
    // Check if email verification is required
    const currentUrl = page.url();
    if (currentUrl.includes('email-verification')) {
        console.log('\n=== Email Verification Required ===');
        console.log('Please check your email for the verification code.');
        
        const verificationCode = readlineSync.question('Enter verification code: ');
        
        // Find and fill the verification code input
        // Looking for input field in the email verification form
        await page.waitForSelector('input[type="text"]', { visible: true, timeout: 10000 });
        const inputs = await page.$$('input[type="text"]');
        
        if (inputs.length > 0) {
            await inputs[0].click();
            await delay(500);
            await inputs[0].type(verificationCode, { delay: 100 });
            await delay(1000);
            
            // Look for submit button and click it
            const submitButton = await page.$('button[type="submit"]');
            if (submitButton) {
                await submitButton.click();
                console.log('Verification code submitted');
            }
        }
        
        // Wait for verification to complete
        await delay(3000);
    }
    
    // Wait for explore button to appear (indicating successful login)
    await page.waitForSelector('[data-testid="explore-gpts-button"]', { visible: true, timeout: 20000 });
    console.log('Login successful!');
    
    // Wait a bit for the page to settle
    await delay(2000);
    
    // Click on Explore GPTs
    console.log('Navigating to Explore GPTs...');
    await page.waitForSelector('[data-testid="explore-gpts-button"]', { visible: true });
    await page.click('[data-testid="explore-gpts-button"]');
    
    // Wait for explore page to load
    await delay(2000);
    
    // Search for GPTs
    console.log(`Searching for GPTs with query: "${searchQuery}"...`);
    await page.waitForSelector('#search', { visible: true });
    await page.click('#search');
    await delay(500);
    
    // Set up a promise to wait for the API response
    const apiResponsePromise = page.waitForResponse(
        response => response.url().includes('/backend-api/gizmos/search'),
        { timeout: 15000 }
    );
    
    await page.type('#search', searchQuery, { delay: 100 });
    await delay(1000);
    
    console.log('Waiting for initial search API call...');
    
    try {
        // Wait for the API response
        await apiResponsePromise;
        console.log('Initial API response received!');
        
        // Give time for the response handler to process and capture cursor
        await delay(3000);
    } catch (error) {
        console.log('No API response detected, results may not be available');
        console.log('Waiting additional time...');
        await delay(3000);
    }
    
    // Debug: Check if we have a cursor and auth token
    console.log(`\n[DEBUG] Last cursor captured: ${lastCursor ? lastCursor : 'NONE'}`);
    console.log(`[DEBUG] Auth token captured: ${authToken ? authToken.substring(0, 30) + '...' : 'NONE'}`);
    
    // Fetch additional pages using cursor-based pagination
    if (seeMoreClicks > 0) {
        if (!authToken) {
            console.log(`\n⚠ Warning: No auth token captured. API calls may fail.`);
            console.log(`Trying anyway with cookies only...\n`);
        }
        
        console.log(`\nFetching ${seeMoreClicks} additional page(s) using cursor pagination...`);
        
        for (let i = 0; i < seeMoreClicks; i++) {
            if (!lastCursor) {
                console.log(`\n✗ No cursor available, cannot fetch more pages`);
                break;
            }
            
            console.log(`\n📄 Fetching page ${i + 2}...`);
            console.log(`   Cursor (raw): ${lastCursor}`);
            console.log(`   Cursor (encoded): ${encodeURIComponent(lastCursor)}`);
            
            try {
                // Build the API URL with cursor
                const apiUrl = `https://chatgpt.com/backend-api/gizmos/search?q=${encodeURIComponent(searchQuery)}&cursor=${encodeURIComponent(lastCursor)}`;
                console.log(`   Full URL: ${apiUrl}`);
                
                // Make the API call using page.evaluate to use the browser's session
                const response = await page.evaluate(async (url, token) => {
                    const headers = {
                        'Accept': '*/*',
                        'Content-Type': 'application/json',
                        'oai-language': 'en-US'
                    };
                    
                    // Add authorization header if we have a token
                    if (token) {
                        headers['Authorization'] = token;
                    }
                    
                    const res = await fetch(url, {
                        method: 'GET',
                        headers: headers,
                        credentials: 'include' // Include cookies for authentication
                    });
                    
                    const responseText = await res.text();
                    
                    if (!res.ok) {
                        return {
                            error: true,
                            status: res.status,
                            statusText: res.statusText,
                            body: responseText
                        };
                    }
                    
                    try {
                        return JSON.parse(responseText);
                    } catch (e) {
                        return {
                            error: true,
                            message: 'Failed to parse JSON',
                            body: responseText
                        };
                    }
                }, apiUrl, authToken);
                
                // Check for errors
                if (response.error) {
                    console.error(`\n✗ API Error: ${response.status} ${response.statusText}`);
                    console.error(`   Body: ${response.body?.substring(0, 200)}`);
                    break;
                }
                
                // Debug: Log what we got back
                console.log(`\n   Response keys: ${Object.keys(response).join(', ')}`);
                console.log(`   Has items: ${!!response.items}, Length: ${response.items?.length || 0}`);
                console.log(`   Has cursor: ${!!response.cursor}, Value: ${response.cursor || 'null'}`);
                
                // Update cursor for next iteration
                if (response.cursor) {
                    lastCursor = response.cursor;
                } else {
                    lastCursor = null;
                }
                
                // Process results (response handler will catch this too, but let's also process here)
                const items = response.items || response.gizmos || [];
                console.log(`\n✓ Received ${items.length} GPTs`);
                if (response.cursor) {
                    console.log(`  Next cursor received: ${response.cursor}`);
                } else {
                    console.log(`  No more pages available`);
                }
                
                // Add results
                items.forEach((item) => {
                    const gizmo = item.gizmo || item;
                    const shortUrl = gizmo.short_url;
                    const name = gizmo.display?.name || gizmo.name || 'Unknown';
                    
                    if (shortUrl) {
                        const fullUrl = `https://chatgpt.com/g/${shortUrl}`;
                        
                        // Extract tools list and deduplicate by type
                        const tools = item.tools || [];
                        const seenTypes = new Set();
                        const uniqueTools = tools.filter(tool => {
                            if (tool && tool.type && !seenTypes.has(tool.type)) {
                                seenTypes.add(tool.type);
                                return true;
                            }
                            return false;
                        });
                        
                        const alreadyExists = gptResults.some(r => r.url === fullUrl);
                        if (!alreadyExists) {
                            // Separate plugins_prototype from other tools
                            const pluginsPrototype = uniqueTools.filter(t => t.type === 'plugins_prototype');
                            const otherTools = uniqueTools.filter(t => t.type !== 'plugins_prototype');
                            
                            const resultObj = {
                                name: name,
                                url: fullUrl,
                                description: gizmo.display?.description || gizmo.description || '',
                                tools: uniqueTools.map(t => t.type)
                            };
                            
                            // Add full plugin data if plugins_prototype exists
                            if (pluginsPrototype.length > 0) {
                                resultObj.plugins_prototype_data = pluginsPrototype;
                                pluginsPrototypeCount++;
                            }
                            
                            gptResults.push(resultObj);
                            
                            // Display with color coding
                            if (uniqueTools.length > 0) {
                                const toolsDisplay = uniqueTools.map(t => {
                                    if (t.type === 'plugins_prototype') {
                                        return `${COLOR_GREEN}${t.type}${COLOR_RESET}`;
                                    } else {
                                        return `${COLOR_ORANGE}${t.type}${COLOR_RESET}`;
                                    }
                                }).join(', ');
                                
                                const checkMark = pluginsPrototype.length > 0 ? `${COLOR_GREEN}✓${COLOR_RESET}` : '';
                                console.log(`  + ${name} ${checkMark} [${toolsDisplay}]`);
                            } else {
                                console.log(`  + ${name}`);
                            }
                        }
                    }
                });
                
                // Small delay between requests
                await delay(1000);
                
                // Stop if no more cursor
                if (!lastCursor) {
                    console.log('\n✓ No more pages available');
                    break;
                }
                
            } catch (error) {
                console.error(`✗ Error fetching page ${i + 2}: ${error.message}`);
                break;
            }
        }
        
        console.log('\n✓ Pagination complete!');
    }
    
    console.log('\n=== Search Complete ===');
    console.log(`Total GPTs found: ${gptResults.length}`);
    console.log(`${COLOR_GREEN}GPTs with plugins_prototype: ${pluginsPrototypeCount}${COLOR_RESET}`);
    
    // Save results to file
    const fs = require('fs');
    const sanitizedQuery = searchQuery.replace(/[^a-z0-9]/gi, '_').toLowerCase();
    
    // Add timestamp to filename
    const now = new Date();
    const timestamp = now.toISOString().replace(/:/g, '-').replace(/\..+/, '').replace('T', '_');
    const outputFilename = `custom_gpt_results_${sanitizedQuery}_${timestamp}.json`;
    
    console.log(`\nSaving results to ${outputFilename}...`);
    
    try {
        fs.writeFileSync(
            outputFilename, 
            JSON.stringify(gptResults, null, 2)
        );
        console.log(`✓ Successfully saved ${gptResults.length} results to ${outputFilename}`);
        
        // Also print summary
        if (gptResults.length > 0) {
            console.log('\n=== Results Summary ===');
            gptResults.forEach((result, index) => {
                console.log(`${index + 1}. ${result.name}`);
                console.log(`   ${result.url}`);
                if (result.tools && result.tools.length > 0) {
                    // Color code tools: plugins_prototype in green, others in orange
                    const toolsDisplay = result.tools.map(t => {
                        if (t === 'plugins_prototype') {
                            return `${COLOR_GREEN}${t}${COLOR_RESET}`;
                        } else {
                            return `${COLOR_ORANGE}${t}${COLOR_RESET}`;
                        }
                    }).join(', ');
                    const checkMark = result.plugins_prototype_data ? `${COLOR_GREEN}✓${COLOR_RESET}` : '';
                    console.log(`   ${checkMark} Tools: ${toolsDisplay}`);
                }
            });
        }
    } catch (writeError) {
        console.error(`✗ Error saving file: ${writeError.message}`);
        console.log('\nResults in memory:');
        console.log(JSON.stringify(gptResults, null, 2));
    }
    
    // console.log('\n\nKeeping browser open for inspection. Press Ctrl+C to exit.');
    
    // Keep browser open for inspection
    // Uncomment the line below to auto-close after completion
    await browser.close();

})().catch(err => {
    console.error('\n=== Error ===');
    console.error(err);
    process.exit(1);
});

