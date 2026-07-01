# Vehicle System

A full-stack car rental management system built with FastAPI on the backend and React on the frontend. It provides a simple way to manage vehicles, customers, reservations, rentals, payments, and an admin dashboard.

## Overview

This project combines a modern REST API with a responsive web interface to support car rental operations in a clean and structured way.

## Features

- Manage vehicles and availability
- Handle customer records
- Create and track reservations
- Process rentals and payments
- View administrative dashboard insights
- REST API documentation with FastAPI

## Tech Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- MySQL / MariaDB support
- Pydantic

### Frontend
- React
- Vite
- TypeScript
- Axios
- Tailwind CSS

## Project Structure

```text
car rental system/
├── backend/
│   ├── app/
│   ├── requirements.txt
│   └── seed.py
└── frontend/
    ├── src/
    └── package.json
```

## Getting Started

### 1. Backend Setup

```bash
cd "car rental system/backend"
python -m venv .venv
source .venv/bin/activate
# On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Run the backend server:

```bash
uvicorn app.main:app --reload
```

The API will be available at:

- http://127.0.0.1:8000
- http://127.0.0.1:8000/docs

### 2. Frontend Setup

```bash
cd "../frontend"
npm install
npm run dev
```

The frontend will be available at:

- http://localhost:5173

## Configuration

Before running the app, make sure your database settings are configured properly in the backend configuration files.

## Notes

- The backend includes seed data support through the seed script.
- The frontend is built for a simple and clean admin-style experience.

## License

This project is intended for learning and demonstration purposes.
