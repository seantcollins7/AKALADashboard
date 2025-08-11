#!/usr/bin/env python3
"""
Power BI Embedded Integration
Low-cost, professional dashboards using Power BI Embedded service.
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

class PowerBIEmbedded:
    """Power BI Embedded integration for low-cost, professional dashboards."""
    
    def __init__(self, config: DashboardConfig):
        """Initialize Power BI Embedded integration."""
        self.config = config
        self.db_connection = DatabaseConnection(config.database)
        self.access_token = None
        
        # Azure/Power BI Embedded endpoints
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.workspace_id = os.getenv("POWERBI_WORKSPACE_ID")
        self.capacity_id = os.getenv("POWERBI_CAPACITY_ID")
        
        # Power BI API endpoints
        self.base_url = "https://api.powerbi.com/v1.0/myorg"
        self.auth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/token"
        
    def authenticate(self) -> bool:
        """Authenticate with Azure AD."""
        try:
            if not all([self.tenant_id, self.client_id, self.client_secret]):
                logger.error("Azure credentials not configured")
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
            
            logger.info("Successfully authenticated with Azure AD")
            return True
            
        except Exception as e:
            logger.error(f"Azure authentication failed: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers for Power BI API requests."""
        if not self.access_token:
            raise Exception("Not authenticated with Azure AD")
        
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    def create_embedded_workspace(self, workspace_name: str) -> Optional[str]:
        """Create a new Power BI workspace for embedded dashboards."""
        try:
            if not self.authenticate():
                return None
            
            # Create workspace
            url = f"{self.base_url}/groups"
            payload = {
                'name': workspace_name,
                'isOnDedicatedCapacity': True,
                'capacityId': self.capacity_id
            }
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            workspace_response = response.json()
            workspace_id = workspace_response['id']
            
            logger.info(f"Created embedded workspace: {workspace_id}")
            return workspace_id
            
        except Exception as e:
            logger.error(f"Failed to create workspace: {e}")
            return None
    
    def create_dataset(self, workspace_id: str, dataset_name: str, data: pd.DataFrame) -> Optional[str]:
        """Create a Power BI dataset in the specified workspace."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            # Define dataset schema
            schema = self._create_dataset_schema(data)
            
            dataset_payload = {
                'name': dataset_name,
                'defaultMode': 'Push',
                'tables': [schema]
            }
            
            # Create dataset in workspace
            url = f"{self.base_url}/groups/{workspace_id}/datasets"
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            dataset_response = response.json()
            dataset_id = dataset_response['id']
            
            logger.info(f"Created dataset in workspace: {dataset_id}")
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
    
    def push_data_to_dataset(self, workspace_id: str, dataset_id: str, data: pd.DataFrame) -> bool:
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
            url = f"{self.base_url}/groups/{workspace_id}/datasets/{dataset_id}/tables/DataTable/rows"
            payload = {'rows': rows}
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            logger.info(f"Pushed {len(rows)} rows to dataset {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to push data: {e}")
            return False
    
    def create_report(self, workspace_id: str, dataset_id: str, report_name: str) -> Optional[str]:
        """Create a Power BI report from a dataset."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            # Create report in workspace
            url = f"{self.base_url}/groups/{workspace_id}/reports"
            payload = {
                'name': report_name,
                'datasetId': dataset_id
            }
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            report_response = response.json()
            report_id = report_response['id']
            report_url = report_response['embedUrl']
            
            logger.info(f"Created report in workspace: {report_id}")
            return report_id
            
        except Exception as e:
            logger.error(f"Failed to create report: {e}")
            return None
    
    def generate_embed_token(self, workspace_id: str, report_id: str, user_email: str = None) -> Optional[str]:
        """Generate an embed token for a report."""
        try:
            if not self.access_token:
                if not self.authenticate():
                    return None
            
            # Generate embed token
            url = f"{self.base_url}/groups/{workspace_id}/reports/{report_id}/GenerateToken"
            
            payload = {
                'accessLevel': 'View',
                'allowEdit': False,
                'identities': []
            }
            
            if user_email:
                payload['identities'].append({
                    'username': user_email,
                    'roles': ['Viewer'],
                    'datasets': ['*']
                })
            
            response = requests.post(url, headers=self.get_headers(), json=payload)
            response.raise_for_status()
            
            token_response = response.json()
            embed_token = token_response['token']
            
            logger.info(f"Generated embed token for report {report_id}")
            return embed_token
            
        except Exception as e:
            logger.error(f"Failed to generate embed token: {e}")
            return None
    
    def create_embedded_dashboard(self, dashboard_name: str, selected_metrics: List[str],
                                 selected_user: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Create a complete embedded Power BI dashboard."""
        try:
            logger.info(f"Creating embedded Power BI dashboard: {dashboard_name}")
            
            # Create workspace
            workspace_name = f"{dashboard_name}_Workspace_{datetime.now().strftime('%Y%m%d')}"
            workspace_id = self.create_embedded_workspace(workspace_name)
            
            if not workspace_id:
                return {
                    'success': False,
                    'error': 'Failed to create workspace',
                    'message': 'Workspace creation failed'
                }
            
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
                user_dataset_id = self.create_dataset(workspace_id, f"{dashboard_name}_Users", user_data)
                if user_dataset_id:
                    self.push_data_to_dataset(workspace_id, user_dataset_id, user_data)
            
            if not analytics_data.empty:
                analytics_dataset_id = self.create_dataset(workspace_id, f"{dashboard_name}_Analytics", analytics_data)
                if analytics_dataset_id:
                    self.push_data_to_dataset(workspace_id, analytics_dataset_id, analytics_data)
            
            # Create reports
            reports = {}
            if user_dataset_id:
                user_report_id = self.create_report(workspace_id, user_dataset_id, f"{dashboard_name}_Users_Report")
                if user_report_id:
                    reports['users'] = user_report_id
            
            if analytics_dataset_id:
                analytics_report_id = self.create_report(workspace_id, analytics_dataset_id, f"{dashboard_name}_Analytics_Report")
                if analytics_report_id:
                    reports['analytics'] = analytics_report_id
            
            # Generate embed tokens
            embed_tokens = {}
            for report_type, report_id in reports.items():
                user_email = selected_user.get('email') if selected_user else None
                embed_token = self.generate_embed_token(workspace_id, report_id, user_email)
                if embed_token:
                    embed_tokens[report_type] = embed_token
            
            result = {
                'success': True,
                'dashboard_name': dashboard_name,
                'workspace_id': workspace_id,
                'workspace_name': workspace_name,
                'datasets': {
                    'users': user_dataset_id,
                    'analytics': analytics_dataset_id
                },
                'reports': reports,
                'embed_tokens': embed_tokens,
                'embed_urls': {
                    'users': f"https://app.powerbi.com/reportEmbed?reportId={reports.get('users')}&groupId={workspace_id}",
                    'analytics': f"https://app.powerbi.com/reportEmbed?reportId={reports.get('analytics')}&groupId={workspace_id}"
                },
                'message': 'Embedded dashboard created successfully'
            }
            
            logger.info(f"Embedded dashboard creation completed: {workspace_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create embedded dashboard: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Embedded dashboard creation failed'
            }
    
    def get_cost_estimate(self, user_count: int) -> Dict[str, Any]:
        """Get cost estimate for Power BI Embedded."""
        # Power BI Embedded pricing (approximate)
        # A1: $0.50/hour, A2: $1.00/hour, A3: $2.00/hour, A4: $4.00/hour
        # Most dashboards use A1 or A2 tier
        
        a1_monthly = 0.50 * 24 * 30  # $0.50/hour * 24 hours * 30 days
        a2_monthly = 1.00 * 24 * 30  # $1.00/hour * 24 hours * 30 days
        
        return {
            'tier_a1': {
                'name': 'A1 (Basic)',
                'monthly_cost': a1_monthly,
                'cost_per_user': a1_monthly / user_count if user_count > 0 else 0,
                'description': 'Suitable for small teams, basic dashboards'
            },
            'tier_a2': {
                'name': 'A2 (Standard)',
                'monthly_cost': a2_monthly,
                'cost_per_user': a2_monthly / user_count if user_count > 0 else 0,
                'description': 'Suitable for medium teams, interactive dashboards'
            },
            'recommendation': 'A1 for most use cases, A2 for high-traffic dashboards'
        }
    
    def test_connection(self) -> bool:
        """Test Power BI Embedded connection."""
        try:
            if not self.authenticate():
                return False
            
            # Try to list workspaces
            url = f"{self.base_url}/groups"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            
            workspaces = response.json().get('value', [])
            logger.info(f"Power BI Embedded connection successful. Found {len(workspaces)} workspaces.")
            return True
                
        except Exception as e:
            logger.error(f"Power BI Embedded connection test failed: {e}")
            return False

def main():
    """Test Power BI Embedded integration."""
    try:
        # Load configuration
        load_dotenv("akala-db.env")
        config = DashboardConfig.from_env()
        
        # Create Power BI Embedded integration
        powerbi = PowerBIEmbedded(config)
        
        # Test connection
        if powerbi.test_connection():
            print("✅ Power BI Embedded connection successful!")
            
            # Show cost estimates
            print("\n💰 Cost Estimates (Power BI Embedded):")
            cost_estimate = powerbi.get_cost_estimate(100)  # 100 users
            
            print(f"   A1 Tier: ${cost_estimate['tier_a1']['monthly_cost']:.2f}/month")
            print(f"   A2 Tier: ${cost_estimate['tier_a2']['monthly_cost']:.2f}/month")
            print(f"   Cost per user (A1): ${cost_estimate['tier_a1']['cost_per_user']:.2f}/month")
            print(f"   Cost per user (A2): ${cost_estimate['tier_a2']['cost_per_user']:.2f}/month")
            
            print(f"\n💡 Recommendation: {cost_estimate['recommendation']}")
            
        else:
            print("❌ Power BI Embedded connection failed!")
            print("\n💡 To set up Power BI Embedded:")
            print("1. Create Azure subscription")
            print("2. Set up Power BI Embedded capacity")
            print("3. Register Azure AD application")
            print("4. Set environment variables:")
            print("   AZURE_TENANT_ID=your_tenant_id")
            print("   AZURE_CLIENT_ID=your_client_id")
            print("   AZURE_CLIENT_SECRET=your_client_secret")
            print("   POWERBI_WORKSPACE_ID=your_workspace_id")
            print("   POWERBI_CAPACITY_ID=your_capacity_id")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
