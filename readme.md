<div align="center">
	<p>
		<sup>Maintained by:</sup>
		<br>
		<br>
		<a href="https://www.zenity.io">
			<img src="zenity_logo.png"/>
		</a>
        <p>
        Secure AI Agents Everywhere.
        </p>
	</p>
	<hr>
</div>

# Overview

![powerpwn](wiki/powerpwn_asci_black.png)
[![Black Hat](https://img.shields.io/badge/Black%20Hat-USA%202024-blue)](https://www.toolswatch.org)
[![SecTor 23](https://img.shields.io/badge/SecTor-23-red)](https://www.blackhat.com/sector/2023/arsenal/schedule/index.html#entraid-guest-to-corp-data-dump-with-powerpwn-36105)
[![Black Hat](https://img.shields.io/badge/Black%20Hat-USA%202023-blue)](https://www.toolswatch.org)
[![DEFCON30](https://img.shields.io/badge/DEFCON-30-8A2BE2)](https://forum.defcon.org/node/241932)

[![stars](https://img.shields.io/github/stars/mbrg/power-pwn?icon=github&style=social)](https://github.com/mbrg/power-pwn)
[![twitter](https://img.shields.io/twitter/follow/mbrg0?icon=twitter&style=social&label=Follow)](https://twitter.com/intent/follow?screen_name=mbrg0)
[![email me](https://img.shields.io/badge/michael.bargury-owasp.org-red?logo=Gmail)](mailto:michael.bargury@owasp.org)

Power Pwn is an offensive and defensive security toolset for Microsoft 365 Power Platform and AI services.

**Key Features, among others:**

- 💾 **PowerDump**: Comprehensive tenant scanning and data collection
- 🚪 **BackDoor**: Deploy backdoor flows for persistent access to Power Platform environments
- 🦠 **NoCodeMalware**: Create and deploy malicious Power Platform artifacts without writing code
- 🎣 **PowerPhishing**: Abuse Power Platform for phishing campaigns and credential harvesting
- 🤖 **Copilot Studio Hunter**: Discover and test misconfigured Copilot Studio bots exposed to unauthenticated users
- 🤖 **Custom GPT Hunter**: Enumerate and analyze custom GPTs
- 🤖 **Agent Builder Hunter**: Discover publicly available Agent Builder deployments and enumerate their capabilities
- 🔎 **LLM Hound**: Discover publicly exposed MCPs & AI middleware across the internet using Shodan
- 🎯 **Copilot M365**: Test Microsoft 365 Copilot for unauthorized data retrieval
- 📄 **Power Pages**: Identify misconfigured Power Pages that leak Dataverse tables

Please review the tools documentation for the full list of features:

<img src="ppwn_help_menu.png"/>
		<br>
		<br>

Check out our [Wiki](https://github.com/mbrg/power-pwn/wiki) for comprehensive documentation, guides, and related talks!

A review of Power Pwn's PowerDump module is available here:

[![BlackHat Arsenal USA 2023 - Power Pwn](https://img.youtube.com/vi/LpdckZyBwvs/0.jpg)](https://www.youtube.com/watch?v=LpdckZyBwvs)

# Installation

For standard usage, install with:

```bash
pip install powerpwn
```

**For developers and advanced usage**, see our comprehensive [Installation Guide](INSTALLATION.md) which covers:

- Full automated installation (Python + external tools)
- Module-specific dependencies (ffuf, subfinder, Node.js, Puppeteer)
- Platform-specific instructions (macOS, Linux, Windows)
- Troubleshooting and verification steps

Some modules require additional tools. Please review the following [Wiki](https://github.com/mbrg/power-pwn/wiki) pages for module-specific requirements:

- [Powerdump](https://github.com/mbrg/power-pwn/wiki/Modules:-PowerDump)
- [Copilot Studio Hunter - deep-scan](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Deep-Scan)
- [Copilot Studio Hunter - tools-recon](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-tools-recon)
- [Copilot Studio Hunter - enum](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Enum)
- [CopilotM365](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Connector-and-Automator)

## Quick Guide for Developers

### Option 1: Full Installation (Recommended)

Install Python packages and external tools (ffuf, subfinder, Node.js):

```bash
python init_repo.py --install-external-tools
source .venv/bin/activate  # Linux/macOS
# or
.\.venv\Scripts\activate  # Windows
```

Supported on macOS and Linux. Windows requires manual tool installation.

### Option 2: Python Only

Install Python packages only (manual tool installation needed later):

```bash
python init_repo.py
source .venv/bin/activate  # Linux/macOS
```

### Verify Installation

```bash
pip install .
powerpwn --help
```

**For detailed installation options, troubleshooting, and platform-specific guides, see [INSTALLATION.md](INSTALLATION.md)**

### Development Tips

1. **Editable Mode**: If local changes aren't reflected when testing, reinstall in editable mode:

   ```bash
   pip install -e .
   ```

2. **Python Version**: Use Python 3.11 for GUI modules (PowerDump) to avoid compatibility issues.

3. **PYTHONPATH Setup** (if needed):

   - Linux/macOS: `export PYTHONPATH=/[your_powerpwn_directory]/src:$PYTHONPATH`
   - Windows PowerShell: `$env:PYTHONPATH = "C:\[your_powerpwn_directory]\src;" + $env:PYTHONPATH`

4. **Code Formatting**: Before submitting PRs, run:
   ```bash
   black -C -l 150 {file_path}
   ```

# Usage

## Quick Start

### 🎯 Common Use Cases

#### 1. Tenant Security Assessment

Start with [PowerDump](https://github.com/mbrg/power-pwn/wiki/Modules:-PowerDump) to scan your Microsoft 365 tenant for security issues and collect comprehensive data.

#### 2. Test M365 Copilot Security

Evaluate your M365 Copilot deployment for unauthorized data retrieval:

- [Copilot M365 - whoami](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-M365-%E2%80%90-Whoami): Identify user context and permissions
- [Copilot M365 - dump](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-M365-%E2%80%90-Dump): Test data exfiltration scenarios

#### 3. Hunt for Exposed Copilot Studio Bots

Test for misconfigured Copilot Studio bots accessible to unauthenticated users:

- [Copilot Studio Hunter - deep-scan](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Deep-Scan): Deep security analysis
- [Copilot Studio Hunter - tools-recon](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Tools-Recon): Discover bot capabilities
- [Copilot Studio Hunter - enum](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Enum): Enumerate available bots

#### 4. Test Power Pages Security

Identify misconfigured [Power Pages](https://github.com/mbrg/power-pwn/wiki/Modules:-Power-Pages) that could leak Dataverse tables.

### 📚 Full Documentation

Please review the [Wiki](https://github.com/mbrg/power-pwn/wiki) for a complete module list, detailed usage instructions, and advanced scenarios.
