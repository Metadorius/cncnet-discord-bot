cd ..

echo Setting up virtual environment...
python -m venv env

call env\Scripts\activate.bat

echo Installing packages...
python -m pip install -r requirements.txt

pause