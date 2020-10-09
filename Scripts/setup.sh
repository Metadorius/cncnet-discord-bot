#!/usr/bin/env bash

cd ..

echo Setting up virtual environment...
python3 -m venv env

echo Installing packages...
source env/bin/activate
python3 -m pip install -r requirements.txt
