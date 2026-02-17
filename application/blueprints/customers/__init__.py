# application/blueprints/customers/__init__.py
from flask import Blueprint

customers_bp = Blueprint("customers", __name__)

from application.blueprints.customers import routes