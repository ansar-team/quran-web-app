from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str
    telegram_bot_token: str
    debug: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
