import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_connection():
    """Fix the database connection and ensure tenants table exists."""
    try:
        # Get database URL from environment
        database_url = os.environ.get("DATABASE_URL")
        if not database_url:
            logger.error("DATABASE_URL environment variable is not set")
            return False
        
        # Create engine with proper SSL parameters
        # Try first with SSL mode=require
        engine = create_engine(
            database_url,
            pool_pre_ping=True,  # This will test the connection before using it
            pool_recycle=300,    # Recycle connections after 5 minutes
            connect_args={"sslmode": "require"}
        )
        
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Test connection by querying tenants table
        try:
            result = session.execute(text("SELECT count(*) FROM tenants"))
            count = result.scalar()
            logger.info(f"Connected to database successfully. Found {count} tenants.")
            session.close()
            return True
        except Exception as e:
            logger.warning(f"Error with SSL mode=require: {e}")
            
            # Try again with SSL mode=prefer
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args={"sslmode": "prefer"}
            )
            
            Session = sessionmaker(bind=engine)
            session = Session()
            
            try:
                result = session.execute(text("SELECT count(*) FROM tenants"))
                count = result.scalar()
                logger.info(f"Connected to database successfully with sslmode=prefer. Found {count} tenants.")
                
                # Update the app's SQLAlchemy config to use this connection mode
                from app import app
                app.config["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"] = {"sslmode": "prefer"}
                logger.info("Updated Flask app SQLAlchemy config with sslmode=prefer")
                
                session.close()
                return True
            except Exception as e2:
                logger.error(f"Error with SSL mode=prefer: {e2}")
                session.close()
                return False
    
    except Exception as e:
        logger.error(f"Error attempting to fix database connection: {e}")
        return False


if __name__ == "__main__":
    # Fix the database connection when run directly
    if fix_database_connection():
        print("Database connection fixed successfully!")
    else:
        print("Failed to fix database connection.")