# config.py
# Central place for configuration so create_app() can load it.
# Sensitive values (DB URL, secrets) live in .env and are loaded here.

import os

from dotenv import load_dotenv

load_dotenv()  # load .env into os.environ

class BaseConfig:
    # SQLAlchemy config: keeps Flask-SQLAlchemy from tracking every object change.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY")

class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError(
            "DATABASE_URL is not set. Copy .env.example to .env and set your database URL."
        )
    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True

    SQLALCHEMY_DATABASE_URI = "sqlite:///testing.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CACHE_TYPE = "SimpleCache"

    SECRET_KEY = "test_secret_key"



# Map config names to classes so create_app() can select by FLASK_ENV / CONFIG.
config_by_name = {
    "development": DevelopmentConfig,
    "DevelopmentConfig": DevelopmentConfig,
    "TestingConfig": TestingConfig,
}

