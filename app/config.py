
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JWT_SECRET = os.getenv("JWT_SECRET")
    if not JWT_SECRET or len(JWT_SECRET) < 32 or JWT_SECRET.lower() in ("changeme", "secret", "password"):
        raise ValueError("JWT_SECRET must be set to a secure value of at least 32 characters")

    DEBUG = False
    DATABASE = os.getenv("DATABASE_PATH", "recipes.db")

    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.abspath(DATABASE)

class DevelopmentConfig(Config):
    SLOW_SERVICE_BASE_URL = "http://localhost:5001"
    DEBUG = True


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    DATABASE = os.getenv("TEST_DATABASE_PATH", "recipes_test.db")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.abspath(DATABASE)

class EmptyBaselineConfig(Config):
    DATABASE = "baseline_empty.db"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.abspath(DATABASE)


class ProductionConfig(Config):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "baseline": EmptyBaselineConfig,
    "production": ProductionConfig,
}
