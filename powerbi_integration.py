#!/usr/bin/env python3
"""
Power BI REST API Integration
Automatically creates and publishes Power BI dashboards without user interaction.
"""
import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from database.connection import DatabaseConnection
from config import DashboardConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PowerBIIntegration:
    """Power BI REST API integration for automatic dashboard creation."""
    
    def __init__(self, config: DashboardConfig):
        """Initialize Power BI integration."""
        self.config = config
        self.db_connection = DatabaseConnection(config.database)
        self.access_token = None
        self.workspace_id = None
        
        # Power BI API endpoints
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.auth_url = "https://login.microsoftonline.com/common/oauth2/token"
        
        # Load Power BI configuration
        self.load_powerbi_config()
        
    def load_powerbi_config(self):
        """Load Power BI configuration from environment."""
        self.client_id = os.getenv("POWERBI_CLIENT_ID")
        self.client_secret = os.getenv("POWERBI_CLIENT_SECRET")
        self.tenant_id = os.getenv("POWERBI_TENANT_ID")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        
        if not all([self.client_id, self.client_secret, self.tenant_id]):
            logger.warning("Power BI credentials not fully configured. Some features may not work.")
    
    def authenticate(self) -> bool:
        """Authenticate with Power BI service."""
        try:
            if not all([self.client_id, self.client_secret, self.tenant_id]):
                logger.error("Power BI credentials not configured")
                return False
            
            # Get access token
            token_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'resource': 'https://analysis.windows.net/powerbi/api'
            }
            
            response = requests.post(self.auth_url, data=token_data)
            response.raise_for_status()
            
            token_response = response.json()
            self.access_token = token_response['access_token']
            
            logger.info("Successfully authenticated with Power BI")
            return True
            
        except Exception as e:
            logger.error(f"Power BI authentication failed: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Power BI API requests."""
        if not self.access_token:
            raise Exception("Not authenticated with Power BI")
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def create_dataset(self, dataset_name: str, data: pd.DataFrame) -> Optional[str]:
        """Create a Power BI dataset."""
        try:
            if not self.authenticate():
                return None
            
            # Define dataset schema
            schema = self._create_dataset_schema(data)
            
            dataset_payload = {
                'name': dataset_name,
                'defaultMode': 'Push',
                'tables': [schema]
            }
            
            # Create dataset
            url = f"{self.base_url}/datasets"
            response = requests.post(url, headers=self.get_headers(), json=dataset_payload)
            response.raise_for_status()
            
            dataset_response = response.json()
            dataset_id = dataset_response['id']
            
            logger.info(f"Created Power BI dataset: {dataset_id}")
            return dataset_id
            
        except Exception as e:
            logger.error(f"Failed to create dataset: {e}")
            return None
    
    def _create_dataset_schema(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Create dataset schema from DataFrame."""
        columns = []
        
        for col_name, col_type in data.dtypes.items():
            if 'int' in str(col_type):
                data_type = 'Int64'
            elif 'float' in str(col_type):
                data_type = 'Double'
            elif 'datetime' in str(col_type):
                data_type = 'DateTime'
            else:
                data_type = 'String'
            
            columns.append({
                'name': col_name,
                'dataType': data_type
            })
        
        return {
            'name': 'DataTable',
            'columns': columns
        }
    
    def push_data_to_dataset(self, dataset_id: str, data: pd.DataFrame) -> bool:
        """Push data to an existing Power BI dataset."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return False
            
            # Convert DataFrame to rows
            rows = []
            for _, row in data.iterrows():
                row_dict = {}
                for col in data.columns:
                    value = row[col]
                    # Handle NaN values
                    if pd.isna(value):
                        value = None
                    row_dict[col] = value
                rows.append(row_dict)
            
            # Push data
            url = f"{self.base_url}/datasets/{dataset_id}/tables/DataTable/rows"
            payload = {'rows': rows}
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            logger.info(f"Pushed {len(rows)} rows to dataset {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push data: {e}")
            return False
    
    def create_report(self, dataset_id: str, report_name: str) -> Optional[str]:
        """Create a Power BI report from a dataset."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            # Create report
            url = f"{self.base_url}/reports"
            payload = {
                'name': report_name,
                'datasetId': dataset_id
            }
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            report_response = response.json()
            report_id = report_response['id']
            report_url = report_response['embedUrl']
            
            logger.info(f"Created Power BI report: {report_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return None
    
    def create_dashboard(self, report_id: str, dashboard_name: str) -> Optional[str]:
        """Create a Power BI dashboard from a report."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            # Create dashboard
            url = f"{self.base_url}/dashboards"
            payload = {
                'name': dashboard_name
            }
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            dashboard_response = response.json()
            dashboard_id = dashboard_response['id']
            
            # Add report to dashboard
            self._add_report_to_dashboard(dashboard_id, report_id)
            
            logger.info(f"Created Power BI dashboard: {dashboard_id}")
            return dashboard_id
            
        except Exception as e:
            logger.error(f"Failed to create dashboard: {e}")
            return None
    
    def _add_report_to_dashboard(self, dashboard_id: str, report_id: str) -> bool:
        """Add a report to a dashboard."""
        try:
            url = f"{self.base_url}/dashboards/{dashboard_id}/tiles"
            payload = {
                'reportId': report_id,
                'datasetId': report_id  # This will be updated with actual dataset ID
            }
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add report to dashboard: {e}")
            return False
    
    def get_dashboard_url(self, dashboard_id: str) -> Optional[str]:
        """Get the public URL for a dashboard."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            url = f"{self.base_url}/dashboards/{dashboard_id}"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            dashboard_info = response.json()
            return dashboard_info.get('embedUrl')
            
        except Exception as e:
            logger.error(f"Failed to get dashboard URL: {e}")
            return None
    
    def generate_automated_dashboard(self, dashboard_name: str, selected_metrics: List[str],
                                   selected_user: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Generate a complete Power BI dashboard automatically."""
        try:
            logger.info(f"Generating automated Power BI dashboard: {dashboard_name}")
            
            # Get data from database
            if selected_user is not None:
                user_data = self.db_connection.get_user_data({'user_id': selected_user.get('user_id')})
                analytics_data = self.db_connection.get_analytics_data({'user_id': selected_user.get('user_id')})
            else:
                user_data = self.db_connection.get_user_data({})
                analytics_data = self.db_connection.get_analytics_data({})
            
            # Create datasets
            user_dataset_id = None
            analytics_dataset_id = None
            
            if not user_data.empty:
                user_dataset_id = self.create_dataset(f"{dashboard_name}_Users", user_data)
                if user_dataset_id:
                    self.push_data_to_dataset(user_dataset_id, user_data)
            
            if not analytics_data.empty:
                analytics_dataset_id = self.create_dataset(f"{dashboard_name}_Analytics", analytics_data)
                if analytics_dataset_id:
                    self.push_data_to_dataset(analytics_dataset_id, analytics_data)
            
            # Create reports
            reports = {}
            if user_dataset_id:
                user_report_id = self.create_report(user_dataset_id, f"{dashboard_name}_Users_Report")
                if user_report_id:
                    reports['users'] = user_report_id
            
            if analytics_dataset_id:
                analytics_report_id = self.create_report(analytics_dataset_id, f"{dashboard_name}_Analytics_Report")
                if analytics_report_id:
                    reports['analytics'] = analytics_report_id
            
            # Create dashboard
            dashboard_id = None
            if reports:
                dashboard_id = self.create_dashboard(list(reports.values())[0], dashboard_name)
            
            # Get dashboard URL
            dashboard_url = None
            if dashboard_id:
                dashboard_url = self.get_dashboard_url(dashboard_id)
            
            result = {
                'success': True,
                'dashboard_name': dashboard_name,
                'dashboard_id': dashboard_id,
                'dashboard_url': dashboard_url,
                'datasets': {
                    'users': user_dataset_id,
                    'analytics': analytics_dataset_id
                },
                'reports': reports,
                'message': 'Dashboard generated successfully'
            }
            
            logger.info(f"Automated dashboard generation completed: {dashboard_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate automated dashboard: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Dashboard generation failed'
            }
    
    def list_workspaces(self) -> List[Dict[str, Any]]:
        """List available Power BI workspaces."""
        try:
            if not self.authenticate():
                return []
            
            url = f"{self.base_url}/groups"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            workspaces = response.json().get('value', [])
            return workspaces
            
        except Exception as e:
            logger.error(f"Failed to list workspaces: {e}")
            return []
    
    def test_connection(self) -> bool:
        """Test Power BI connection."""
        try:
            if not self.authenticate():
                return False
            
            # Try to list workspaces
            workspaces = self.list_workspaces()
            if workspaces:
                logger.info(f"Power BI connection successful. Found {len(workspaces)} workspaces.")
                return True
            else:
                logger.warning("Power BI connection successful but no workspaces found.")
                return True
                
        except Exception as e:
            logger.error(f"Power BI connection test failed: {e}")
            return False

def main():
    """Test Power BI integration."""
    try:
        # Load configuration
        load_dotenv("akala-db.env")
        config = DashboardConfig.from_env()
        
        # Create Power BI integration
        powerbi = PowerBIIntegration(config)
        
        # Test connection
        if powerbi.test_connection():
            print("✅ Power BI connection successful!")
            
            # List workspaces
            workspaces = powerbi.list_workspaces()
            if workspaces:
                print(f"\n📁 Available workspaces:")
                for workspace in workspaces:
                    print(f"   • {workspace.get('name', 'Unknown')} (ID: {workspace.get('id', 'N/A')})")
            else:
                print("\n⚠️  No workspaces found. You may need to create one in Power BI.")
        else:
            print("❌ Power BI connection failed!")
            print("\n💡 To set up Power BI integration:")
            print("1. Create a Power BI Pro account")
            print("2. Register an Azure AD application")
            print("3. Set environment variables:")
            print("   POWERBI_CLIENT_ID=your_client_id")
            print("   POWERBI_CLIENT_SECRET=your_client_secret")
            print("   POWERBI_TENANT_ID=your_tenant_id")
            print("   POWERBI_WORKSPACE_ID=your_workspace_id")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
