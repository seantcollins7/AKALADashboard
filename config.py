"""
Configuration management for the AKALA Dashboard Generator.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables from akala-db.env
load_dotenv("akala-db.env")


class AWSConfig(BaseModel):
    """AWS configuration settings."""
    region: str = Field(default="us-east-1")
    access_key_id: Optional[str] = Field(default=None)
    secret_access_key: Optional[str] = Field(default=None)
    session_token: Optional[str] = Field(default=None)
    
    @classmethod
    def from_env(cls) -> "AWSConfig":
        """Load AWS config from environment variables."""
        return cls(
            region=os.getenv("AWS_REGION", "us-east-1"),
            access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            session_token=os.getenv("AWS_SESSION_TOKEN")
        )


class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    host: str
    port: int = Field(default=5432)
    database: str
    username: str
    password: str
    engine: str = Field(default="postgresql")  # postgresql, mysql, mssql
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load database config from environment variables."""
        return cls(
            host=os.getenv("DB_HOST", ""),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", ""),
            username=os.getenv("DB_USERNAME", ""),
            password=os.getenv("DB_PASSWORD", ""),
            engine=os.getenv("DB_ENGINE", "postgresql")
        )


class GoogleConfig(BaseModel):
    """Google Looker Studio configuration settings."""
    credentials_file: Optional[str] = Field(default=None)
    service_account_key: Optional[str] = Field(default=None)
    spreadsheet_id: Optional[str] = Field(default=None)
    folder_id: Optional[str] = Field(default=None)
    
    @classmethod
    def from_env(cls) -> "GoogleConfig":
        """Load Google config from environment variables."""
        return cls(
            credentials_file=os.getenv("GOOGLE_CREDENTIALS_FILE"),
            service_account_key=os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY"),
            spreadsheet_id=os.getenv("GOOGLE_SPREADSHEET_ID"),
            folder_id=os.getenv("GOOGLE_DRIVE_FOLDER_ID")
        )


class DashboardConfig(BaseModel):
    """Dashboard generator configuration."""
    aws: Optional[AWSConfig] = Field(default=None)
    database: DatabaseConfig
    google: Optional[GoogleConfig] = Field(default=None)
    log_level: str = Field(default="INFO")
    cache_timeout: int = Field(default=3600)  # seconds
    
    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Load complete configuration from environment variables."""
        # Only load AWS config if credentials are provided
        aws_config = None
        if os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("AWS_REGION"):
            aws_config = AWSConfig.from_env()
        
        # Only load Google config if credentials are provided
        google_config = None
        if (os.getenv("GOOGLE_CREDENTIALS_FILE") or os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")):
            google_config = GoogleConfig.from_env()
        
        return cls(
            aws=aws_config,
            database=DatabaseConfig.from_env(),
            google=google_config,
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            cache_timeout=int(os.getenv("CACHE_TIMEOUT", "3600"))
        )
