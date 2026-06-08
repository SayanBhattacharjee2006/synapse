from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
  
    # Database   
    POSTGRES_USER:str
    POSTGRES_PASSWORD:str
    POSTGRES_DB:str
    POSTGRES_HOST:str
    POSTGRES_PORT:int
    DATABASE_URL:PostgresDsn

    # LangSmith
    LANGCHAIN_TRACING_V2:bool
    LANGCHAIN_ENDPOINT:str
    LANGCHAIN_API_KEY:str
    LANGCHAIN_PROJECT:str

    # LLM
    OPENAI_API_KEY:str

    # App
    APP_ENV:str
    APP_HOST:str
    APP_PORT:int

    TEST_DATABASE_URL:PostgresDsn

    SECRET_KEY:str
    ALGORITHM:str
    ACCESS_TOKEN_EXPIRE_MINUTES:int

    VITE_API_BASE_URL:str

    model_config= SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
    )

settings = Settings()