rem to install:
rem python 3.5 - 3.7 required
python -m venv .\env
.\venv\Scripts\activate.bat
pip install --trusted-host pypi.python.org -r /app/requirements.txt
rem if it complains pip is not up to date
python -m pip install --upgrade pip

# on, webfaction
python3 -m venv ./env
source ./env/bin/activate
pip3 install --trusted-host pypi.python.org -r requirements.txt
rem if it complains pip is not up to date
pip3 install --upgrade pip



