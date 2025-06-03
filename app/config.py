import os
from pathlib import Path
from typing import Optional, List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings using Pydantic"""
    
    # Server configuration
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # OpenAI configuration
    openai_api_key: str = Field(default="your_openai_api_key_here", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    
    # LLM parameters
    llm_temperature: float = Field(default=0.3, env="LLM_TEMPERATURE")
    llm_max_tokens: Optional[int] = Field(default=500, env="LLM_MAX_TOKENS")
    
    @field_validator('llm_max_tokens', mode='before')
    @classmethod
    def validate_max_tokens(cls, v):
        if isinstance(v, str) and v.lower() in ('none', 'null', ''):
            return None
        return v
    
    # Processing configuration
    confidence_threshold: float = Field(default=0.7, env="CONFIDENCE_THRESHOLD")
    human_review_threshold: float = Field(default=0.5, env="HUMAN_REVIEW_THRESHOLD")
    background_processing_threshold: int = Field(default=50, env="BACKGROUND_PROCESSING_THRESHOLD")
    
    # Data paths
    data_dir: str = Field(default="data", env="DATA_DIR")
    
    # CORS settings
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignore extra environment variables
    }

# Global settings instance
settings = Settings()