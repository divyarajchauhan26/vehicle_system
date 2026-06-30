from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .database import engine, Base
from . import models
from .routes import vehicles, customers

# Create database tables (Ideally use Alembic for this, but for now we create directly if they don't exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DRIVEFLOW API",
    description="Car Rental System API",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace with frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicles.router)
app.include_router(customers.router)
app.include_router(reservations.router)
app.include_router(rentals.router)
app.include_router(payments.router)
app.include_router(dashboard.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to DRIVEFLOW API. Visit /docs for Swagger documentation."}
