import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Shared configuration settings."""
    JWT_SECRET = os.getenv("JWT_SECRET")
    DEBUG = False
    DATABASE = "recipes.db"


class DevelopmentConfig(Config):
    """Settings for development."""
    DEBUG = True


class TestingConfig(Config):
    """Settings for testing."""
    DEBUG = False
    TESTING = True
    DATABASE = "recipes_test.db"


class ProductionConfig(Config):
    """Settings for production."""
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
