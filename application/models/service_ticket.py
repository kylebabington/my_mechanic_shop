# application/models/service_ticket.py
# Service Ticket model + the many-to-many table lives here.

from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from application.extensions import db, Base
from application.models.inventory import service_ticket_inventory

service_mechanics = db.Table(
    "service_mechanics",
    Base.metadata,
    db.Column("ticket_id", db.ForeignKey("service_tickets.id"), primary_key=True),
    db.Column("mechanic_id", db.ForeignKey("mechanics.id"), primary_key=True)
)

class ServiceTicket(Base):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(db.String(50), nullable=False)
    service_date: Mapped[str] = mapped_column(db.String(50), nullable=False)
    service_desc: Mapped[str] = mapped_column(db.String(255), nullable=False)

    customer_id: Mapped[int] = mapped_column(db.ForeignKey("customers.id"), nullable=False)

    parts: Mapped[List["Inventory"]] = relationship(
        secondary=service_ticket_inventory,
        back_populates="service_tickets",
    )

    # "Customer" is declared in customer.py, but we can still refer to it by string.
    customer: Mapped["Customer"] = relationship(back_populates="service_tickets")

    mechanics: Mapped[List["Mechanic"]] = relationship(
        secondary=service_mechanics,
        back_populates="service_tickets",

    
    )