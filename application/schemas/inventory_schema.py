# application/schemas/inventory_schema.py
# Marshmallow schemas for Inventory model.

from marshmallow import fields
from application.extensions import ma
from application.models.inventory import Inventory

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        load_instance = False

    name = fields.Str(required=True)
    price = fields.Float(required=True)

inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)