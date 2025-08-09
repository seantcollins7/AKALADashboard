#!/usr/bin/env python3
"""
Simple database connection test script.
Run this to test your database configuration before setting up Power BI.
"""
import sys
from config import DashboardConfig
from database import DatabaseConnection
from utils import setup_logging, get_logger


def main():
    """Test database connection only."""
    
    # Setup logging
    setup_logging("INFO")
    logger = get_logger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = DashboardConfig.from_env()
        
        # Check if database config is loaded
        if not config.database.host:
            logger.error("Database configuration not found. Please check your akala-db.env file.")
            return 1
        
        logger.info(f"Database config loaded:")
        logger.info(f"  Host: {config.database.host}")
        logger.info(f"  Port: {config.database.port}")
        logger.info(f"  Database: {config.database.database}")
        logger.info(f"  Engine: {config.database.engine}")
        logger.info(f"  Username: {config.database.username}")
        
        # Initialize database connection
        logger.info("Initializing database connection...")
        db_connection = DatabaseConnection(config.database, config.aws)
        
        # Test connection
        logger.info("Testing database connection...")
        if db_connection.test_connection():
            logger.info("✅ Database connection successful!")
            
            # Try a simple query
            logger.info("Testing a simple query...")
            try:
                result = db_connection.execute_query("SELECT 1 as test_column")
                logger.info(f"✅ Query test successful! Result: {result.iloc[0]['test_column']}")
            except Exception as e:
                logger.warning(f"Query test failed (but connection works): {e}")
            
            print("\n" + "="*50)
            print("✅ DATABASE CONNECTION SUCCESSFUL!")
            print("="*50)
            print("Your database configuration is working correctly.")
            print("You can now add Power BI configuration when ready.")
            
        else:
            logger.error("❌ Database connection failed!")
            print("\n" + "="*50)
            print("❌ DATABASE CONNECTION FAILED!")
            print("="*50)
            print("Please check:")
            print("1. Your database credentials in akala-db.env")
            print("2. Network connectivity to the database")
            print("3. Database server is running")
            print("4. Firewall/security group settings")
            return 1
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print("\n" + "="*50)
        print("❌ CONFIGURATION ERROR!")
        print("="*50)
        print(f"Error: {e}")
        print("\nPlease check your akala-db.env file configuration.")
        return 1
    finally:
        # Cleanup
        if 'db_connection' in locals():
            db_connection.close()
            logger.info("Database connection closed")


if __name__ == "__main__":
    sys.exit(main())
