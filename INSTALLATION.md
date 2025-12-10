# Power-Pwn Installation Guide

## Quick Start

### Standard Installation (Python Only)

```bash
python init_repo.py
source .venv/bin/activate
powerpwn --help
```

This installs Python dependencies only. Some modules require additional tools.

### Full Installation (Python + External Tools)

```bash
python init_repo.py --install-external-tools
source .venv/bin/activate
powerpwn --help
```

This installs Python dependencies **and** external tools (ffuf, subfinder, Node.js).

## Installation Options

### Option 1: Full Automated Installation (Recommended)

Install everything at once:

```bash
python init_repo.py --install-external-tools
```

**What gets installed:**

- ✅ Python virtual environment
- ✅ Python packages (from requirements.txt)
- ✅ ffuf (for agent-builder-hunter scan)
- ✅ subfinder (for copilot-studio-hunter enum)
- ✅ Node.js & npm (for Puppeteer-based tools)
- ✅ Node.js packages (puppeteer, xlsx, etc.)

**Supported platforms:**

- ✅ macOS (via Homebrew)
- ✅ Linux (Debian/Ubuntu via apt, others via direct download)
- ⚠️ Windows (manual installation required)

### Option 2: Python Only + Manual Tool Installation

Install Python dependencies only:

```bash
python init_repo.py
```

Then install external tools manually per module (see below).

### Option 3: Module-Specific Installation

Install dependencies for specific modules only:

```bash
# Custom GPT Hunter
./src/powerpwn/custom_gpt_hunter/install_dependencies.sh

# Agent Builder Hunter
./src/powerpwn/agent_builder/install_dependencies.sh

# Copilot Studio Hunter
./src/powerpwn/copilot_studio/install_dependencies.sh
```

## External Tools by Module

Different modules require different external tools:

| Module                                | Tools Required                | Install Script                                             |
| ------------------------------------- | ----------------------------- | ---------------------------------------------------------- |
| **agent-builder-hunter scan**         | ffuf                          | `./src/powerpwn/agent_builder/install_dependencies.sh`     |
| **agent-builder-hunter tools-recon**  | Node.js, npm, puppeteer       | Same as above                                              |
| **copilot-studio-hunter enum**        | subfinder                     | No separate script (uses system subfinder)                 |
| **copilot-studio-hunter deep-scan**   | ffuf, Node.js, puppeteer      | `./src/powerpwn/copilot_studio/install_dependencies.sh`    |
| **copilot-studio-hunter tools-recon** | Node.js, npm, puppeteer       | Same as above                                              |
| **custom-gpt-hunter**                 | Node.js, npm, puppeteer       | `./src/powerpwn/custom_gpt_hunter/install_dependencies.sh` |
| **llm-hound**                         | Python only (shodan, aiohttp) | No additional tools                                        |

## Platform-Specific Installation

### macOS

Requires [Homebrew](https://brew.sh/):

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Full installation
python init_repo.py --install-external-tools
```

Tools are installed via Homebrew:

- `brew install node` (Node.js)
- `brew install ffuf` (ffuf)
- `brew install subfinder` (subfinder)

### Linux (Debian/Ubuntu)

```bash
# Full installation
python init_repo.py --install-external-tools
```

Tools are installed via:

- `apt-get install nodejs npm` (Node.js)
- Direct download from GitHub releases (ffuf)
- Go install for subfinder (requires Go)

### Linux (Other Distributions)

Use manual installation for non-Debian systems:

```bash
# Python only
python init_repo.py

# Install tools manually
# Node.js: https://nodejs.org/
# ffuf: https://github.com/ffuf/ffuf/releases
# subfinder: https://github.com/projectdiscovery/subfinder (requires Go)
```

### Windows

Automated installation is limited on Windows. Install tools manually:

```bash
# Python setup
python init_repo.py
```

**Manual installations required:**

1. **Node.js**: Download from https://nodejs.org/
2. **ffuf**: Download from https://github.com/ffuf/ffuf/releases
3. **subfinder**: Install Go, then run: `go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest`

Then run module-specific install scripts:

```bash
.\src\powerpwn\custom_gpt_hunter\install_dependencies.sh
.\src\powerpwn\agent_builder\install_dependencies.sh
.\src\powerpwn\copilot_studio\install_dependencies.sh
```

## Error Messages

If you try to use a module without required tools, you'll see helpful error messages:

### Missing ffuf

```
❌ ffuf is not installed!

Please install ffuf:
  macOS: brew install ffuf
  Linux: See https://github.com/ffuf/ffuf#installation
  Or run: python init_repo.py --install-external-tools
```

### Missing subfinder

```
❌ subfinder is not installed!

Please install subfinder:
  macOS: brew install subfinder
  Linux: go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
  Or run: python init_repo.py --install-external-tools
```

### Missing Node.js

```
❌ Node.js is not installed!

Please install Node.js first:
  macOS: brew install node
  Linux: sudo apt-get install nodejs npm
  Or download from: https://nodejs.org/
```

## Verification

After installation, verify tools are installed:

```bash
# Check Python environment
source .venv/bin/activate
powerpwn --help

# Check external tools
node --version
npm --version
ffuf -V
subfinder -version

# Check Node.js packages (if applicable)
ls src/powerpwn/custom_gpt_hunter/node_modules/
ls src/powerpwn/agent_builder/node_modules/
```

## Troubleshooting

### init_repo.py fails with permission errors

Some installations require sudo. The script will prompt when needed:

```bash
# Linux: May need sudo for system-wide tool installation
sudo python init_repo.py --install-external-tools
```

### Homebrew not found (macOS)

Install Homebrew first:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### npm install timeout

If npm install times out (slow network), try manual installation:

```bash
cd src/powerpwn/custom_gpt_hunter
npm install --timeout=600000
```

### Architecture not supported

The script automatically detects architecture (amd64/arm64). If your architecture isn't supported, install manually from:

- ffuf: https://github.com/ffuf/ffuf/releases
- subfinder: https://github.com/projectdiscovery/subfinder (requires Go)

## Minimal Installation

If you only need specific modules, you can skip external tools:

```bash
# Python only (for llm-hound, powerdump, etc.)
python init_repo.py

# Then activate and use modules that don't require external tools, e.g.:
source .venv/bin/activate
powerpwn llm-hound --help
powerpwn powerdump --help
```

## Docker Installation

For containerized environments, see `.devcontainer/setup.sh` for reference:

```bash
# Build container with all dependencies
docker build -t power-pwn .
```

## Support

For installation issues:

1. Check error messages for specific guidance
2. Verify Python version (3.11 required)
3. Check platform compatibility above
4. Refer to module-specific README files
5. Open an issue with installation logs

## Summary

**TL;DR:**

- **Easiest**: `python init_repo.py --install-external-tools` (macOS/Linux)
- **Windows**: `python init_repo.py` + manual tool installation
- **Minimal**: `python init_repo.py` + install tools as needed
- **Module-specific**: Run `install_dependencies.sh` in module directories
