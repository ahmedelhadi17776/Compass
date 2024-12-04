# AIWA (AI Workflow Automation)

## Quick Start Guide

### 1. Setup Environment
```bash
# Create and activate virtual environment
python -m venv venv312
venv312\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Project
```bash
# Copy environment template
copy configs\.env.template configs\.env

# Edit configs\.env with your settings:
# - Database credentials
# - JWT secrets
# - Other configurations
```

### 3. Database Setup
```bash
# Initialize database
cd scripts/database
python init.py

# Run migrations
alembic upgrade head

# Initialize default data
python -m src.data.database.init_db
```

### 4. Test the Setup

#### A. Test Database Connection
```bash
# Run database tests
cd tests
python test_auth.py
```
Expected output: All tests should pass with no errors

#### B. Test Authentication
1. Register a new user:
```bash
curl -X POST "http://localhost:8000/auth/register" -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"email\":\"test@example.com\",\"password\":\"Test123!\"}"
```
Expected output: User created with access token

2. Login with the user:
```bash
curl -X POST "http://localhost:8000/auth/login" -H "Content-Type: application/json" -d "{\"username\":\"testuser\",\"password\":\"Test123!\"}"
```
Expected output: Access token returned

### 5. Backup and Restore (Optional)

#### Create Backup
```bash
cd scripts/database
python backup.py
```
Backups are saved in the `backups/` directory

#### Restore from Backup
```bash
python backup.py --restore path/to/backup.gz
```

## Authentication System

The AIWA Backend implements a robust authentication system with the following features:

### Key Features
- JWT-based authentication
- Secure password hashing with bcrypt
- Rate limiting protection
- Role-based access control
- Comprehensive logging
- Token refresh mechanism
- Password reset functionality

### Authentication Endpoints

#### User Registration
```http
POST /api/v1/auth/register
```
Register a new user with email, username, and password.

#### User Login
```http
POST /api/v1/auth/login
```
Login with username/email and password to receive access token.

#### Token Refresh
```http
POST /api/v1/auth/refresh
```
Refresh an existing valid token.

#### Password Reset
```http
POST /api/v1/auth/reset-password-request
POST /api/v1/auth/reset-password-confirm
```
Two-step password reset process.

### Security Features

- Password strength validation
- Rate limiting on authentication endpoints
- JWT token expiration
- Secure password hashing
- CORS protection
- Security headers
- Comprehensive error handling
- Event logging

### Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn src.main:app --reload
```

### Testing

Run the test suite:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src tests/
```

### API Documentation

Once the server is running, view the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure
```
graduation_project/
├── configs/          # All configuration files
│   ├── .env         # Environment variables
│   └── alembic.ini  # Database migration config
├── scripts/
│   └── database/    # Database management scripts
├── src/             # Main source code
└── tests/           # Test files
```

## Common Issues and Solutions

### Database Connection Failed
1. Check if PostgreSQL is running
2. Verify database credentials in `configs/.env`
3. Ensure database exists: `aiwa_dev`

### Authentication Failed
1. Check if JWT secret is set in `configs/.env`
2. Verify user exists in database
3. Check password meets requirements:
   - Minimum 8 characters
   - At least 1 uppercase letter
   - At least 1 number
   - At least 1 special character

## Need Help?
- Check logs in `logs/app.log`
- Review error messages in terminal
- Ensure all environment variables are set correctly