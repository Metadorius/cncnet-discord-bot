cd ..

call env\Scripts\activate.bat

echo Installing packages...
python -m pip install -r requirements.txt

echo Running the bot. Press Ctrl+C to exit.
python discord_cncnet_bot.py > bot.log 2>&1

pause