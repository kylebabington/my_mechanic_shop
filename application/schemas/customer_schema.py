

from marshmallow import fields
from application.extensions import ma
from application.models.customer import Customer

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customer
        load_instance = False 

    name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str(required=False, allow_none=True)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)