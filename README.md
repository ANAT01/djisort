# djisort
DJI photo sort by EXIF GPS and reverse geocoding

## Disclaimer
> DO NOT USE ON REAL DATA!!!
> COPY DATA BEFORE USE THIS SCRIPT!!!

## Requirements

```
sudo apt-get --no-install-recommends install python3-pip
sudo apt-get install virtualenv
```

## Usage
#### Install python3 virtual environment
`virtualenv -p python3 venv`

`. venv/bin/activate`

#### Check python version
`python --version`
> Python 3.5.2

#### Install python requirements
pip install -r requirements.txt 

#### Run
djisort <src> <dest>
