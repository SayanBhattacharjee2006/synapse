from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, model_validator

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

    SECRET_KEY:str | None = None
    ALGORITHM:str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 30

    #vector store
    QDRANT_URL:str
    QDRANT_CONVERSATIONS_COLLECTION:str
    QDRANT_SUMMARIES_COLLECTION:str
    QDRANT_DOCUMENTS_COLLECTION:str

    # S3 bucket keys 
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str
    AWS_S3_BUCKET_NAME: str
    MAX_FILE_SIZE: int
    CHUNK_SIZE: int

    # RAG
    
    RAG_CHUNK_SIZE:int
    RAG_OVERLAP:int

    # Taviily
    TAVILY_API_KEY:str

    @model_validator(mode="after")
    def validate_auth_settings(self):
        if self.SECRET_KEY:
            return self

        if self.APP_ENV.lower() in {"production", "prod"}:
            raise ValueError("SECRET_KEY must be set in production")

        self.SECRET_KEY = "dev-only-insecure-secret-key-change-me"
        return self


    model_config= SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
    )

settings = Settings()
