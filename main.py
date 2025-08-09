#!/usr/bin/env python3
"""
AKALA Dashboard Generator - Main entry point
"""
import argparse
import sys
from typing import Dict, Any, Optional

from config import DashboardConfig
from dashboard import DashboardGenerator
from utils import setup_logging, get_logger


def main():
    """Main entry point for the dashboard generator."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AKALA Dashboard Generator")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--log-level", default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                       help="Logging level")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--test-connections", action="store_true",
                       help="Test database and Power BI connections")
    parser.add_argument("--dashboard-name", help="Custom dashboard name")
    parser.add_argument("--user-type", help="Filter users by type")
    parser.add_argument("--department", help="Filter users by department")
    parser.add_argument("--analytics-period", default="30 days",
                       help="Analytics time period (e.g., '30 days', '7 days', '1 year')")
    parser.add_argument("--refresh-dataset", help="Refresh existing dataset by ID")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = get_logger(__name__)
    
    try:
        # Load configuration
        logger.info("Loading configuration...")
        config = DashboardConfig.from_env()
        
        # Initialize dashboard generator
        logger.info("Initializing dashboard generator...")
        generator = DashboardGenerator(config)
        
        # Test connections if requested
        if args.test_connections:
            logger.info("Testing connections...")
            results = generator.test_connections()
            
            print("\\nConnection Test Results:")
            print("-" * 30)
            for service, status in results.items():
                status_text = "✓ SUCCESS" if status else "✗ FAILED"
                print(f"{service.capitalize()}: {status_text}")
            
            if not all(results.values()):
                logger.error("Some connection tests failed")
                return 1
            
            logger.info("All connection tests passed")
            return 0
        
        # Handle dataset refresh
        if args.refresh_dataset:
            logger.info(f"Refreshing dataset: {args.refresh_dataset}")
            
            # Build user filters
            user_filters = {}
            if args.user_type:
                user_filters["user_type"] = args.user_type
            if args.department:
                user_filters["department"] = args.department
            
            generator.refresh_dashboard(
                args.refresh_dataset,
                user_filters=user_filters if user_filters else None
            )
            
            print(f"\\nDataset {args.refresh_dataset} refreshed successfully!")
            return 0
        
        # Generate new dashboard
        logger.info("Generating dashboard...")
        
        # Build user filters
        user_filters = {}
        if args.user_type:
            user_filters["user_type"] = args.user_type
        if args.department:
            user_filters["department"] = args.department
        
        # Generate dashboard
        dataset_id = generator.generate_complete_dashboard(
            dashboard_name=args.dashboard_name,
            user_filters=user_filters if user_filters else None,
            analytics_time_period=args.analytics_period
        )
        
        print(f"\\nDashboard generated successfully!")
        print(f"Dataset ID: {dataset_id}")
        print("\\nYou can now create reports and dashboards in Power BI using this dataset.")
        
        # Show dashboard info
        logger.info("Retrieving dashboard information...")
        dashboard_info = generator.get_dashboard_info()
        
        print(f"\\nPower BI Workspace Info:")
        print(f"Available datasets: {len(dashboard_info['datasets'])}")
        print(f"Available reports: {len(dashboard_info['reports'])}")
        print(f"Available dashboards: {len(dashboard_info['dashboards'])}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}", exc_info=True)
        return 1
    finally:
        # Cleanup
        if 'generator' in locals():
            generator.close()


if __name__ == "__main__":
    sys.exit(main())
