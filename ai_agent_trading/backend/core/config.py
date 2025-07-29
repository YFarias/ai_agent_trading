# backend/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    HOST: str
    PORT: int
    DATABASE: str
    USER_NAME: str
    PASSWORD: str

    class Config:
        env_file = ".env"
        extra = "ignore"

    def get_database_url(self) -> str:
        # Returns the database URL in the format required by SQLAlchemy for PostgreSQL
        return (
            f"postgresql+psycopg2://{self.USER_NAME}:{self.PASSWORD}"
            f"@{self.HOST}:{self.PORT}/{self.DATABASE}"
        )

settings = Settings()