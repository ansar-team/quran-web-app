from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/spaced_repetition_db"

    telegram_bot_token: str = "bot_token"

    # Environment
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
