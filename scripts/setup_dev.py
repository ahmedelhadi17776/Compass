"""Development environment setup script."""
import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version meets requirements."""
    required_version = (3, 12)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print(f"Error: Python {required_version[0]}.{required_version[1]} or higher is required")
        print(f"Current version: Python {current_version[0]}.{current_version[1]}")
        sys.exit(1)
    print(f"[OK] Python version {current_version[0]}.{current_version[1]} meets requirements")

def create_virtual_environment():
    """Create virtual environment if it doesn't exist."""
    venv_path = Path("venv312")
    if venv_path.exists():
        print("[OK] Virtual environment already exists")
        return
    
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv312"], check=True)
        print("[OK] Created virtual environment")
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        sys.exit(1)

def install_dependencies():
    """Install project dependencies."""
    python_cmd = "venv312\\Scripts\\python.exe" if platform.system() == "Windows" else "venv312/bin/python"
    pip_cmd = "venv312\\Scripts\\pip.exe" if platform.system() == "Windows" else "venv312/bin/pip"
    
    try:
        # Upgrade pip
        subprocess.run([python_cmd, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        print("[OK] Upgraded pip")
        
        # Install dependencies
        subprocess.run([pip_cmd, "install", "-r", "requirements.txt"], check=True)
        print("[OK] Installed dependencies")
        
        # Install development dependencies
        subprocess.run([pip_cmd, "install", "-r", "requirements-dev.txt"], check=True)
        print("[OK] Installed development dependencies")
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        sys.exit(1)

def setup_environment_variables():
    """Set up environment variables from template."""
    env_template = Path("configs/.env.template")
    env_file = Path("configs/.env")
    
    if not env_template.exists():
        print("Error: .env.template file not found")
        sys.exit(1)
    
    if not env_file.exists():
        env_file.write_text(env_template.read_text())
        print("[OK] Created .env file from template")
    else:
        print("[OK] .env file already exists")

def initialize_database():
    """Initialize database with Alembic."""
    alembic_cmd = "venv312\\Scripts\\alembic.exe" if platform.system() == "Windows" else "venv312/bin/alembic"
    
    try:
        # Run migrations
        subprocess.run([alembic_cmd, "-c", "configs/alembic.ini", "upgrade", "head"], check=True)
        print("[OK] Applied database migrations")
        
        # Run database seeding
        python_cmd = "venv312\\Scripts\\python.exe" if platform.system() == "Windows" else "venv312/bin/python"
        subprocess.run([python_cmd, "scripts/database/seed_data.py"], check=True)
        print("[OK] Seeded database with initial data")
    except subprocess.CalledProcessError as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)

def run_tests():
    """Run test suite."""
    pytest_cmd = "venv312\\Scripts\\pytest.exe" if platform.system() == "Windows" else "venv312/bin/pytest"
    
    try:
        subprocess.run([pytest_cmd, "tests"], check=True)
        print("[OK] All tests passed")
    except subprocess.CalledProcessError as e:
        print(f"Error: Some tests failed: {e}")
        sys.exit(1)

def main():
    """Main setup function."""
    print("Setting up development environment...")
    
    # Create necessary directories
    os.makedirs("logs", exist_ok=True)
    os.makedirs("backups", exist_ok=True)
    
    # Run setup steps
    check_python_version()
    create_virtual_environment()
    install_dependencies()
    setup_environment_variables()
    initialize_database()
    run_tests()
    
    print("""
Development environment setup complete!

To start developing:
1. Activate virtual environment:
   - Windows: .\\venv312\\Scripts\\activate
   - Unix: source venv312/bin/activate
   
2. Start the development server:
   python -m uvicorn src.main:app --reload --port 8000
   
3. View API documentation:
   http://localhost:8000/api/docs
   
Happy coding!
""")

if __name__ == "__main__":
    main()
