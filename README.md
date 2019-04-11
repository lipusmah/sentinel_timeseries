# Sentinel-2 time series
Masters degree project at UL FGG. Extraction of NDVI index and statistics over time for specific polygons.

## Environment setup

### Anaconda

Install Anaconda and create a virtual environment with all necessary libraries from YML file.

```bash
conda env create -f environment.yml
```

This will create a new conda enviroment PythonEx. Activate it using

```bash
conda activate PythonEx
```

### virutalenv
REQUIREMENTS:
Python 3.6.* installed on system and added to PATH.
Installed virtualenv on mentioned Python interpreter:
```bash
pip install virtualenv
```

Needs preinstalled C/C++ compiler.
```bash
WINDOWS:
./create_win_env.bat
./env/Scripts/activate
pip install -r requirements

OTHER:
pip install virutalenv
python -m pip virtualenv env
source ./env/bin/activate
pip install -r requirements.txt
```

### HOW TO RUN
To run for one polygon from sqlite database see function run_for_one
inside main.py file. Change layer variable (line 96) to match one of the
layers defined inside your sentinel-hub configuration utility.

Function supports different SRS via EPSG code. Default SRS is set to EPSG:3912.
Example of running this function:
```bash
if __name__ == "__main__":
    conn = sqliteConnector(r"./dbs/raba_2018.sqlite")
    ogc_id = 122
    table_name = "raba_2018"
    run_for_one(conn, table_name, ogc_id, "epsg:3912")
```

Other requirements:
* Account on sentinel-hub
* Created configuration and layer in configuration utility on sentinel-hub
* File "api.id" inside ./assets/ folder with ID of configuration.
(Can be pasted also in api_key variable - line 27 of sentinel-hub.py file)
