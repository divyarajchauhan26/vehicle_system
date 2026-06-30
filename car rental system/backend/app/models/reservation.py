from sqlalchemy import Column, Integer, Date, Enum, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class ReservationStatus(str, enum.Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class Reservation(Base):
    __tablename__ = "RESERVATION"
    reservation_id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("CUSTOMER.customer_id"))
    vehicle_id = Column(Integer, ForeignKey("VEHICLE.vehicle_id"))
    start_date = Column(Date)
    end_date = Column(Date)
    status = Column(Enum(ReservationStatus), default=ReservationStatus.CONFIRMED)
    
    customer = relationship("Customer", back_populates="reservations")
    vehicle = relationship("Vehicle", back_populates="reservations")
    rental = relationship("Rental", back_populates="reservation", uselist=False)
