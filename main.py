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
                       help="Test database and Google Sheets connections")
    parser.add_argument("--dashboard-name", help="Custom dashboard name")
    parser.add_argument("--user-type", help="Filter users by type")
    parser.add_argument("--department", help="Filter users by department")
    parser.add_argument("--analytics-period", default="30 days",
                       help="Analytics time period (e.g., '30 days', '7 days', '1 year')")
    parser.add_argument("--refresh-spreadsheet", help="Refresh existing spreadsheet by ID")
    parser.add_argument("--make-public", action="store_true", help="Make spreadsheet publicly viewable")
    parser.add_argument("--share-with", help="Email address to share dashboard with")
    
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
        
        # Handle spreadsheet refresh
        if args.refresh_spreadsheet:
            logger.info(f"Refreshing spreadsheet: {args.refresh_spreadsheet}")
            
            # Build user filters
            user_filters = {}
            if args.user_type:
                user_filters["user_type"] = args.user_type
            if args.department:
                user_filters["department"] = args.department
            
            generator.refresh_dashboard(
                args.refresh_spreadsheet,
                user_filters=user_filters if user_filters else None
            )
            
            print(f"\\nSpreadsheet {args.refresh_spreadsheet} refreshed successfully!")
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
        dashboard_result = generator.generate_complete_dashboard(
            dashboard_name=args.dashboard_name,
            user_filters=user_filters if user_filters else None,
            analytics_time_period=args.analytics_period,
            make_public=args.make_public
        )
        
        spreadsheet_id = dashboard_result["spreadsheet_id"]
        spreadsheet_url = dashboard_result["url"]
        
        print(f"\\nDashboard generated successfully!")
        print(f"Spreadsheet ID: {spreadsheet_id}")
        print(f"Spreadsheet URL: {spreadsheet_url}")
        
        # Share if requested
        if args.share_with:
            generator.share_dashboard(spreadsheet_id, args.share_with)
            print(f"Shared with: {args.share_with}")
        
        print("\\nNext steps:")
        print("1. Open the spreadsheet URL above")
        print("2. Go to https://lookerstudio.google.com/")
        print("3. Create New -> Data Source -> Google Sheets")
        print("4. Select your dashboard spreadsheet")
        print("5. Create beautiful reports and dashboards!")
        
        # Show dashboard info
        logger.info("Retrieving dashboard information...")
        dashboard_info = generator.get_dashboard_info()
        
        print(f"\\nGoogle Integration Status:")
        print(f"Google Sheets configured: {dashboard_info['google_configured']}")
        print(f"Created spreadsheets: {len(dashboard_info['cached_spreadsheets'])}")
        
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
