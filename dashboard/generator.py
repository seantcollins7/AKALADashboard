"""
Core dashboard generator that orchestrates data retrieval and Power BI integration.
"""
import logging
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from datetime import datetime, timedelta

from config import DashboardConfig
from database import DatabaseConnection
from powerbi import PowerBIClient, create_dataset_schema

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Main dashboard generator class that coordinates data flow from AWS to Power BI."""
    
    def __init__(self, config: DashboardConfig):
        """
        Initialize dashboard generator.
        
        Args:
            config: Complete dashboard configuration
        """
        self.config = config
        self.db_connection = DatabaseConnection(config.database, config.aws)
        self.powerbi_client = PowerBIClient(config.powerbi)
        self._datasets_cache: Dict[str, str] = {}  # name -> dataset_id mapping
        
    def test_connections(self) -> Dict[str, bool]:
        """
        Test all connections (database and Power BI).
        
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
        
        # Test Power BI connection
        try:
            workspaces = self.powerbi_client.get_workspaces()
            results["powerbi"] = len(workspaces) >= 0  # Should return at least empty list
            logger.info(f"Power BI connection successful, found {len(workspaces)} workspaces")
        except Exception as e:
            logger.error(f"Power BI connection test failed: {e}")
            results["powerbi"] = False
        
        return results
    
    def _infer_powerbi_column_type(self, pandas_dtype: str) -> str:
        """
        Map pandas data types to Power BI column types.
        
        Args:
            pandas_dtype: Pandas data type string
            
        Returns:
            Power BI column type
        """
        dtype_mapping = {
            'int64': 'Int64',
            'int32': 'Int64',
            'float64': 'Double',
            'float32': 'Double',
            'object': 'String',
            'bool': 'Boolean',
            'datetime64[ns]': 'DateTime',
            'timedelta64[ns]': 'String'
        }
        
        return dtype_mapping.get(str(pandas_dtype), 'String')
    
    def _prepare_data_for_powerbi(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for Power BI upload by handling data types and nulls.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Processed DataFrame ready for Power BI
        """
        df_clean = df.copy()
        
        # Handle datetime columns
        for col in df_clean.columns:
            if df_clean[col].dtype == 'datetime64[ns]':
                # Convert to ISO format string for Power BI
                df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            elif df_clean[col].dtype == 'timedelta64[ns]':
                # Convert timedelta to string
                df_clean[col] = df_clean[col].astype(str)
        
        # Replace NaN values with None for proper JSON serialization
        df_clean = df_clean.where(pd.notnull(df_clean), None)
        
        return df_clean
    
    def create_user_dashboard_dataset(self, dataset_name: Optional[str] = None) -> str:
        """
        Create a Power BI dataset for user dashboard data.
        
        Args:
            dataset_name: Custom dataset name (auto-generated if not provided)
            
        Returns:
            Created dataset ID
        """
        if not dataset_name:
            dataset_name = f"UserDashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Define schema for user data
        user_columns = [
            {"name": "user_id", "dataType": "String"},
            {"name": "username", "dataType": "String"},
            {"name": "email", "dataType": "String"},
            {"name": "created_at", "dataType": "DateTime"},
            {"name": "last_login", "dataType": "DateTime"},
            {"name": "user_type", "dataType": "String"},
            {"name": "status", "dataType": "String"},
            {"name": "department", "dataType": "String"},
            {"name": "role", "dataType": "String"}
        ]
        
        # Define schema for analytics data
        analytics_columns = [
            {"name": "date", "dataType": "DateTime"},
            {"name": "metric_type", "dataType": "String"},
            {"name": "metric_value", "dataType": "Int64"},
            {"name": "category", "dataType": "String"}
        ]
        
        # Create dataset with multiple tables
        dataset_definition = {
            "name": dataset_name,
            "tables": [
                {
                    "name": "Users",
                    "columns": user_columns
                },
                {
                    "name": "Analytics",
                    "columns": analytics_columns
                }
            ]
        }
        
        try:
            result = self.powerbi_client.create_dataset(dataset_definition)
            dataset_id = result["id"]
            self._datasets_cache[dataset_name] = dataset_id
            logger.info(f"Created Power BI dataset '{dataset_name}' with ID: {dataset_id}")
            return dataset_id
        except Exception as e:
            logger.error(f"Failed to create Power BI dataset: {e}")
            raise
    
    def update_user_data(self, dataset_id: str, user_filters: Optional[Dict[str, Any]] = None, 
                        clear_existing: bool = True) -> None:
        """
        Update user data in Power BI dataset.
        
        Args:
            dataset_id: Power BI dataset ID
            user_filters: Filters to apply when retrieving user data
            clear_existing: Whether to clear existing data before adding new data
        """
        try:
            # Retrieve user data from database
            logger.info("Retrieving user data from database...")
            user_data = self.db_connection.get_user_data(user_filters)
            
            if user_data.empty:
                logger.warning("No user data found with provided filters")
                return
            
            # Prepare data for Power BI
            user_data_clean = self._prepare_data_for_powerbi(user_data)
            
            # Clear existing data if requested
            if clear_existing:
                self.powerbi_client.delete_dataset_rows(dataset_id, "Users")
                logger.info("Cleared existing user data from Power BI dataset")
            
            # Upload data to Power BI
            self.powerbi_client.push_data_to_dataset(dataset_id, "Users", user_data_clean)
            logger.info(f"Successfully updated {len(user_data_clean)} user records in Power BI")
            
        except Exception as e:
            logger.error(f"Failed to update user data: {e}")
            raise
    
    def update_analytics_data(self, dataset_id: str, metrics: List[str], 
                            time_period: Optional[str] = None, clear_existing: bool = True) -> None:
        """
        Update analytics data in Power BI dataset.
        
        Args:
            dataset_id: Power BI dataset ID
            metrics: List of metric types to retrieve
            time_period: Time period for analytics data
            clear_existing: Whether to clear existing data before adding new data
        """
        try:
            all_analytics_data = []
            
            # Retrieve each metric type
            for metric_type in metrics:
                logger.info(f"Retrieving {metric_type} analytics data...")
                metric_data = self.db_connection.get_analytics_data(metric_type, time_period)
                
                if not metric_data.empty:
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
            analytics_data_clean = self._prepare_data_for_powerbi(combined_data)
            
            # Clear existing data if requested
            if clear_existing:
                self.powerbi_client.delete_dataset_rows(dataset_id, "Analytics")
                logger.info("Cleared existing analytics data from Power BI dataset")
            
            # Upload data to Power BI
            self.powerbi_client.push_data_to_dataset(dataset_id, "Analytics", analytics_data_clean)
            logger.info(f"Successfully updated {len(analytics_data_clean)} analytics records in Power BI")
            
        except Exception as e:
            logger.error(f"Failed to update analytics data: {e}")
            raise
    
    def generate_complete_dashboard(self, dashboard_name: Optional[str] = None,
                                  user_filters: Optional[Dict[str, Any]] = None,
                                  analytics_metrics: Optional[List[str]] = None,
                                  analytics_time_period: Optional[str] = None) -> str:
        """
        Generate a complete dashboard with user and analytics data.
        
        Args:
            dashboard_name: Custom dashboard name
            user_filters: Filters for user data
            analytics_metrics: List of analytics metrics to include
            analytics_time_period: Time period for analytics
            
        Returns:
            Power BI dataset ID for the created dashboard
        """
        # Set defaults
        if analytics_metrics is None:
            analytics_metrics = ["user_activity", "user_registrations"]
        
        if analytics_time_period is None:
            analytics_time_period = "30 days"
        
        try:
            # Create dataset
            logger.info("Creating Power BI dataset...")
            dataset_id = self.create_user_dashboard_dataset(dashboard_name)
            
            # Update user data
            logger.info("Updating user data...")
            self.update_user_data(dataset_id, user_filters)
            
            # Update analytics data
            logger.info("Updating analytics data...")
            self.update_analytics_data(dataset_id, analytics_metrics, analytics_time_period)
            
            # Trigger dataset refresh
            logger.info("Triggering dataset refresh...")
            self.powerbi_client.refresh_dataset(dataset_id)
            
            logger.info(f"Dashboard generation completed successfully. Dataset ID: {dataset_id}")
            return dataset_id
            
        except Exception as e:
            logger.error(f"Dashboard generation failed: {e}")
            raise
    
    def refresh_dashboard(self, dataset_id: str, update_user_data: bool = True,
                         update_analytics: bool = True, user_filters: Optional[Dict[str, Any]] = None,
                         analytics_metrics: Optional[List[str]] = None) -> None:
        """
        Refresh an existing dashboard with latest data.
        
        Args:
            dataset_id: Existing dataset ID
            update_user_data: Whether to update user data
            update_analytics: Whether to update analytics data
            user_filters: Filters for user data
            analytics_metrics: Analytics metrics to update
        """
        try:
            if update_user_data:
                logger.info("Refreshing user data...")
                self.update_user_data(dataset_id, user_filters)
            
            if update_analytics:
                if analytics_metrics is None:
                    analytics_metrics = ["user_activity", "user_registrations"]
                logger.info("Refreshing analytics data...")
                self.update_analytics_data(dataset_id, analytics_metrics)
            
            # Trigger dataset refresh
            self.powerbi_client.refresh_dataset(dataset_id)
            logger.info("Dashboard refresh completed successfully")
            
        except Exception as e:
            logger.error(f"Dashboard refresh failed: {e}")
            raise
    
    def get_dashboard_info(self) -> Dict[str, Any]:
        """
        Get information about available dashboards and datasets.
        
        Returns:
            Dictionary with dashboard information
        """
        try:
            workspaces = self.powerbi_client.get_workspaces()
            datasets = self.powerbi_client.get_datasets()
            reports = self.powerbi_client.get_reports()
            dashboards = self.powerbi_client.get_dashboards()
            
            return {
                "workspaces": workspaces,
                "datasets": datasets,
                "reports": reports,
                "dashboards": dashboards,
                "cached_datasets": self._datasets_cache
            }
        except Exception as e:
            logger.error(f"Failed to get dashboard info: {e}")
            raise
    
    def close(self):
        """Clean up resources."""
        if self.db_connection:
            self.db_connection.close()
        logger.info("Dashboard generator resources cleaned up")
