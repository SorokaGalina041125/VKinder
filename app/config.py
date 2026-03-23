"""
Конфигурация приложения с использованием pydantic-settings.
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Настройки приложения"""
    
    # VK Tokens
    VK_GROUP_TOKEN: str = ""
    VK_USER_TOKEN: str = ""
    VK_GROUP_ID: Optional[int] = None
    
    # Database
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: str = "5432"
    DB_NAME: str = "vkinder"
    
    # Search settings
    SEARCH_BATCH_SIZE: int = 100
    SEARCH_MAX_CANDIDATES: int = 1000
    SEARCH_SLEEP_BETWEEN: float = 0.5
    
    # Scoring weights
    SCORE_AGE_WEIGHT: float = 0.3
    SCORE_INTERESTS_WEIGHT: float = 0.4
    SCORE_CITY_WEIGHT: float = 0.1
    SCORE_FRIENDS_WEIGHT: float = 0.2
    
    # Interest weights
    INTEREST_GROUPS_WEIGHT: float = 0.4
    INTEREST_MUSIC_WEIGHT: float = 0.35
    INTEREST_BOOKS_WEIGHT: float = 0.25
    
    # Test settings
    TEST_USER_ID: int = 123456
    TEST_CANDIDATE_ID: int = 1
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL connection URL"""
        return f"postgresql+psycopg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def SYSTEM_DSN(self) -> str:
        """System DSN for database creation"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/postgres"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Глобальный экземпляр настроек
settings = Settings()


def get_test_settings() -> Settings:
    """Получить настройки для тестового окружения"""
    return Settings(_env_file=".env.test")
