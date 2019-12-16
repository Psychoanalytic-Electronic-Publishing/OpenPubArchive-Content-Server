#!/bin/bash

# under linux, webfaction
# to install
# python3.7 -m venv ./env
# source ./env/bin/activate
# pip3.7 install --trusted-host pypi.python.org -r requirements.txt
# if it complains pip is not up to date
# pip3.7 install --upgrade pip

# cd app
source ./env/bin/activate
uvicorn main:app --port 28280