# config.py
# Central place for configuration so create_app() can load it.
# Sensitive values (DB URL, secrets) live in .env and are loaded here.

import os

try:
    from dotenv import load_dotenv
    load_dotenv()  # load .env into os.environ
except ImportError:
    pass

class BaseConfig:
    # SQLAlchemy config: keeps Flask-SQLAlchemy from tracking every object change.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY")

class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
    )

    if not SQLALCHEMY_DATABASE_URI and os.environ.get("FLASK_ENV", "").lower() != "testing":
        raise ValueError("Database URL is not set. Set DATABASE_URL or SQLALCHEMY_DATABASE_URI.")

    DEBUG = os.environ.get("FLASK_DEBUG", "true").lower() in ("1", "true", "yes")

class ProductionConfig(BaseConfig):
    DEBUG = False
    TESTING = False

    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("SQLALCHEMY_DATABASE_URI")
        or os.environ.get("DATABASE_URL")
    )

    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("Production database URL not set in environment variables.")

    CACHE_TYPE = "SimpleCache"


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
    
    "testing": TestingConfig,
    "TestingConfig": TestingConfig,
    
    "production": ProductionConfig,
    "ProductionConfig": ProductionConfig,
}

