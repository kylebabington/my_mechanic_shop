"""Marshmallow schemas for the Service Ticket resource."""
from marshmallow import fields
from application.extensions import ma
from application.models.service_ticket import ServiceTicket
from application.blueprints.mechanics.schemas import MechanicSchema
from application.schemas.inventory_schema import InventorySchema


class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket
        load_instance = False

    VIN = fields.Str(required=True)
    service_date = fields.Str(required=True)
    service_desc = fields.Str(required=True)
    customer_id = fields.Int(required=True)
    mechanics = fields.Nested(MechanicSchema, many=True, dump_only=True)
    parts = fields.Nested(InventorySchema, many=True, dump_only=True)


ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)
