"""
Core dashboard generator that orchestrates data retrieval and Google Sheets/Looker Studio integration.
"""
import logging
from typing import Dict, Any, List, Optional, Union
try:
    import pandas as pd  # type: ignore
    HAS_PANDAS = True
except Exception:
    HAS_PANDAS = False
from datetime import datetime, timedelta

from config import DashboardConfig
from database import DatabaseConnection
from google_integration import GoogleSheetsClient, prepare_dataframe_for_looker_studio

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Main dashboard generator class that coordinates data flow from AWS to Google Sheets/Looker Studio."""
    
    def __init__(self, config: DashboardConfig):
        """
        Initialize dashboard generator.
        
        Args:
            config: Complete dashboard configuration
        """
        self.config = config
        self.db_connection = DatabaseConnection(config.database, config.aws)
        self.google_client = GoogleSheetsClient(config.google) if config.google else None
        self._spreadsheets_cache: Dict[str, str] = {}  # name -> spreadsheet_id mapping
        
    def test_connections(self) -> Dict[str, bool]:
        """
        Test all connections (database and Google Sheets).
        
        Returns:
            Dictionary with connection test results
        """
        results = {}
        
        # Test database connection
        try:
            results["database"] = self.db_connection.test_connection()
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            results["database"] = False
        
        # Test Google Sheets connection (if configured)
        if self.google_client:
            try:
                connection_status = self.google_client.test_connection()
                results["google_sheets"] = connection_status
                if connection_status:
                    logger.info("Google Sheets API connection successful")
            except Exception as e:
                logger.error(f"Google Sheets connection test failed: {e}")
                results["google_sheets"] = False
        else:
            results["google_sheets"] = "not_configured"
            logger.info("Google Sheets not configured - skipping connection test")
        
        return results
    
    def create_dashboard_spreadsheet(self, dashboard_name: Optional[str] = None) -> str:
        """
        Create a Google Spreadsheet for dashboard data.
        
        Args:
            dashboard_name: Custom dashboard name (auto-generated if not provided)
            
        Returns:
            Created spreadsheet ID
        """
        if not self.google_client:
            raise Exception("Google Sheets client not configured")
            
        if not dashboard_name:
            dashboard_name = f"UserDashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            spreadsheet_id = self.google_client.create_dashboard_spreadsheet(dashboard_name)
            self._spreadsheets_cache[dashboard_name] = spreadsheet_id
            logger.info(f"Created Google Spreadsheet '{dashboard_name}' with ID: {spreadsheet_id}")
            return spreadsheet_id
        except Exception as e:
            logger.error(f"Failed to create Google Spreadsheet: {e}")
            raise
    
    def update_user_data(self, spreadsheet_id: str, user_filters: Optional[Dict[str, Any]] = None, 
                        clear_existing: bool = True) -> None:
        """
        Update user data in Google Sheets.
        
        Args:
            spreadsheet_id: Google Spreadsheet ID
            user_filters: Filters to apply when retrieving user data
            clear_existing: Whether to clear existing data before adding new data
        """
        if not self.google_client:
            raise Exception("Google Sheets client not configured")
        if not HAS_PANDAS:
            raise ImportError("pandas is required to process and upload dataframes to Google Sheets.")
            
        try:
            # Retrieve user data from database
            logger.info("Retrieving user data from database...")
            user_data = self.db_connection.get_user_data(user_filters)
            
            if getattr(user_data, "empty", False):
                logger.warning("No user data found with provided filters")
                return
            
            # Prepare data for Google Sheets/Looker Studio
            user_data_clean = prepare_dataframe_for_looker_studio(user_data)
            
            # Upload data to Google Sheets
            self.google_client.write_dataframe_to_sheet(
                spreadsheet_id, 
                "Users", 
                user_data_clean, 
                clear_existing=clear_existing
            )
            logger.info(f"Successfully updated {len(user_data_clean)} user records in Google Sheets")
            
        except Exception as e:
            logger.error(f"Failed to update user data: {e}")
            raise
    
    def update_analytics_data(self, spreadsheet_id: str, metrics: List[str], 
                            time_period: Optional[str] = None, clear_existing: bool = True) -> None:
        """
        Update analytics data in Google Sheets.
        
        Args:
            spreadsheet_id: Google Spreadsheet ID
            metrics: List of metric types to retrieve
            time_period: Time period for analytics data
            clear_existing: Whether to clear existing data before adding new data
        """
        if not self.google_client:
            raise Exception("Google Sheets client not configured")
        if not HAS_PANDAS:
            raise ImportError("pandas is required to process and upload dataframes to Google Sheets.")
            
        try:
            all_analytics_data = []
            
            # Retrieve each metric type
            for metric_type in metrics:
                logger.info(f"Retrieving {metric_type} analytics data...")
                metric_data = self.db_connection.get_analytics_data(metric_type, time_period)
                
                if not getattr(metric_data, "empty", True):
                    # Add metric type column
                    metric_data["metric_type"] = metric_type
                    
                    # Standardize column names for analytics table
                    if "active_users" in metric_data.columns:
                        metric_data["metric_value"] = metric_data["active_users"]
                        metric_data["category"] = "active_users"
                    elif "new_registrations" in metric_data.columns:
                        metric_data["metric_value"] = metric_data["new_registrations"]
                        metric_data["category"] = metric_data.get("user_type", "all")
                    elif "total_logins" in metric_data.columns:
                        metric_data["metric_value"] = metric_data["total_logins"]
                        metric_data["category"] = "total_logins"
                    
                    # Select only required columns
                    analytics_subset = metric_data[["date", "metric_type", "metric_value", "category"]].copy()
                    all_analytics_data.append(analytics_subset)
            
            if not all_analytics_data:
                logger.warning("No analytics data found")
                return
            
            # Combine all analytics data
            combined_data = pd.concat(all_analytics_data, ignore_index=True)
            analytics_data_clean = prepare_dataframe_for_looker_studio(combined_data)
            
            # Upload data to Google Sheets
            self.google_client.write_dataframe_to_sheet(
                spreadsheet_id, 
                "Analytics", 
                analytics_data_clean, 
                clear_existing=clear_existing
            )
            logger.info(f"Successfully updated {len(analytics_data_clean)} analytics records in Google Sheets")
            
        except Exception as e:
            logger.error(f"Failed to update analytics data: {e}")
            raise
    
    def create_summary_sheet(self, spreadsheet_id: str) -> None:
        """
        Create a summary sheet with key metrics.
        
        Args:
            spreadsheet_id: Google Spreadsheet ID
        """
        if not self.google_client:
            raise Exception("Google Sheets client not configured")
        if not HAS_PANDAS:
            raise ImportError("pandas is required to process and upload dataframes to Google Sheets.")
            
        try:
            # Get summary data from database
            user_data = self.db_connection.get_user_data()
            
            # Calculate summary metrics
            summary_data = {
                'Metric': [
                    'Total Users',
                    'Active Users',
                    'New Users (Last 30 Days)',
                    'Premium Users',
                    'Most Common Department',
                    'Last Updated'
                ],
                'Value': [
                    len(user_data),
                    len(user_data[user_data['status'] == 'active']) if 'status' in user_data.columns else 'N/A',
                    len(user_data[user_data['created_at'] >= (datetime.now() - timedelta(days=30))]) if 'created_at' in user_data.columns else 'N/A',
                    len(user_data[user_data['user_type'] == 'premium']) if 'user_type' in user_data.columns else 'N/A',
                    user_data['department'].mode().iloc[0] if 'department' in user_data.columns and not user_data['department'].empty else 'N/A',
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            
            # Upload to Google Sheets
            self.google_client.write_dataframe_to_sheet(
                spreadsheet_id, 
                "Summary", 
                summary_df, 
                clear_existing=True
            )
            logger.info("Successfully created summary sheet")
            
        except Exception as e:
            logger.error(f"Failed to create summary sheet: {e}")
            raise
    
    def generate_complete_dashboard(self, dashboard_name: Optional[str] = None,
                                  user_filters: Optional[Dict[str, Any]] = None,
                                  analytics_metrics: Optional[List[str]] = None,
                                  analytics_time_period: Optional[str] = None,
                                  make_public: bool = False) -> Dict[str, str]:
        """
        Generate a complete dashboard with user and analytics data.
        
        Args:
            dashboard_name: Custom dashboard name
            user_filters: Filters for user data
            analytics_metrics: List of analytics metrics to include
            analytics_time_period: Time period for analytics
            make_public: Whether to make the spreadsheet publicly viewable
            
        Returns:
            Dictionary with spreadsheet_id and url
        """
        # Set defaults
        if analytics_metrics is None:
            analytics_metrics = ["user_activity", "user_registrations"]
        
        if analytics_time_period is None:
            analytics_time_period = "30 days"
        
        try:
            # Create spreadsheet
            logger.info("Creating Google Spreadsheet...")
            spreadsheet_id = self.create_dashboard_spreadsheet(dashboard_name)
            
            # Update user data
            logger.info("Updating user data...")
            self.update_user_data(spreadsheet_id, user_filters)
            
            # Update analytics data
            logger.info("Updating analytics data...")
            self.update_analytics_data(spreadsheet_id, analytics_metrics, analytics_time_period)
            
            # Create summary sheet
            logger.info("Creating summary sheet...")
            self.create_summary_sheet(spreadsheet_id)
            
            # Get spreadsheet URL
            spreadsheet_url = self.google_client.get_spreadsheet_url(spreadsheet_id)
            
            # Make public if requested
            if make_public:
                self.google_client.make_public_viewable(spreadsheet_id)
                logger.info("Made spreadsheet publicly viewable")
            
            logger.info(f"Dashboard generation completed successfully. Spreadsheet ID: {spreadsheet_id}")
            
            return {
                "spreadsheet_id": spreadsheet_id,
                "url": spreadsheet_url,
                "looker_studio_url": f"https://lookerstudio.google.com/datasources/create?connectorId=AKEAFjCMCpf"
            }
            
        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
            raise
    
    def refresh_dashboard(self, spreadsheet_id: str, update_user_data: bool = True,
                         update_analytics: bool = True, user_filters: Optional[Dict[str, Any]] = None,
                         analytics_metrics: Optional[List[str]] = None) -> None:
        """
        Refresh an existing dashboard with latest data.
        
        Args:
            spreadsheet_id: Existing spreadsheet ID
            update_user_data: Whether to update user data
            update_analytics: Whether to update analytics data
            user_filters: Filters for user data
            analytics_metrics: Analytics metrics to update
        """
        try:
            if update_user_data:
                logger.info("Refreshing user data...")
                self.update_user_data(spreadsheet_id, user_filters)
            
            if update_analytics:
                if analytics_metrics is None:
                    analytics_metrics = ["user_activity", "user_registrations"]
                logger.info("Refreshing analytics data...")
                self.update_analytics_data(spreadsheet_id, analytics_metrics)
            
            # Update summary
            logger.info("Refreshing summary sheet...")
            self.create_summary_sheet(spreadsheet_id)
            
            logger.info("Dashboard refresh completed successfully")
            
        except Exception as e:
            logger.error(f"Dashboard refresh failed: {e}")
            raise
    
    def get_dashboard_info(self) -> Dict[str, Any]:
        """
        Get information about created spreadsheets.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            return {
                "cached_spreadsheets": self._spreadsheets_cache,
                "google_configured": self.google_client is not None,
                "instructions": {
                    "looker_studio": "1. Go to https://lookerstudio.google.com/\n2. Create New -> Data Source\n3. Select Google Sheets\n4. Choose your dashboard spreadsheet\n5. Create reports using the data",
                    "sharing": "Use the spreadsheet URL to share with team members or make it public"
                }
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard info: {e}")
            raise
    
    def share_dashboard(self, spreadsheet_id: str, email: str, role: str = 'reader') -> None:
        """
        Share dashboard with an email address.
        
        Args:
            spreadsheet_id: Spreadsheet ID
            email: Email address to share with
            role: Permission role ('reader', 'writer', 'commenter')
        """
        if not self.google_client:
            raise Exception("Google Sheets client not configured")
            
        try:
            self.google_client.share_spreadsheet(spreadsheet_id, email, role)
            logger.info(f"Shared dashboard with {email}")
        except Exception as e:
            logger.error(f"Failed to share dashboard: {e}")
            raise
    
    def close(self):
        """Clean up resources."""
        if self.db_connection:
            self.db_connection.close()
        logger.info("Dashboard generator resources cleaned up")
