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

```bash
pip install virutalenv
python -m pip virtualenv env
source ./env/bin/activate
pip install -r requirements.txt
```