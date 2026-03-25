"""
Configuration module for the application
"""

from pydantic_settings import BaseSettings
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent if BASE_DIR.name == "backend" else BASE_DIR


class Settings(BaseSettings):
    """Application settings"""
    
    # Groq API
    groq_api_key: str
    
    # Application
    app_name: str = "Order-to-Cash Graph AI"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Graph
    graph_path: str = str(PROJECT_ROOT / "dataset" / "processed_data" / "graph.gpickle")
    
    class Config:
        env_file = str(PROJECT_ROOT / ".env")
        case_sensitive = False


settings = Settings()
