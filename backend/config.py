from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    GROQ_API_KEY: str
    FIRECRAWL_API_KEY: str
    DATABASE_URL: str
    SERPAPI_KEY: str         
    SCRAPE_INTERVAL_HOURS: int = 6

    class Config:
        env_file = ".env"

settings = Settings()