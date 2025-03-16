@echo off
cd /d D:\grad\Graduation_project

:: Define your Anaconda environment name
set CONDA_ENV=compass

:: Start Backend in Anaconda Prompt
start cmd /k "C:\Users\felix_new\anaconda3\Scripts\activate.bat && conda activate compass && cd Backend && set PYTHONPATH=D:\grad\Graduation_project && python -m uvicorn main:app --reload --port 8000"

:: Start Frontend in a new terminal
start cmd /k "cd Frontend && npm run electron:dev"

echo Backend and Frontend started in Anaconda environment: %CONDA_ENV%.
