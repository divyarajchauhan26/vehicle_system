from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..database import Base

class Branch(Base):
    __tablename__ = "BRANCH"
    branch_id = Column(Integer, primary_key=True, index=True)
    branch_name = Column(String(100))
    location = Column(String(255))
    phone = Column(String(20))
    
    vehicles = relationship("Vehicle", back_populates="branch")
