# application/models/customer.py

from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from application.extensions import db, Base

from werkzeug.security import generate_password_hash, check_password_hash

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(255), nullable=False, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(db.String(50))

    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)

    # 1-to-Many: Customer -> ServiceTicket
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        back_populates="customer"
    )

    def set_password(self, plain_password: str) -> None:
        """
        Convert a plain password into a secure hash and store it.
        """
        self.password_hash = generate_password_hash(plain_password)

    def check_password(self, plain_password: str) -> bool:
        """
        Check a plain password against the stored hash.
        Returns True if correct, False otherwise.
        """
        return check_password_hash(self.password_hash, plain_password)