#!/usr/bin/env python3
"""
Configuration management for AKALA Dashboard Generator.
"""
import os
from typing import Optional
from pydantic import BaseModel, Field

class DatabaseConfig(BaseModel):
    """Database configuration settings."""
    host: str
    port: int
    database: str
    username: str
    password: str
    engine: str

class PowerBIConfig(BaseModel):
    """Power BI configuration settings."""
    output_directory: str = "dashboards"
    template_theme: str = "professional"
    auto_refresh: bool = True
    export_formats: list = ["pdf", "png"]
    
class GeminiConfig(BaseModel):
    api_key: str
    model: str = "gemini-pro"
    max_tokens: int = 1000
    temperature: float = 0.7

class DashboardConfig(BaseModel):
    """Main dashboard configuration."""
    database: DatabaseConfig
    powerbi: Optional[PowerBIConfig] = None
    gemini: GeminiConfig
    
    @classmethod
    def from_env(cls):
        """Create configuration from environment variables."""
        return cls(
            database=DatabaseConfig(
                host=os.getenv("DB_HOST", ""),
                port=int(os.getenv("DB_PORT", "5432")),
                database=os.getenv("DB_NAME", ""),
                username=os.getenv("DB_USERNAME", ""),
                password=os.getenv("DB_PASSWORD", ""),
                engine=os.getenv("DB_ENGINE", "postgresql")
            ),
            powerbi=PowerBIConfig(
                output_directory=os.getenv("POWERBI_OUTPUT_DIR", "dashboards"),
                template_theme=os.getenv("POWERBI_THEME", "professional"),
                auto_refresh=os.getenv("POWERBI_AUTO_REFRESH", "true").lower() == "true",
                export_formats=os.getenv("POWERBI_EXPORT_FORMATS", "pdf,png").split(",")
            ), 
            gemini=GeminiConfig(
                api_key=os.getenv("GEMINI_API_KEY", ""), 
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", 1000)),
                temperature=float(os.getenv("GEMINI_TEMPERATURE", 0.7))
            )
        )
