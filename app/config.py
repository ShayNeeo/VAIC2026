import os
from pydantic import BaseModel

class Settings(BaseModel):
    # API Keys (Sẽ đọc từ Environment Variables)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    
    # Model Configurations
    DEFAULT_LLM: str = os.getenv("DEFAULT_LLM", "openai")  # openai | google | ollama
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    GOOGLE_MODEL: str = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    # Vector DB settings
    VECTOR_DB_DIR: str = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
    
    # App Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    APPROVAL_SECRET: str = os.getenv("APPROVAL_SECRET", "demo-only-change-me")
    APPROVAL_TOKEN_TTL_SECONDS: int = int(os.getenv("APPROVAL_TOKEN_TTL_SECONDS", 300))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
