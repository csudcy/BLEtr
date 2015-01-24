call %~dp0venv\scripts\activate
:loop
python app.py runserver -h 0.0.0.0
goto loop
