# application/__init__.py
# This is where create_app() lives.

from flask import Flask
from config import DevelopmentConfig
from application.extensions import db, ma

# import modesl so SQLAlchemy knows about them (table creation/migrations).
import application.models

# import blueprints
from application.blueprints.customers import customers_bp
from application.blueprints.mechanics import mechanics_bp
from application.blueprints.tickets import tickets_bp

def create_app(config_object=DevelopmentConfig):
    app = Flask(__name__)
    
    # load configuration (db uri, debug flags, etc)
    app.config.from_object(config_object)

    # Bind extensions to this app instance.
    db.init_app(app)
    ma.init_app(app)

    # Register blueprints.
    app.register_blueprint(customers_bp, url_prefix="/customers")
    app.register_blueprint(mechanics_bp, url_prefix="/mechanics")
    app.register_blueprint(tickets_bp, url_prefix="/tickets")

    with app.app_context():
        db.create_all()
    
    return app