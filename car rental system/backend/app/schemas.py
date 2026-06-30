from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import date, datetime
from enum import Enum

# Enums
class DocumentStatus(str, Enum):
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    PENDING = "PENDING"

class VehicleStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RENTED = "RENTED"
    MAINTENANCE = "MAINTENANCE"
    RETIRED = "RETIRED"

class ReservationStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"

class RentalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"

class PaymentStatus(str, Enum):
    COMPLETED = "COMPLETED"
    PENDING = "PENDING"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

# --- Membership ---
class MembershipBase(BaseModel):
    membership_type: str
    discount_rate: float = 0.0

class MembershipCreate(MembershipBase):
    pass

class MembershipResponse(MembershipBase):
    membership_id: int
    class Config:
        from_attributes = True

# --- Customer ---
class CustomerBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    membership_id: Optional[int] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    customer_id: int
    membership: Optional[MembershipResponse] = None
    class Config:
        from_attributes = True

# --- Branch ---
class BranchBase(BaseModel):
    branch_name: str
    location: str
    phone: str

class BranchCreate(BranchBase):
    pass

class BranchResponse(BranchBase):
    branch_id: int
    class Config:
        from_attributes = True

# --- Vehicle ---
class VehicleBase(BaseModel):
    registration_no: str
    model: str
    category: str
    fuel_type: str
    status: VehicleStatus = VehicleStatus.AVAILABLE
    branch_id: Optional[int] = None

class VehicleCreate(VehicleBase):
    pass

class VehicleResponse(VehicleBase):
    vehicle_id: int
    branch: Optional[BranchResponse] = None
    class Config:
        from_attributes = True

# --- Reservation ---
class ReservationBase(BaseModel):
    customer_id: int
    vehicle_id: int
    start_date: date
    end_date: date

class ReservationCreate(ReservationBase):
    pass

class ReservationResponse(ReservationBase):
    reservation_id: int
    status: ReservationStatus
    customer: Optional[CustomerResponse] = None
    vehicle: Optional[VehicleResponse] = None
    class Config:
        from_attributes = True

# --- Rental ---
class RentalBase(BaseModel):
    reservation_id: int
    vehicle_id: int
    pickup_branch_id: int
    pickup_date: datetime

class RentalCreate(RentalBase):
    pass

class RentalUpdate(BaseModel):
    return_branch_id: int
    return_date: datetime
    total_amount: float

class RentalResponse(RentalBase):
    rental_id: int
    return_branch_id: Optional[int] = None
    return_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    status: RentalStatus
    reservation: Optional[ReservationResponse] = None
    class Config:
        from_attributes = True

# --- Payment ---
class PaymentBase(BaseModel):
    rental_id: int
    amount: float
    payment_type: str

class PaymentCreate(PaymentBase):
    pass

class PaymentResponse(PaymentBase):
    payment_id: int
    payment_date: datetime
    status: PaymentStatus
    class Config:
        from_attributes = True
