from sqlalchemy import Column, Integer, String, Enum, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base
import enum

class VehicleStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"

class Vehicle(Base):
    __tablename__ = "VEHICLE"
    vehicle_id = Column(Integer, primary_key=True, index=True)
    registration_no = Column(String(50), unique=True)
    model = Column(String(100))
    category = Column(String(50))
    fuel_type = Column(String(50))
    status = Column(Enum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    branch_id = Column(Integer, ForeignKey("BRANCH.branch_id"), nullable=True)

    branch = relationship("Branch", back_populates="vehicles")
    reservations = relationship("Reservation", back_populates="vehicle")
    rentals = relationship("Rental", back_populates="vehicle")
