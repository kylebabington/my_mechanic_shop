

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

    password = fields.Str(required=True, load_only=True)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)

class CustomerLoginSchema(ma.Schema):
    """
    Schema used only for login payload validation.
    """
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)

login_schema = CustomerLoginSchema()