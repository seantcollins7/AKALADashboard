#!/usr/bin/env python3
"""
AKALA Dashboard Generator
Generates professional Power BI dashboards from AWS database data.
"""
import argparse
import logging
import sys
from dotenv import load_dotenv
from interactive_dashboard import InteractiveDashboardSelector
from config import DashboardConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate professional Power BI dashboards from AWS database data")
    
    # Dashboard options
    parser.add_argument("--dashboard-name", default="AKALA Dashboard", 
                       help="Name for the dashboard")
    
    # Filter options
    parser.add_argument("--user-type", help="Filter users by type (admin, active, etc.)")
    parser.add_argument("--department", help="Filter by department")
    parser.add_argument("--analytics-period", default="30d", 
                       help="Analytics time period (e.g., 7d, 30d, 1y)")
    
    # Action options
    parser.add_argument("--test-connections", action="store_true", 
                       help="Test database connection")
    parser.add_argument("--output-dir", default="dashboards",
                       help="Output directory for dashboard files")
    parser.add_argument("--interactive", action="store_true",
                       help="Launch interactive dashboard selector")
    
    args = parser.parse_args()
    
    try:
        # Load configuration
        load_dotenv("akala-db.env")
        config = DashboardConfig.from_env()
        
        logger.info("Loading configuration...")
        
        # Test connections if requested
        if args.test_connections:
            logger.info("Testing connections...")
            test_connections(config)
            return
        
        # Launch interactive mode if requested
        if args.interactive:
            logger.info("Launching interactive dashboard selector...")
            launch_interactive_selector(config)
            return
        
        # Generate Power BI dashboard
        generate_powerbi_dashboard(config, args)
            
    except Exception as e:
        logger.error(f"Failed to generate dashboard: {e}")
        sys.exit(1)

def launch_interactive_selector(config: DashboardConfig):
    """Launch the interactive dashboard selector."""
    try:
        selector = InteractiveDashboardSelector(config)
        selector.show_main_menu()
    except Exception as e:
        logger.error(f"Failed to launch interactive selector: {e}")
        raise

def generate_powerbi_dashboard(config: DashboardConfig, args):
    """Generate Power BI dashboard."""
    try:
        logger.info("Initializing Power BI dashboard generator...")
        
        # For now, redirect to interactive mode
        print("\n🎯 For the best experience, use interactive mode!")
        print("Run: python3 main.py --interactive")
        print("\nOr use the interactive dashboard directly:")
        print("python3 interactive_dashboard.py")
        
    except Exception as e:
        logger.error(f"Failed to generate Power BI dashboard: {e}")
        raise

def test_connections(config: DashboardConfig):
    """Test database connection."""
    try:
        # Test database connection
        print("🔍 Testing connections...")
        
        # Test database
        from database.connection import DatabaseConnection
        db_connection = DatabaseConnection(config.database)
        if db_connection.test_connection():
            print("✅ Database: SUCCESS")
        else:
            print("❌ Database: FAILED")
        
        print("\n✅ Connection tests completed!")
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

if __name__ == "__main__":
    main()
