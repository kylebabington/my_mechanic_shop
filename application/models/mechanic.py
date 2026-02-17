from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from application.extensions import db, Base
from application.models.service_ticket import service_mechanics

class Mechanic(Base):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(50))
    salary: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)

    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        secondary=service_mechanics,
        back_populates="mechanics",
    )