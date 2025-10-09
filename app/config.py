from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/spaced_repetition_db"

    # Environment
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
