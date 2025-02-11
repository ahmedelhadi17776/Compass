@echo off 
cd /d "c:\Users\ahmed\OneDrive\Desktop\COMPASS\scripts\database\..\.." 
call venv312\Scripts\activate.bat 
python scripts\database\scheduled_backup.py 
if errorlevel 1 ( 
  echo Backup failed. Check logs for details. 
  pause 
) 
