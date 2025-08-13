# 🎟️ Eventix

This repository contains the **Eventix** ticket booking platform, built with FastAPI, SQLAlchemy, and PostgreSQL.  
It includes both the **User Service** and the **Event Service** for managing users, events, venues, and ticket pricing.

---

## ⚡ Prerequisites

- 🐍 Python 3.12+
- 🐳 Docker & Docker Compose
- 🛢️ PostgreSQL (via Docker)
- 🛡️ (Recommended) Virtual environment

---

## 🚀 Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/your-org/eventix-user-service.git
   cd eventix-user-service
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv .venv
   .venv\Scripts\activate
   ```
   with uv package manager
   ```sh
   uv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
   with uv package manager
   ```sh
   uv pip install -r requirements.txt
   ```

<!-- 4. **Configure environment variables:**
   - Copy `.env.example` to `.env` and update values as needed (especially the database URL). -->

5. **Start PostgreSQL with Docker Compose:**
   ```sh
   docker compose up -d
   ```

<!-- 6. **Run Alembic migrations:**
   ```sh
   alembic upgrade head
   ``` -->

## 🏃‍♂️ Running the Service

### 👤 User Service

   Start the FastAPI server:

   ```sh
   uvicorn main:app --reload
   ```

   The API will be available at [http://localhost:8000](http://localhost:8000).

### 🎫 Event Service

   Start the FastAPI server for event management:

   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8002 --reload
   ```

   The API will be available at [http://localhost:8002](http://localhost:8002).

---

## 🗂️ Project Structure

### User Service

- `main.py` — 🚦 FastAPI entrypoint
- `database.py` — 🗄️ Database setup
- `models.py` — 🧩 SQLAlchemy models
- `auth.py` — 🔐 Authentication routes
<!-- - `alembic/` — 🛠️ Database migrations -->

### Event Service

- `routes/pricing_routes.py` — 💸 Pricing tier management for events
- `routes/events_routes.py` — 🎉 Event CRUD operations
- `routes/venue_routes.py` — 🏟️ Venue and section management
- `models.py` — 🧩 SQLAlchemy models for events, venues, pricing, etc.
- `schemas.py` — 📦 Pydantic schemas for request/response validation

---

<!-- ## Useful Commands

- **Run tests:**  
  ```sh
  pytest
  ```
- **Generate a new Alembic migration:**  
  ```sh
  alembic revision --autogenerate -m "Migration message"
  ```
- **Upgrade database:**  
  ```sh
  alembic upgrade head
  ``` -->

---

## 🎫 Event Service Features

- **Event Management:** Create, update, and list events.
- **Venue Management:** Manage venues and their sections.
- **Pricing Tiers:**  
  - Create pricing tiers for events and venue sections  
  - Update pricing tiers and seat availability  
  - Deactivate pricing tiers
- **Search & Pagination:** Filter and paginate events and pricing tiers.

---

## Troubleshooting

- Ensure Docker containers are running before running the app.
<!-- - If you see `KeyError: 'USER_DB_URL'`, check your `.env` file and environment variable setup. -->

---