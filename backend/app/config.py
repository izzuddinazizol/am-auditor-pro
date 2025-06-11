from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # API Keys
    gemini_api_key: str = ""
    openai_api_key: str = ""
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/am_auditor_pro"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Application Settings
    environment: str = "development"
    debug: bool = True
    secret_key: str = "your-secret-key-change-in-production"
    
    # File Upload Settings
    max_file_size_mb: int = 100
    allowed_extensions: str = "mp3,wav,mp4,avi,mov,pdf,docx,txt,png,jpg,jpeg"
    upload_dir: str = "uploads"
    temp_dir: str = "temp"
    
    # Processing Settings
    default_language: str = "en"
    supported_languages: str = "en,ms,zh,zh-hk"
    
    # Paths
    docs_dir: str = "../docs"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def allowed_extensions_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [ext.strip() for ext in self.allowed_extensions.split(",")]
    
    @property
    def supported_languages_list(self) -> List[str]:
        """Convert comma-separated string to list"""
        return [lang.strip() for lang in self.supported_languages.split(",")]


# Global settings instance
settings = Settings()

# Ensure upload and temp directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.temp_dir, exist_ok=True) 