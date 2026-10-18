
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET or len(JWT_SECRET) < 32 or JWT_SECRET.lower() in ("changeme", "secret", "password"):
        raise ValueError("JWT_SECRET must be set to a secure value of at least 32 characters")

    DEBUG = False
    DATABASE = os.getenv("DATABASE_PATH", "recipes.db")


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DATABASE = os.getenv("TEST_DATABASE_PATH", "recipes_test.db")


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
