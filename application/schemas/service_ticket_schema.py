from marshmallow import fields
from application.extensions import ma
from application.models.service_ticket import ServiceTicket

class ServiceTicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ServiceTicket
        load_instance = False

    VIN = fields.Str(required=True)
    service_date = fields.Str(required=True)
    service_desc = fields.Str(required=True)
    customer_id = fields.Int(required=True)

ticket_schema = ServiceTicketSchema()
tickets_schema = ServiceTicketSchema(many=True)