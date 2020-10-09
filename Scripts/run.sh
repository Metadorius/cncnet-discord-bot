#!/usr/bin/env bash

cd ..

source env/bin/activate

echo Installing packages...
python3 -m pip install -r requirements.txt

echo Running the bot...
python3 discord_cncnet_bot.py > bot.log &