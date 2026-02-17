# application/models/__init__.py
# import all models so SQLAlchemy sees them when creating tables / migrations.

from application.models.customer import Customer 
from application.models.service_ticket import ServiceTicket
from application.models.mechanic import Mechanic