# npm
sudo apt update
sudo apt install nodejs npm -y
# ffuf
wget https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_arm64.tar.gz
tar -xzf ffuf_2.1.0_linux_arm64.tar.gz ffuf
rm -rf ffuf_2.1.0_linux_arm64.tar.gz
sudo mv ffuf /usr/local/bin/ffuf
# amass
wget https://github.com/owasp-amass/amass/releases/download/v4.2.0/amass_Linux_arm64.zip
unzip -j amass_Linux_arm64.zip "amass_Linux_arm64/amass"
rm -rf amass_Linux_arm64.zip
sudo mv amass /usr/local/bin/amass
# puppeteer prereqs
sudo apt-get install -y \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libgcc1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    lsb-release \
    wget \
    xdg-utils
# puppeteer
npm i puppeteer
# puppeteer in dir
cd puppeteer_get_substrate_bearer
npm install
npx puppeteer browsers install chrome
sudo apt-get update
sudo apt-get install -y chromium
cd ..
# powerpwn
pip install .
