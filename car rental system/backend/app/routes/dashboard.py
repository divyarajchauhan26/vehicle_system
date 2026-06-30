from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_customers = db.query(models.Customer).count()
    total_vehicles = db.query(models.Vehicle).count()
    active_rentals = db.query(models.Rental).filter(models.Rental.status == "ACTIVE").count()
    
    # Calculate simple revenue (sum of completed payments)
    revenue = db.query(func.sum(models.Payment.amount)).filter(models.Payment.status == "COMPLETED").scalar() or 0.0
    
    # Simple utilization (Rented / Total)
    rented_vehicles = db.query(models.Vehicle).filter(models.Vehicle.status == "RENTED").count()
    utilization = (rented_vehicles / total_vehicles * 100) if total_vehicles > 0 else 0
    
    return {
        "total_customers": total_customers,
        "total_vehicles": total_vehicles,
        "active_rentals": active_rentals,
        "revenue": float(revenue),
        "utilization_pct": round(utilization, 1),
        "available_vehicles": db.query(models.Vehicle).filter(models.Vehicle.status == "AVAILABLE").count()
    }
