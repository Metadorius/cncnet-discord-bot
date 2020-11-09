#!/usr/bin/env bash

cd ..


if type python3.8 > /dev/null; then
  py="python3.8"
  echo Detected Python 3.8.
elif type python3.7 > /dev/null; then
  py="python3.7"
  echo Detected Python 3.7.
else
  echo No suitable Python interpreter detected. Please install Python 3.7 or higher.
  exit 1
fi

echo Setting up virtual environment...
$py -m venv env

echo Installing packages...
source env/bin/activate
$py -m pip install -r requirements.txt
