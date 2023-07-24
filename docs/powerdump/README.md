# powerdump 


powerdump is a tool for exploring information in Microsoft PowerPlatform from a Red Team perspective. In short, this is what it does:
* Generates access tokens to fetch available resources in Microsoft PowerApps.
* Use HTTP calls in Python to dump all available information in the Micsrofot PowerPlatform to local directory.
* Generates access tokens to perform advanced actions on discovered resources.
* Provide a basic GUI to present collected resources and data.

powerpwn uses `browsepy` Python library and is only compatible with Python 3.6-3.8 (development is done with Python 3.8). 

### Installation
**Using a version from GitHub**

Clone the repository and run:

```
pip install .
```

### Installation for development
Clone the repository and setup a virtual environment in your IDE. Install python packages by running:

```
python init_repo.py

```
To activate the virtual environment (.venv) run:
```
.\.venv\Scripts\activate (Windows)

./.venv/bin/activate (Linux)

```

### Using powerpwn
**Explore using cli**
* Run `powerpwn dump --tenant {tenantId} --cache-path {path}` to collect data from tenantId and store it in path. The default cache-path is `.cache` .
* For more options run `powerpwn dump --help`
* On first run, a device flow will initiate to acquire an access token.
* This may take a while depends on the tenant size. Once collect is done, you can find collected resources and data under `path` directory
* Access tokens to powerapps and apihub are cached in tokens.json file.
* To run a local server for gui, run dump command with `-g` or `--gui`.

**Using Gui**
* Run `powerpwn gui --cache-path {path}`, with same cache-path of `dump` command. The default cache-path is `.cache` .
* On http://127.0.0.1:5000/ you can find an application with all collected resources
* For connections, Playground will generate the connections swagger, that allow you to run these connections and perform actions on the platform. To authenticate, use the generated apihub access token generated in the previous step.
* On http://127.0.0.1:8080/ you can find a simple file browser with all resources and data dump.
