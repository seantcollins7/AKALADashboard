"""
Power BI REST API client for dashboard integration.
"""
import logging
from typing import Dict, Any, List, Optional, Union
import requests
import json
from datetime import datetime, timedelta
from msal import ConfidentialClientApplication
import pandas as pd

from config import PowerBIConfig

logger = logging.getLogger(__name__)


class PowerBIClient:
    """Power BI REST API client for managing datasets, reports, and dashboards."""
    
    def __init__(self, config: PowerBIConfig):
        """
        Initialize Power BI client.
        
        Args:
            config: Power BI configuration
        """
        self.config = config
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._msal_app = ConfidentialClientApplication(
            client_id=config.client_id,
            client_credential=config.client_secret,
            authority=f"https://login.microsoftonline.com/{config.tenant_id}"
        )
        
    def _get_access_token(self) -> str:
        """
        Get or refresh access token for Power BI API.
        
        Returns:
            Valid access token
        """
        # Check if current token is still valid
        if (self._access_token and self._token_expires_at and 
            datetime.now() < self._token_expires_at - timedelta(minutes=5)):
            return self._access_token
        
        # Request new token
        scopes = ["https://analysis.windows.net/powerbi/api/.default"]
        
        try:
            result = self._msal_app.acquire_token_for_client(scopes=scopes)
            
            if "access_token" in result:
                self._access_token = result["access_token"]
                # Token typically expires in 1 hour
                self._token_expires_at = datetime.now() + timedelta(seconds=result.get("expires_in", 3600))
                logger.info("Successfully acquired Power BI access token")
                return self._access_token
            else:
                error_msg = result.get("error_description", "Unknown error")
                logger.error(f"Failed to acquire token: {error_msg}")
                raise Exception(f"Authentication failed: {error_msg}")
                
        except Exception as e:
            logger.error(f"Token acquisition failed: {e}")
            raise
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make authenticated request to Power BI API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base URL)
            data: Request payload
            
        Returns:
            Response data
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {}
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
    
    def get_workspaces(self) -> List[Dict[str, Any]]:
        """
        Get list of available workspaces.
        
        Returns:
            List of workspace information
        """
        response = self._make_request("GET", "groups")
        return response.get("value", [])
    
    def get_datasets(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get datasets in workspace.
        
        Args:
            workspace_id: Workspace ID (uses default if not provided)
            
        Returns:
            List of dataset information
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = "datasets"
        else:
            endpoint = f"groups/{workspace_id}/datasets"
        
        response = self._make_request("GET", endpoint)
        return response.get("value", [])
    
    def create_dataset(self, dataset_definition: Dict[str, Any], workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new dataset in Power BI.
        
        Args:
            dataset_definition: Dataset definition following Power BI schema
            workspace_id: Workspace ID (uses default if not provided)
            
        Returns:
            Created dataset information
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = "datasets"
        else:
            endpoint = f"groups/{workspace_id}/datasets"
        
        return self._make_request("POST", endpoint, dataset_definition)
    
    def push_data_to_dataset(self, dataset_id: str, table_name: str, data: pd.DataFrame, 
                           workspace_id: Optional[str] = None) -> None:
        """
        Push data to an existing dataset table.
        
        Args:
            dataset_id: Dataset ID
            table_name: Table name in the dataset
            data: Data to push as pandas DataFrame
            workspace_id: Workspace ID (uses default if not provided)
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = f"datasets/{dataset_id}/tables/{table_name}/rows"
        else:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows"
        
        # Convert DataFrame to required format
        rows_data = {"rows": data.to_dict('records')}
        
        self._make_request("POST", endpoint, rows_data)
        logger.info(f"Successfully pushed {len(data)} rows to dataset {dataset_id}, table {table_name}")
    
    def delete_dataset_rows(self, dataset_id: str, table_name: str, workspace_id: Optional[str] = None) -> None:
        """
        Delete all rows from a dataset table.
        
        Args:
            dataset_id: Dataset ID
            table_name: Table name in the dataset
            workspace_id: Workspace ID (uses default if not provided)
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = f"datasets/{dataset_id}/tables/{table_name}/rows"
        else:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/tables/{table_name}/rows"
        
        self._make_request("DELETE", endpoint)
        logger.info(f"Successfully deleted rows from dataset {dataset_id}, table {table_name}")
    
    def get_reports(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get reports in workspace.
        
        Args:
            workspace_id: Workspace ID (uses default if not provided)
            
        Returns:
            List of report information
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = "reports"
        else:
            endpoint = f"groups/{workspace_id}/reports"
        
        response = self._make_request("GET", endpoint)
        return response.get("value", [])
    
    def get_dashboards(self, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get dashboards in workspace.
        
        Args:
            workspace_id: Workspace ID (uses default if not provided)
            
        Returns:
            List of dashboard information
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = "dashboards"
        else:
            endpoint = f"groups/{workspace_id}/dashboards"
        
        response = self._make_request("GET", endpoint)
        return response.get("value", [])
    
    def refresh_dataset(self, dataset_id: str, workspace_id: Optional[str] = None) -> None:
        """
        Trigger dataset refresh.
        
        Args:
            dataset_id: Dataset ID to refresh
            workspace_id: Workspace ID (uses default if not provided)
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = f"datasets/{dataset_id}/refreshes"
        else:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        
        self._make_request("POST", endpoint, {})
        logger.info(f"Successfully triggered refresh for dataset {dataset_id}")
    
    def get_dataset_refresh_history(self, dataset_id: str, workspace_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get dataset refresh history.
        
        Args:
            dataset_id: Dataset ID
            workspace_id: Workspace ID (uses default if not provided)
            
        Returns:
            List of refresh history records
        """
        workspace_id = workspace_id or self.config.workspace_id
        if not workspace_id:
            endpoint = f"datasets/{dataset_id}/refreshes"
        else:
            endpoint = f"groups/{workspace_id}/datasets/{dataset_id}/refreshes"
        
        response = self._make_request("GET", endpoint)
        return response.get("value", [])


def create_dataset_schema(table_name: str, columns: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Create Power BI dataset schema definition.
    
    Args:
        table_name: Name of the table
        columns: List of column definitions with 'name' and 'dataType'
        
    Returns:
        Dataset schema definition
    """
    return {
        "name": f"Dashboard_{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "tables": [
            {
                "name": table_name,
                "columns": columns
            }
        ]
    }
