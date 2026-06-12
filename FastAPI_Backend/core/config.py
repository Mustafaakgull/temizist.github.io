from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "TemizIST API"
    DATABASE_URL: str = "postgresql+asyncpg://temizist:temizist_pass@db:5432/temizist_db"
    # PC'de çalışan AI sunucusu. Docker'da: http://host.docker.internal:9000
    AI_SERVER_URL: str = "http://127.0.0.1:9000"
    
    class Config:
        env_file = ".env"

settings = Settings()
