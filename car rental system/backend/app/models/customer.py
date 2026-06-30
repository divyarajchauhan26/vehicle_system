from sqlalchemy import Column, Integer, String, Boolean, Date, DateTime, ForeignKey, Enum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import enum

class Membership(Base):
    __tablename__ = "MEMBERSHIP"
    membership_id = Column(Integer, primary_key=True, index=True)
    membership_type = Column(String(50), unique=True)
    discount_rate = Column(Float, default=0.0)
    customers = relationship("Customer", back_populates="membership")

class Customer(Base):
    __tablename__ = "CUSTOMER"
    customer_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(150), unique=True, index=True)
    phone = Column(String(20))
    membership_id = Column(Integer, ForeignKey("MEMBERSHIP.membership_id"))
    
    membership = relationship("Membership", back_populates="customers")
    documents = relationship("Document", back_populates="customer")
    reservations = relationship("Reservation", back_populates="customer")

class DocumentStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class Document(Base):
    __tablename__ = "DOCUMENT"
    document_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("CUSTOMER.customer_id"))
    document_type = Column(String(50))
    document_number = Column(String(100))
    expiry_date = Column(Date)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.PENDING)
    
    customer = relationship("Customer", back_populates="documents")
