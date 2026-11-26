@echo off
"C:\Program Files\PostgreSQL\19\bin\pg_ctl.exe" -D "C:\Users\Mehmethan\pgdata" -l "C:\Users\Mehmethan\pgdata\log.txt" start
python app.py
pause