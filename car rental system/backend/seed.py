from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models
import random
from datetime import datetime, timedelta
import sys
import os

# Ensure the app module can be found when running this script directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

def seed():
    print("Re-creating tables...")
    with engine.connect() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
        Base.metadata.drop_all(bind=engine)
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
    
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    print("Seeding database...")
    
    try:
        # Create Branches
        branch = models.Branch(name="Main Hub", address="123 Tech Avenue", city="San Francisco", phone="555-0192")
        db.add(branch)
        db.commit()
        db.refresh(branch)
        
        # Create Vehicles
        vehicles_data = [
            {"model": "Tesla Model S Plaid", "brand": "Tesla", "year": 2024, "category": "Luxury SUV", "fuel_type": "Electric", "daily_rate": 120.0, "status": "AVAILABLE", "license_plate": "TSLA-001", "branch_id": branch.branch_id},
            {"model": "BMW M3 Competition", "brand": "BMW", "year": 2023, "category": "Sedan", "fuel_type": "Petrol", "daily_rate": 95.0, "status": "AVAILABLE", "license_plate": "BMW-M3C", "branch_id": branch.branch_id},
            {"model": "Audi RS6 Avant", "brand": "Audi", "year": 2023, "category": "Wagon", "fuel_type": "Petrol", "daily_rate": 110.0, "status": "RENTED", "license_plate": "AUDI-RS6", "branch_id": branch.branch_id},
            {"model": "Porsche Taycan", "brand": "Porsche", "year": 2024, "category": "Luxury", "fuel_type": "Electric", "daily_rate": 150.0, "status": "AVAILABLE", "license_plate": "POR-TAY", "branch_id": branch.branch_id},
            {"model": "Toyota RAV4 Hybrid", "brand": "Toyota", "year": 2023, "category": "SUV", "fuel_type": "Hybrid", "daily_rate": 65.0, "status": "AVAILABLE", "license_plate": "TOY-R4H", "branch_id": branch.branch_id},
            {"model": "Mercedes G63 AMG", "brand": "Mercedes", "year": 2022, "category": "Luxury SUV", "fuel_type": "Petrol", "daily_rate": 200.0, "status": "MAINTENANCE", "license_plate": "MER-G63", "branch_id": branch.branch_id},
        ]
        
        vehicles = []
        for v in vehicles_data:
            vehicle = models.Vehicle(**v)
            db.add(vehicle)
            vehicles.append(vehicle)
        db.commit()
        
        # Create Customers
        customers_data = [
            {"first_name": "Sarah", "last_name": "Jenkins", "email": "sarah@example.com", "phone": "555-1001", "license_number": "DL-001", "status": "ACTIVE"},
            {"first_name": "Michael", "last_name": "Chen", "email": "michael@example.com", "phone": "555-1002", "license_number": "DL-002", "status": "ACTIVE"},
            {"first_name": "Emma", "last_name": "Watson", "email": "emma@example.com", "phone": "555-1003", "license_number": "DL-003", "status": "ACTIVE"},
        ]
        
        customers = []
        for c in customers_data:
            customer = models.Customer(**c)
            db.add(customer)
            customers.append(customer)
        db.commit()
        
        # Create Rentals and Payments
        # Emma is currently renting Audi RS6
        rental1 = models.Rental(
            customer_id=customers[2].customer_id,
            vehicle_id=vehicles[2].vehicle_id,
            pickup_branch_id=branch.branch_id,
            pickup_date=datetime.now() - timedelta(days=2),
            expected_return_date=datetime.now() + timedelta(days=3),
            status="ACTIVE",
            total_amount=550.0
        )
        db.add(rental1)
        db.commit()
        db.refresh(rental1)
        
        payment1 = models.Payment(
            rental_id=rental1.rental_id,
            amount=550.0,
            payment_method="CREDIT_CARD",
            status="COMPLETED",
            transaction_id="TRX-1001"
        )
        db.add(payment1)
        db.commit()
        
        # Sarah rented Tesla last week
        rental2 = models.Rental(
            customer_id=customers[0].customer_id,
            vehicle_id=vehicles[0].vehicle_id,
            pickup_branch_id=branch.branch_id,
            return_branch_id=branch.branch_id,
            pickup_date=datetime.now() - timedelta(days=10),
            expected_return_date=datetime.now() - timedelta(days=7),
            return_date=datetime.now() - timedelta(days=7),
            status="COMPLETED",
            total_amount=360.0
        )
        db.add(rental2)
        db.commit()
        db.refresh(rental2)
        
        payment2 = models.Payment(
            rental_id=rental2.rental_id,
            amount=360.0,
            payment_method="CREDIT_CARD",
            status="COMPLETED",
            transaction_id="TRX-1002"
        )
        db.add(payment2)
        db.commit()
        
        print("Database seeded successfully!")
    except Exception as e:
        print(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
