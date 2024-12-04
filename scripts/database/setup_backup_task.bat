@echo off
echo Setting up daily database backup task...

REM Get the project root directory
set PROJECT_ROOT=%~dp0..\..

REM Create a wrapper batch script for the backup
echo @echo off > "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo cd /d "%PROJECT_ROOT%" >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo call venv312\Scripts\activate.bat >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo python scripts\database\scheduled_backup.py >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo if errorlevel 1 ( >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo   echo Backup failed. Check logs for details. >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo   pause >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"
echo ) >> "%PROJECT_ROOT%\scripts\database\run_backup.bat"

REM Create the scheduled task using the wrapper script
schtasks /create /tn "AIWA_DatabaseBackup" /tr "\"%PROJECT_ROOT%\scripts\database\run_backup.bat\"" /sc daily /st 02:00 /ru "%USERNAME%" /f

if %ERRORLEVEL% equ 0 (
    echo Task created successfully!
    echo Database will be backed up daily at 2:00 AM
    echo You can find the backup logs in logs/app.log
) else (
    echo Failed to create task. Please run as administrator.
)

pause
