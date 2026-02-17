from marshmallow import fields
from application.extensions import ma
from application.models.mechanic import Mechanic

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanic
        load_instance = False

    name = fields.Str(required=True)
    email = fields.Email(required=True)
    phone = fields.Str(required=False, allow_none=True)
    salary = fields.Float(required=True)

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)