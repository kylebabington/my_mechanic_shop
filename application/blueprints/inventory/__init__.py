# application/blueprints/inventory/routes.py
# Blueprint initialization for inventory routes.

from flask import Blueprint

inventory_bp = Blueprint("inventory_bp", __name__)

from application.blueprints.inventory import routes