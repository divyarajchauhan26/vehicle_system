from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum

class PaymentStatus(str, enum.Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class Payment(Base):
    __tablename__ = "PAYMENT"
    payment_id = Column(Integer, primary_key=True, index=True)
    rental_id = Column(Integer, ForeignKey("RENTAL.rental_id"))
    amount = Column(Float)
    payment_date = Column(DateTime, default=func.now())
    payment_type = Column(String(50))
    status = Column(Enum(PaymentStatus), default=PaymentStatus.COMPLETED)
    
    rental = relationship("Rental", back_populates="payments")
