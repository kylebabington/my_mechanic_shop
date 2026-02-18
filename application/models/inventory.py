# application/models/inventory.py
# This file defines the Inventory model (parts in the shop).

from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from application.extensions import db, Base

service_ticket_inventory = db.Table(
    "service_ticket_inventory",
    Base.metadata,
    db.Column("ticket_id", db.ForeignKey("service_tickets.id"), primary_key=True),
    db.Column("inventory_id", db.ForeignKey("inventory.id"), primary_key=True),
)

class Inventory(Base):
    """
    Inventory = a part in the mechanic shop (ex: Oil Filter, Brake Pads, etc.)
    """
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)

    price: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)

    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        secondary=service_ticket_inventory,
        back_populates="parts"
    )