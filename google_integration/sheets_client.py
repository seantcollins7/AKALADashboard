"""
Google Sheets client for dashboard data export and Looker Studio integration.
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from datetime import datetime

# Optional Google imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    HAS_GOOGLE = True
except ImportError:
    HAS_GOOGLE = False

from config import GoogleConfig

logger = logging.getLogger(__name__)


class GoogleSheetsClient:
    """Google Sheets client for exporting dashboard data and connecting to Looker Studio."""
    
    def __init__(self, config: GoogleConfig):
        """
        Initialize Google Sheets client.
        
        Args:
            config: Google configuration
        """
        if not HAS_GOOGLE:
            raise ImportError(
                "Google client libraries not installed. "
                "Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client"
            )
        
        self.config = config
        self.credentials = None
        self.service = None
        self._initialize_credentials()
        
    def _initialize_credentials(self):
        """Initialize Google API credentials."""
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        try:
            if self.config.credentials_file and os.path.exists(self.config.credentials_file):
                # Use service account file
                self.credentials = service_account.Credentials.from_service_account_file(
                    self.config.credentials_file, 
                    scopes=scopes
                )
                logger.info("Loaded credentials from service account file")
                
            elif self.config.service_account_key:
                # Use service account key string
                key_data = json.loads(self.config.service_account_key)
                self.credentials = service_account.Credentials.from_service_account_info(
                    key_data, 
                    scopes=scopes
                )
                logger.info("Loaded credentials from service account key")
                
            else:
                raise ValueError("No Google credentials provided")
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            
        except Exception as e:
            logger.error(f"Failed to initialize Google credentials: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Test Google Sheets API connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to access the service
            self.service.spreadsheets().get(spreadsheetId='test').execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                # 404 is expected for test spreadsheet, means API is working
                logger.info("Google Sheets API connection successful")
                return True
            else:
                logger.error(f"Google Sheets API connection failed: {e}")
                return False
        except Exception as e:
            logger.error(f"Google Sheets API connection test failed: {e}")
            return False
    
    def create_spreadsheet(self, title: str, folder_id: Optional[str] = None) -> str:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Spreadsheet title
            folder_id: Optional Google Drive folder ID
            
        Returns:
            Spreadsheet ID
        """
        try:
            spreadsheet_body = {
                'properties': {
                    'title': title
                }
            }
            
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            logger.info(f"Created spreadsheet '{title}' with ID: {spreadsheet_id}")
            
            # Move to folder if specified
            if folder_id:
                self._move_to_folder(spreadsheet_id, folder_id)
            
            return spreadsheet_id
            
        except Exception as e:
            logger.error(f"Failed to create spreadsheet: {e}")
            raise
    
    def _move_to_folder(self, file_id: str, folder_id: str):
        """Move a file to a specific Google Drive folder."""
        try:
            # Get current parents
            file = self.drive_service.files().get(fileId=file_id, fields='parents').execute()
            previous_parents = ",".join(file.get('parents'))
            
            # Move to new folder
            self.drive_service.files().update(
                fileId=file_id,
                addParents=folder_id,
                removeParents=previous_parents,
                fields='id, parents'
            ).execute()
            
            logger.info(f"Moved file to folder {folder_id}")
            
        except Exception as e:
            logger.warning(f"Failed to move file to folder: {e}")
    
    def write_dataframe_to_sheet(self, spreadsheet_id: str, sheet_name: str, 
                                df: pd.DataFrame, clear_existing: bool = True) -> None:
        """
        Write pandas DataFrame to Google Sheets.
        
        Args:
            spreadsheet_id: Target spreadsheet ID
            sheet_name: Sheet name
            df: DataFrame to write
            clear_existing: Whether to clear existing data
        """
        try:
            # Ensure sheet exists
            self._ensure_sheet_exists(spreadsheet_id, sheet_name)
            
            # Clear existing data if requested
            if clear_existing:
                self._clear_sheet(spreadsheet_id, sheet_name)
            
            # Prepare data
            # Include headers
            values = [df.columns.tolist()] + df.fillna('').values.tolist()
            
            # Convert any datetime objects to strings
            for row in values:
                for i, cell in enumerate(row):
                    if pd.isna(cell):
                        row[i] = ''
                    elif isinstance(cell, (pd.Timestamp, datetime)):
                        row[i] = cell.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        row[i] = str(cell)
            
            # Write to sheet
            range_name = f"{sheet_name}!A1"
            body = {
                'values': values
            }
            
            self.service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Successfully wrote {len(df)} rows to sheet '{sheet_name}'")
            
        except Exception as e:
            logger.error(f"Failed to write DataFrame to sheet: {e}")
            raise
    
    def _ensure_sheet_exists(self, spreadsheet_id: str, sheet_name: str):
        """Ensure a sheet with the given name exists."""
        try:
            # Get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            # Check if sheet exists
            sheet_names = [sheet['properties']['title'] for sheet in spreadsheet['sheets']]
            
            if sheet_name not in sheet_names:
                # Create the sheet
                request_body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                }
                
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body=request_body
                ).execute()
                
                logger.info(f"Created sheet '{sheet_name}'")
                
        except Exception as e:
            logger.error(f"Failed to ensure sheet exists: {e}")
            raise
    
    def _clear_sheet(self, spreadsheet_id: str, sheet_name: str):
        """Clear all data from a sheet."""
        try:
            range_name = f"{sheet_name}!A:ZZ"
            self.service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            logger.info(f"Cleared sheet '{sheet_name}'")
            
        except Exception as e:
            logger.error(f"Failed to clear sheet: {e}")
            raise
    
    def create_dashboard_spreadsheet(self, dashboard_name: str) -> str:
        """
        Create a complete dashboard spreadsheet with multiple sheets.
        
        Args:
            dashboard_name: Name for the dashboard
            
        Returns:
            Spreadsheet ID
        """
        try:
            # Create main spreadsheet
            title = f"Dashboard - {dashboard_name} - {datetime.now().strftime('%Y-%m-%d')}"
            spreadsheet_id = self.create_spreadsheet(
                title, 
                folder_id=self.config.folder_id
            )
            
            # Create additional sheets for different data types
            sheet_names = ['Users', 'Analytics', 'Summary']
            
            for sheet_name in sheet_names[1:]:  # Skip first one (already exists as 'Sheet1')
                self._ensure_sheet_exists(spreadsheet_id, sheet_name)
            
            # Rename the default sheet
            self._rename_sheet(spreadsheet_id, 'Sheet1', 'Users')
            
            logger.info(f"Created dashboard spreadsheet with {len(sheet_names)} sheets")
            return spreadsheet_id
            
        except Exception as e:
            logger.error(f"Failed to create dashboard spreadsheet: {e}")
            raise
    
    def _rename_sheet(self, spreadsheet_id: str, old_name: str, new_name: str):
        """Rename a sheet."""
        try:
            # Get sheet ID
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=spreadsheet_id
            ).execute()
            
            sheet_id = None
            for sheet in spreadsheet['sheets']:
                if sheet['properties']['title'] == old_name:
                    sheet_id = sheet['properties']['sheetId']
                    break
            
            if sheet_id is None:
                logger.warning(f"Sheet '{old_name}' not found")
                return
            
            # Rename the sheet
            request_body = {
                'requests': [{
                    'updateSheetProperties': {
                        'properties': {
                            'sheetId': sheet_id,
                            'title': new_name
                        },
                        'fields': 'title'
                    }
                }]
            }
            
            self.service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=request_body
            ).execute()
            
            logger.info(f"Renamed sheet '{old_name}' to '{new_name}'")
            
        except Exception as e:
            logger.error(f"Failed to rename sheet: {e}")
    
    def get_spreadsheet_url(self, spreadsheet_id: str) -> str:
        """Get the public URL for a spreadsheet."""
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
    
    def share_spreadsheet(self, spreadsheet_id: str, email: str, role: str = 'reader') -> None:
        """
        Share spreadsheet with an email address.
        
        Args:
            spreadsheet_id: Spreadsheet ID
            email: Email address to share with
            role: Permission role ('reader', 'writer', 'commenter')
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission
            ).execute()
            
            logger.info(f"Shared spreadsheet with {email} as {role}")
            
        except Exception as e:
            logger.error(f"Failed to share spreadsheet: {e}")
            raise
    
    def make_public_viewable(self, spreadsheet_id: str) -> None:
        """Make spreadsheet viewable by anyone with the link."""
        try:
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            
            self.drive_service.permissions().create(
                fileId=spreadsheet_id,
                body=permission
            ).execute()
            
            logger.info("Made spreadsheet publicly viewable")
            
        except Exception as e:
            logger.error(f"Failed to make spreadsheet public: {e}")
            raise


def prepare_dataframe_for_looker_studio(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for optimal Looker Studio integration.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Processed DataFrame
    """
    df_clean = df.copy()
    
    # Handle datetime columns - convert to strings in ISO format
    for col in df_clean.columns:
        if df_clean[col].dtype == 'datetime64[ns]':
            df_clean[col] = df_clean[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        elif df_clean[col].dtype == 'timedelta64[ns]':
            df_clean[col] = df_clean[col].astype(str)
    
    # Replace NaN values with empty strings
    df_clean = df_clean.fillna('')
    
    # Ensure column names are Looker Studio friendly (no special characters)
    df_clean.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_') 
                       for col in df_clean.columns]
    
    return df_clean
