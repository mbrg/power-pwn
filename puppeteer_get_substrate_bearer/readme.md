# Get the substrate token (CoPilot API)

## Background
1. Context and origin [here](https://docs.google.com/document/d/15xamKGTO2pC2HI9kjL8A9uQzOFK_Bd7FlXwfrCev0Bw/edit#) (BH24 CoPilot effort) and [here](https://github.com/zenitysec/research/tree/develop/scripts/other/puppeteer_get_substrate_bearer).
2. The main goal of this script is to be a POC for programatically getting the substrate token, which is used to interact with CoPilot via WS messages.
3. This is a Node.JS Puppeteer script.

## Prerequisites and basic functionality
1. [Install Node.JS & NPM](https://nodejs.org/en/download/package-manager) to be able to run the JS script.
2. Install dependencies by running the following from within the project directory (e.g., the Puppeteer module).
   
    ```npm install```

3. Script execution: 
   - Run one of the following commands:

      - ```node get_substrate_bearer_teams.js user=<your_user> password=<your_password>``` 
   
        (uses _teams[.]microsoft[.]com_ to get the token)
     
      - ```node get_substrate_bearer_office.js user=<your_user> password=<your_password>```

        (uses _www[.]office[.]com_ to get the token)

   - If you see errors regarding missing resources in the node_modules directory when you first run the script, please run the following to clear NPM cache and reinstall dependencies:
     ```bash
     npm cache clean --force 
     rm -rf node_modules 
     npm install
     ```

   - You should get a print to the terminal of the substrate token (save it securely and delete the terminal output afterwards).

## FAQ
-   **Why do we want the substrate token?** 

      We can use this token to interact with the CoPilot API directly and via CLI, scripts, etc.

-   **Why is Puppeteer and Node.JS used for this?**
   
      Puppeteer is a headless browser, which means that it can act as a browser, but still to be controlled programmatically via code. JS & headless browsers are good tools to simulate human session behavior online quickly and/or on a small scale. Since MSFT don't seem to try to block this kind of automated behavior ATM (at least on the target we used for the POC), this was currently feasible without too many additional complications besides the basic browser impersonation headless browsers provide.

-   **Why didn't we just use Python?**
   
      We wanted a POC for getting the substrate token, and JS + Puppeteer provided that more quickly because Teams & CoPilot have pretty busy mechanics which aren't straightforward with Python (headless browsers and JS handle sessions, state, JS rendering, async requests, redirections, etc. more out-of-the-box). In other words, we used a headless browser to perform the user journey required to get the substrate token.

-   **Why didn't we use the [family-of-client-ids-research](https://github.com/secureworks/family-of-client-ids-research) to get the token?**

     Apparently, the substrate token is not in included in the family of tokens tokens documented by the FOCIS.

-   **How can I verify that I actually got the correct token after running the script?**    
     Check the token via [jwt.io](jwt.io) and you should see that it has specific details related to the CoPilot token (TBD more info on this). BTW you're basically sending your CoPilot private token when you use this site, so keep that in mind :)

-  **How stable is this script?**
  
     Testing so far was predominantly successful, however, please note the following:
     1. This is basically a headless browser botting solution, which depends on the webpage/JS and other elements to remain as they were to keep working. These are things that could possibly be improved to gain stability in the long run but currently this is a basic POC. For example, the user journey was tailor-made based on the current test user's login to the old Teams and expected redirections to the new Teams and then to CoPilot itself to get the correct token.
     2. Breaking changes between running environments shouldn't occur, but they could in some cases, in which the script will have to be tailor-made for your specific case (e.g., if the user journey in Teams is different than what the script was built upon, for some reason).
     3. This project was created and documented with the goal of allowing to easily run it on other environments. That being said, such differences could cause issues ATM.
 
        
-  **What do I do if I encounter errors?**
     1. Check dependencies, installation and errors and try to answer this: did the target change or did your environment change? 
     2. Since it's a headless browser, you'll want to run it in headless mode unless you're debugging, in which case it'll be clearer to run in headful mode (line 17).
     3. Check the comment line 19 for some common fixes (e.g., dedicated browser profile).
