@echo off
set TESTING=true
set JWT_SECRET_KEY=4uo3TBPh48tUm-9TxmqtRYuSVYqxaGHj3RQxj8sRLvU
set JWT_ALGORITHM=HS256
set ACCESS_TOKEN_EXPIRE_MINUTES=30
set APP_NAME=AIWA
set APP_VERSION=1.0.0
set DEBUG=True
set ENVIRONMENT=testing
set API_V1_PREFIX=/api/v1

echo Running tests...
venv312\Scripts\python.exe -m pytest tests/ -v --cov=src --cov-report=term-missing
