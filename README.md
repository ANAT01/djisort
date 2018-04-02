# djisort

DJI photo sort by EXIF GPS and reverse geocoding

## Disclaimer

> DO NOT USE ON REAL DATA!!!
> COPY DATA BEFORE USE THIS SCRIPT!!!

## Requirements

```
sudo apt-get --no-install-recommends install python3-pip
sudo apt-get install virtualenv python3-setuptools
```

## Usage

### Install Python3 virtual environment

```
virtualenv -p python3 venv
. venv/bin/activate
```

### Check python version

```
python --version
```
> Python 3.5.2

### Install python requirements

```
pip install https://github.com/ANAT01/djisort/archive/master.zip
```

### Run

Usage: `djisort <src> <dst>`

For example:
```
djisort unsorted/ sorted/ 
```