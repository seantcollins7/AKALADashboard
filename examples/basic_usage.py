#!/usr/bin/env python3
"""
Basic usage example for the AKALA Dashboard Generator.
"""
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DashboardConfig
from dashboard import DashboardGenerator
from utils import setup_logging, get_logger


def main():
    """Basic usage example."""
    
    # Setup logging
    setup_logging("INFO")
    logger = get_logger(__name__)
    
    try:
        # Load configuration from environment variables
        logger.info("Loading configuration...")
        config = DashboardConfig.from_env()
        
        # Initialize dashboard generator
        logger.info("Initializing dashboard generator...")
        generator = DashboardGenerator(config)
        
        # Test connections first
        logger.info("Testing connections...")
        connection_results = generator.test_connections()
        
        if not all(connection_results.values()):
            logger.error("Connection tests failed. Please check your configuration.")
            for service, status in connection_results.items():
                if not status:
                    logger.error(f"{service} connection failed")
            return
        
        logger.info("All connections successful!")
        
        # Generate a basic dashboard
        logger.info("Generating dashboard...")
        dataset_id = generator.generate_complete_dashboard(
            dashboard_name="Basic User Analytics Dashboard",
            analytics_time_period="30 days"
        )
        
        logger.info(f"Dashboard generated successfully!")
        logger.info(f"Dataset ID: {dataset_id}")
        
        # Get dashboard information
        dashboard_info = generator.get_dashboard_info()
        logger.info(f"Total datasets in workspace: {len(dashboard_info['datasets'])}")
        logger.info(f"Total reports in workspace: {len(dashboard_info['reports'])}")
        
        print("\\n" + "="*50)
        print("DASHBOARD GENERATION COMPLETED")
        print("="*50)
        print(f"Dataset ID: {dataset_id}")
        print("\\nNext steps:")
        print("1. Open Power BI Service (app.powerbi.com)")
        print("2. Navigate to your workspace")
        print(f"3. Find the dataset: 'Basic User Analytics Dashboard'")
        print("4. Create a new report using this dataset")
        print("5. Build visualizations and save your report")
        print("6. Pin visuals to a dashboard for sharing")
        
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
    finally:
        # Cleanup
        if 'generator' in locals():
            generator.close()
            logger.info("Cleanup completed")


if __name__ == "__main__":
    main()
