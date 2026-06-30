from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/rentals",
    tags=["Rentals"]
)

@router.get("/", response_model=List[schemas.RentalResponse])
def get_rentals(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    rentals = db.query(models.Rental).offset(skip).limit(limit).all()
    return rentals

@router.post("/", response_model=schemas.RentalResponse, status_code=status.HTTP_201_CREATED)
def start_rental(rental: schemas.RentalCreate, db: Session = Depends(get_db)):
    db_rental = models.Rental(**rental.model_dump())
    db.add(db_rental)
    db.commit()
    db.refresh(db_rental)
    return db_rental

@router.patch("/{rental_id}/complete", response_model=schemas.RentalResponse)
def complete_rental(rental_id: int, rental_update: schemas.RentalUpdate, db: Session = Depends(get_db)):
    rental = db.query(models.Rental).filter(models.Rental.rental_id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    
    rental.return_branch_id = rental_update.return_branch_id
    rental.return_date = rental_update.return_date
    rental.total_amount = rental_update.total_amount
    rental.status = schemas.RentalStatus.COMPLETED
    
    db.commit()
    db.refresh(rental)
    return rental
