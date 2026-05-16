from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # application
    app_name: str = "AI Data Analyst"
    app_version: str = "0.1.0"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False

    # LLM ( Groq, OpenAI-compatible )
    groq_api_key: str
    llm_model: str = "llama-3.3-70-versatile"
    llm_base_url: str = "https://api.groq.com/openai/v1"

    # embeddings ( local sentence-transformers,no api key needed )
    embedding_model: str = "all-MiniLM-L6-v2"

    # database
    database_url: str = "sqlite:///./data/analyst.db"

    # vector DB
    chroma_persist_dir: str = "./chroma_db"

    # security
    secret_key: str = "change_this_in_production"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"
    
@lru_cache()
def get_settings() -> Settings:
    return Settings()