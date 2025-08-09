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


class PowerBIConfig(BaseModel):
    """Power BI configuration settings."""
    tenant_id: str
    client_id: str
    client_secret: str
    workspace_id: Optional[str] = Field(default=None)
    base_url: str = Field(default="https://api.powerbi.com/v1.0/myorg")
    
    @classmethod
    def from_env(cls) -> "PowerBIConfig":
        """Load Power BI config from environment variables."""
        return cls(
            tenant_id=os.getenv("POWERBI_TENANT_ID", ""),
            client_id=os.getenv("POWERBI_CLIENT_ID", ""),
            client_secret=os.getenv("POWERBI_CLIENT_SECRET", ""),
            workspace_id=os.getenv("POWERBI_WORKSPACE_ID"),
            base_url=os.getenv("POWERBI_BASE_URL", "https://api.powerbi.com/v1.0/myorg")
        )


class DashboardConfig(BaseModel):
    """Dashboard generator configuration."""
    aws: AWSConfig
    database: DatabaseConfig
    powerbi: PowerBIConfig
    log_level: str = Field(default="INFO")
    cache_timeout: int = Field(default=3600)  # seconds
    
    @classmethod
    def from_env(cls) -> "DashboardConfig":
        """Load complete configuration from environment variables."""
        return cls(
            aws=AWSConfig.from_env(),
            database=DatabaseConfig.from_env(),
            powerbi=PowerBIConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            cache_timeout=int(os.getenv("CACHE_TIMEOUT", "3600"))
        )
