# application/extensions.py
# Declare extensions once. Do NOT bind them to an app here.

from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """Base class for all models"""
    pass

db = SQLAlchemy(model_class=Base)

ma = Marshmallow()