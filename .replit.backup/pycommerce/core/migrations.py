"""
Database migration utilities for PyCommerce SDK.

This module provides tools for managing database migrations
in a multi-tenant environment.
"""

import os
import logging
import alembic
from alembic.config import Config
from alembic import command
from pathlib import Path

from pycommerce.core.db import engine, init_db

# Configure logging
logger = logging.getLogger("pycommerce.migrations")


def create_migration_config():
    """Create an Alembic configuration object."""
    # Get base directory
    base_dir = Path(__file__).parent.parent.parent
    migrations_dir = base_dir / "migrations"
    
    # Create migrations directory if it doesn't exist
    migrations_dir.mkdir(exist_ok=True)
    
    # Create alembic directory if it doesn't exist
    alembic_dir = migrations_dir / "alembic"
    alembic_dir.mkdir(exist_ok=True)
    
    # Create versions directory if it doesn't exist
    versions_dir = alembic_dir / "versions"
    versions_dir.mkdir(exist_ok=True)
    
    # Create alembic.ini if it doesn't exist
    alembic_ini = base_dir / "alembic.ini"
    if not alembic_ini.exists():
        with open(alembic_ini, "w") as f:
            f.write("""[alembic]
script_location = migrations/alembic
prepend_sys_path = .
sqlalchemy.url = %s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %%(levelname)-5.5s [%%(name)s] %%(message)s
datefmt = %%H:%%M:%%S
""" % os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost/pycommerce"))
    
    # Create alembic env.py if it doesn't exist
    env_py = alembic_dir / "env.py"
    if not env_py.exists():
        with open(env_py, "w") as f:
            f.write("""import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Add the parent directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the models
from pycommerce.core.db import Base, engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    \"\"\"Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    \"\"\"
    url = os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    \"\"\"Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    \"\"\"
    connectable = engine

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata,
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
""")
    
    # Create Alembic config
    config = Config(alembic_ini)
    config.set_main_option("script_location", str(migrations_dir / "alembic"))
    
    return config


def init_migrations():
    """Initialize the migrations system."""
    try:
        # Create migration config
        config = create_migration_config()
        
        # Initialize database schema
        init_db()
        
        logger.info("Database migrations initialized")
        return config
    except Exception as e:
        logger.error(f"Error initializing migrations: {str(e)}")
        raise


def create_migration(message):
    """
    Create a new migration.
    
    Args:
        message: The migration message
    """
    try:
        config = create_migration_config()
        command.revision(config, message=message, autogenerate=True)
        logger.info(f"Created migration: {message}")
    except Exception as e:
        logger.error(f"Error creating migration: {str(e)}")
        raise


def upgrade_database():
    """Upgrade the database to the latest migration."""
    try:
        config = create_migration_config()
        command.upgrade(config, "head")
        logger.info("Database upgraded to latest migration")
    except Exception as e:
        logger.error(f"Error upgrading database: {str(e)}")
        raise


def downgrade_database(revision):
    """
    Downgrade the database to a specific revision.
    
    Args:
        revision: The revision to downgrade to
    """
    try:
        config = create_migration_config()
        command.downgrade(config, revision)
        logger.info(f"Database downgraded to {revision}")
    except Exception as e:
        logger.error(f"Error downgrading database: {str(e)}")
        raise