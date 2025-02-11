from Backend.data.database.models import Base  # Ensure this imports all models
from Backend.data.database.connection import DATABASE_URL
from Backend.data.database.models import Base
from logging.config import fileConfig
import os
import sys
import logging
from alembic import context
from sqlalchemy import engine_from_config, pool


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define the project root directory
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '../../..'))

# Add the project root to sys.path to ensure modules can be imported
sys.path.append(project_root)


# Import the Base and DATABASE_URL
from Backend.data.database.models import Base  # Ensure this imports all models
# this is the Alembic Config object, which provides

# access to the values within the .ini file in use.
config = context.config

# override sqlalchemy.url with the one from our connection module
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Update config file path for the new location
if config.config_file_name is not None:
    config_path = os.path.join(project_root, 'configs', 'alembic.ini')
    if os.path.exists(config_path):
        fileConfig(config_path)
    else:
        logger.warning(f"Alembic config file not found at {config_path}")
else:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    try:
        url = config.get_main_option("sqlalchemy.url")
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
    except Exception as e:
        logger.error(f"Offline migration error: {e}")
        raise


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    try:
        # Create an Engine from the configuration
        connectable = engine_from_config(
            config.get_section(config.config_ini_section),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()
    except Exception as e:
        logger.error(f"Online migration error: {e}")
        raise


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
