@echo off
if not exist "venv\" (
	pip install virtualenv
	virtualenv venv
	cd .\venv
	call .\Scripts\activate
	cd ..\
	pip install -r requirements.txt
)

cd .\venv
call .\Scripts\activate
cd ..\
python web_check.py