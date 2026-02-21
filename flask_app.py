# flask_app.py
# Gunicorn entrypoint for Render.
# Gunicorn will import "app" from this file.

from application import create_app
from config import ProductionConfig

app = create_app(ProductionConfig)