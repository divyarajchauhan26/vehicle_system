from sqlalchemy import Column, Integer, DateTime, Enum, ForeignKey, Float
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class RentalStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"

class Rental(Base):
    __tablename__ = "RENTAL"
    rental_id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("RESERVATION.reservation_id"))
    vehicle_id = Column(Integer, ForeignKey("VEHICLE.vehicle_id"))
    pickup_branch_id = Column(Integer, ForeignKey("BRANCH.branch_id"))
    return_branch_id = Column(Integer, ForeignKey("BRANCH.branch_id"), nullable=True)
    pickup_date = Column(DateTime)
    return_date = Column(DateTime, nullable=True)
    total_amount = Column(Float, nullable=True)
    status = Column(Enum(RentalStatus), default=RentalStatus.ACTIVE)

    reservation = relationship("Reservation", back_populates="rental")
    vehicle = relationship("Vehicle", back_populates="rentals")
    pickup_branch = relationship("Branch", foreign_keys=[pickup_branch_id])
    return_branch = relationship("Branch", foreign_keys=[return_branch_id])
    payments = relationship("Payment", back_populates="rental")
