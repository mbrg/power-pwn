<div align="center">
	<p>
		<sup>Maintained by:</sup>
		<br>
		<br>
		<a href="https://www.zenity.io">
			<img src="/zenity_logo.png"/>
		</a>
        <p>git
        Empower your business, not the adversaries.
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

Power Pwn is an offensive security toolset for Microsoft 365.
Check out our [Wiki](https://github.com/mbrg/power-pwn/wiki) for docs, guides and related talks!

An review of the tool's basic modules is available here:

[![BlackHat Arsenal USA 2023 - Power Pwn](https://img.youtube.com/vi/LpdckZyBwvs/0.jpg)](https://www.youtube.com/watch?v=LpdckZyBwvs)

# Installation
1. Install with `pip install powerpwn`.
2. Please review the following modules' [Wiki](https://github.com/mbrg/power-pwn/wiki) pages for additional installation dependencies:
   - [Powerdump](https://github.com/mbrg/power-pwn/wiki/Modules:-PowerDump)
   - [Copilot Studio Hunter - deep-scan](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Deep-Scan)
   - [Copilot Studio Hunter - enum](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Enum)
   - [CopilotM365](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Connector-and-Automator)
  
## Quick Guide for Developers
1. Clone the repository and setup a virtual environment in your IDE. Install python packages by running:

```
  python init_repo.py
```
2. If not active already, run the folloeing to activate the virtual environment (.venv):
```
  .\.venv\Scripts\activate (Windows)

  source .venv/bin/activate (Linux & MacOS)
```

3. Verify all dependencies are installed:

```
  pip install .
```

**Notes**: 
1. To handle the GUI properly, please use Python 3.8 for the above virtual environment, if it is not already the default.
2. If the project directory isn't set up correctly you can use this command (or one similar to it) to set it up manually:
   - `export PYTHONPATH=/[your_powerpwn_directory]/src:$PYTHONPATH` (Linux)
   - `$env:PYTHONPATH = "C:\[your_powerpwn_directory]\src;" + $env:PYTHONPATH` (Windows PowerShell)

3. To handle the PowerDump module's GUI properly, please use Python 3.8 for the above `pip` version if it is not already the default. Alternatively, you can install the above within a Python 3.8 virtual environment.
4. When pushing PR, you can run `black -C -l 150 {file to path}` to fix any formatting issues related to _black_.

# Usage
## Quick Start
1. For quickly getting started with scanning your tenant, please check the [powerdump](https://github.com/mbrg/power-pwn/wiki/Modules:-PowerDump) module here.
2. For testing your M365 Copilot for retrieval of internal information (e.g., via a compromised user), please check the C365 modules:
  * [whoami](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-M365-%E2%80%90-Whoami)
  * [C365 dump](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-M365-%E2%80%90-Dump)
3. For testing misconfigured Copilot Studio bots available to unauthenticated users please check the Copilot Hunter _deep-scan_ module [here](https://github.com/mbrg/power-pwn/wiki/Modules:-Copilot-Studio-Hunter-%E2%80%90-Deep-Scan).
4. To test misconfigured Power Pages which could allow for Dataverse tables to be leak, please check the [powerpages](https://github.com/mbrg/power-pwn/wiki/Modules:-Power-Pages) module.

Please review the [Wiki](https://github.com/mbrg/power-pwn/wiki) for a full module list and detailed usage.
