# application/models/customer.py

from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from application.extensions import db, Base

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(50))

    # 1-to-Many: Customer -> ServiceTicket
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        back_populates="customer"
    )