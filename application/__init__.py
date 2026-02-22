# application/__init__.py
# Application factory: create_app() is the only place that creates a Flask instance.

import os
from flask import Flask
from flask_swagger_ui import get_swaggerui_blueprint

from config import DevelopmentConfig, ProductionConfig, config_by_name
from application.extensions import db, ma, limiter, cache, migrate

# Import models so SQLAlchemy knows about them (table creation/migrations).
import application.models  # noqa: F401

# Import blueprints (they are registered inside create_app).
from application.blueprints.customers import customers_bp
from application.blueprints.mechanics import mechanics_bp
from application.blueprints.tickets import tickets_bp
from application.blueprints.inventory import inventory_bp

SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "My Mechanic Shop API",
    },
)


def create_app(config_object=None):
    """Create and configure the Flask application (application factory pattern)."""
    if config_object is None:
        config_name = os.environ.get("FLASK_ENV", "development")
        config_object = config_by_name.get(config_name, DevelopmentConfig)

    # Require DATABASE_URL in production (e.g. Render); defer check so tests can import config with FLASK_ENV=testing.
    if config_object is ProductionConfig:
        uri = getattr(config_object, "SQLALCHEMY_DATABASE_URI", None)
        if not uri:
            raise ValueError("Production database URL not set in environment variables.")

    app = Flask(__name__)
    
    # load configuration (db uri, debug flags, etc)
    app.config.from_object(config_object)

    # Bind extensions to this app instance.
    db.init_app(app)
    ma.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints.
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(tickets_bp, url_prefix="/service-tickets")
    app.register_blueprint(inventory_bp, url_prefix="/inventory")
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)
    return app