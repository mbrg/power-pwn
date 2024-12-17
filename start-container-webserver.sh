#!/bin/bash

python3 -m http.server -d /home/powerpwn/power-pwn/src/powerpwn/copilot_studio/final_results 8765

echo "You'll be able to download files at the end of a copilot hunter scan at the following url"
echo "http://localhost:8765"