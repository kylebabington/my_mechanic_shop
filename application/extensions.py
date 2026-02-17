# application/extensions.py
# Declare extensions once. Do NOT bind them to an app here.

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flask_migrate import Migrate

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per day", "10 per hour"]
)

cache = Cache(config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 60
})

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

db = SQLAlchemy(model_class=Base)

ma = Marshmallow()

migrate = Migrate()