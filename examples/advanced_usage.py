#!/usr/bin/env python3
"""
Advanced usage example for the AKALA Dashboard Generator.
"""
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import DashboardConfig
from dashboard import DashboardGenerator
from utils import setup_logging, get_logger


def main():
    """Advanced usage example with filters and multiple dashboards."""
    
    # Setup logging with file output
    setup_logging("DEBUG", f"logs/advanced_example_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    logger = get_logger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = DashboardConfig.from_env()
        
        # Initialize dashboard generator
        logger.info("Initializing dashboard generator...")
        generator = DashboardGenerator(config)
        
        # Test connections
        logger.info("Testing connections...")
        connection_results = generator.test_connections()
        
        if not all(connection_results.values()):
            logger.error("Connection tests failed")
            return
        
        # Example 1: Department-specific dashboard
        logger.info("Creating department-specific dashboard...")
        sales_dataset_id = generator.generate_complete_dashboard(
            dashboard_name="Sales Department Analytics",
            user_filters={
                "department": "sales",
                "status": "active"
            },
            analytics_time_period="90 days"
        )
        
        print(f"\\nSales Department Dashboard Created!")
        print(f"Dataset ID: {sales_dataset_id}")
        
        # Example 2: Premium users dashboard
        logger.info("Creating premium users dashboard...")
        premium_dataset_id = generator.generate_complete_dashboard(
            dashboard_name="Premium Users Analytics",
            user_filters={
                "user_type": "premium"
            },
            analytics_metrics=["user_activity", "user_registrations"],
            analytics_time_period="180 days"
        )
        
        print(f"\\nPremium Users Dashboard Created!")
        print(f"Dataset ID: {premium_dataset_id}")
        
        # Example 3: Executive summary dashboard (all users, recent activity)
        logger.info("Creating executive summary dashboard...")
        exec_dataset_id = generator.generate_complete_dashboard(
            dashboard_name="Executive Summary Dashboard",
            user_filters={
                "date_from": (datetime.now() - timedelta(days=365)).isoformat(),
                "status": "active"
            },
            analytics_time_period="365 days"
        )
        
        print(f"\\nExecutive Summary Dashboard Created!")
        print(f"Dataset ID: {exec_dataset_id}")
        
        # Example 4: Refresh an existing dashboard
        logger.info("Demonstrating dashboard refresh...")
        generator.refresh_dashboard(
            sales_dataset_id,
            user_filters={"department": "sales", "status": "active"}
        )
        
        print(f"\\nSales Dashboard Refreshed!")
        
        # Get comprehensive dashboard information
        logger.info("Retrieving dashboard information...")
        dashboard_info = generator.get_dashboard_info()
        
        print("\\n" + "="*60)
        print("ADVANCED DASHBOARD GENERATION COMPLETED")
        print("="*60)
        print(f"Total Workspaces: {len(dashboard_info['workspaces'])}")
        print(f"Total Datasets: {len(dashboard_info['datasets'])}")
        print(f"Total Reports: {len(dashboard_info['reports'])}")
        print(f"Total Dashboards: {len(dashboard_info['dashboards'])}")
        
        print("\\nCreated Datasets:")
        print(f"1. Sales Department: {sales_dataset_id}")
        print(f"2. Premium Users: {premium_dataset_id}")
        print(f"3. Executive Summary: {exec_dataset_id}")
        
        print("\\nRecommended Power BI Visualizations:")
        print("\\nFor Sales Department Dashboard:")
        print("- Bar chart: Sales team performance")
        print("- Line chart: Sales activities over time")
        print("- Card: Total active sales users")
        print("- Table: Sales user details with filters")
        
        print("\\nFor Premium Users Dashboard:")
        print("- Pie chart: Premium vs other user types")
        print("- Line chart: Premium user growth over time")
        print("- Gauge: Premium user engagement score")
        print("- Map: Geographic distribution of premium users")
        
        print("\\nFor Executive Summary Dashboard:")
        print("- KPI cards: Total users, active users, growth rate")
        print("- Stacked bar chart: Users by department and type")
        print("- Area chart: User activity trends")
        print("- Heatmap: Activity patterns by day/hour")
        
    except Exception as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
    finally:
        # Cleanup
        if 'generator' in locals():
            generator.close()
            logger.info("Cleanup completed")


if __name__ == "__main__":
    main()
