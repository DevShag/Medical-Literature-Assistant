import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Medical Literature Assistant RAG"

    # OpenAI config
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = "gpt-4o-mini"
    EMBEDDING_MODEL: str = 'text-embedding-3-small'


    # Qdrant config
    QDRANT_PATH: str = os.getenv("QDRANT_PATH", "qdrant_db")
    QDRANT_HOST: str = 'localhost'
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION_NAME: str = 'medical_literature'

    
    # RAG Settings
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP : int = 200
    TOP_K: int = 5

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()