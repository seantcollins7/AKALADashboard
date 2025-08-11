"""
Configuration management for the AKALA Dashboard Generator.
"""
import os
from typing import Optional

# Optional pydantic import with dataclass fallback for restricted environments
try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
    USE_PYDANTIC = True
except ImportError:  # Fallback to dataclasses to avoid hard dep in minimal envs
    _PydanticBaseModel = object
    def _PydanticField(*args, **kwargs):  # type: ignore
        # simple passthrough to support both default and default_factory signatures
        return kwargs.get("default", None)
    USE_PYDANTIC = False

# Optional dotenv import; fall back to no-op if unavailable
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False

# Load environment variables from akala-db.env
load_dotenv("akala-db.env")

# Configure a decorator that is a no-op when using pydantic, or @dataclass when not
if USE_PYDANTIC:
    def _dataclass_decorator(cls):  # no-op so pydantic BaseModel behavior remains
        return cls
    BaseModel = _PydanticBaseModel
    Field = _PydanticField
else:
    from dataclasses import dataclass as _dataclass, field as _dataclass_field
    def _dataclass_decorator(cls):
        return _dataclass(cls)
    class BaseModel:  # Minimal shim to satisfy type references
        pass
    def Field(*, default=None, default_factory=None):  # type: ignore
        if default_factory is not None:
            return _dataclass_field(default_factory=default_factory)
        return _dataclass_field(default=default)


@_dataclass_decorator
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


@_dataclass_decorator
class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    host: str = Field(default="")
    port: int = Field(default=5432)
    database: str = Field(default="")
    username: str = Field(default="")
    password: str = Field(default="")
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


@_dataclass_decorator
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


# Define DashboardConfig differently depending on dependency availability
if USE_PYDANTIC:
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
else:
    @_dataclass_decorator
    class DashboardConfig(BaseModel):
        """Dashboard generator configuration."""
        aws: Optional[AWSConfig] = Field(default=None)
        database: DatabaseConfig = Field(default_factory=DatabaseConfig)
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
