from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://agrodata:agrodata@127.0.0.1:5433/agrodata"
    jwt_secret: str
    frontend_url: str = "http://localhost:3000"
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[1] / ".env", extra="ignore")
settings = Settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
Session = sessionmaker(engine)
class Base(DeclarativeBase): pass
