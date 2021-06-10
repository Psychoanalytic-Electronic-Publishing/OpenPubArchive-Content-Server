#!/bin/bash

source ./env/bin/activate
cd app
uvicorn main:app --port 9100