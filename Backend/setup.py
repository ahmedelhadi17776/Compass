from setuptools import setup, find_packages

setup(
    name="compass-backend",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "sqlalchemy",
        "alembic",
        "python-jose[cryptography]",
        "passlib",
        "python-multipart",
        "pytest",
        "pytest-asyncio",
        "aiosqlite",
        "httpx"
    ],
) 