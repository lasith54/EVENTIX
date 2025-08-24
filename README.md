# 🎟️ Eventix

A comprehensive **microservices-based ticket booking platform** built with FastAPI, SQLAlchemy, and PostgreSQL.  
The system includes **User Service**, **Event Service**, **Booking Service**, and **Payment Service** for complete ticket management.

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

### 2️⃣ Start All Services
```bash
# Build and start all services
docker-compose up --build -d
```

**Start services locally:**
```bash
# Terminal 1 - User Service
cd services/user-service
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Event Service  
cd services/event-service
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Terminal 3 - Booking Service
cd services/booking-service
uvicorn main:app --host 0.0.0.0 --port 8002 --reload

# Terminal 4 - Payment Service
cd services/payment-service
uvicorn main:app --host 0.0.0.0 --port 8003 --reload
```

---

## 🗂️ Project Structure

```
eventix/
├── 📁 services/
│   ├── 📁 user-service/
│   │   ├── main.py              # 🚦 FastAPI app & authentication
│   │   ├── models.py            # 🧩 User, preferences, sessions
│   │   ├── database.py          # 🗄️ Database setup
│   │   ├── auth_utils.py        # 🔐 JWT & password utilities
│   │   ├── admin.py             # 👑 Admin user creation
│   │   └── requirements.txt     # 📦 Python dependencies
│   │
│   ├── 📁 event-service/
│   │   ├── main.py              # 🎫 Event management API
│   │   ├── models.py            # 🧩 Events, venues, pricing
│   │   ├── schemas.py           # 📝 Pydantic models
│   │   └── requirements.txt     # 📦 Dependencies
│   │
│   ├── 📁 booking-service/
│   │   ├── main.py              # 📝 Booking management
│   │   ├── models.py            # 🧩 Bookings, seats, history
│   │   ├── schemas.py           # 📝 Booking schemas
│   │   └── requirements.txt     # 📦 Dependencies
│   │
│   └── 📁 payment-service/
│       ├── main.py              # 💳 Payment processing
│       ├── models.py            # 🧩 Payments, transactions
│       ├── schemas.py           # 📝 Payment schemas
│       └── requirements.txt     # 📦 Dependencies
│
├── docker-compose.yml           # 🐳 Full system orchestration
├── start-eventix.sh             # 🚀 Startup script
└── README.md                    # 📚 This file
```

---

## 🎯 Core Features

### 👤 User Service (Port 8000)
- **Authentication**: JWT-based login/registration
- **User Management**: Profile, preferences, sessions
- **Admin Panel**: Admin user creation and management
- **Email Notifications**: Booking confirmations, receipts

### 🎫 Event Service (Port 8001)
- **Event Management**: Create, update, list events
- **Venue Management**: Venues with seating sections
- **Pricing Tiers**: Multiple pricing levels per event
- **Seat Management**: Real-time availability tracking
- **Admin Panel**: Full event administration

### 📝 Booking Service (Port 8002)  
- **Seat Reservation**: Temporary holds during booking
- **Booking Management**: Create, confirm, cancel bookings
- **Booking History**: Complete audit trail
- **Timeout Handling**: Auto-release expired reservations

### 💳 Payment Service (Port 8003)
- **Payment Processing**: Multiple gateway support
- **Transaction Logging**: Complete payment history
- **Refund Management**: Full and partial refunds
- **Payment Status**: Real-time payment tracking

---

## 🔐 Default Admin Access

**Admin Login:**
- **Email**: `admin@eventix.com`
- **Password**: `admin123`

The admin user is automatically created when the user service starts.

---

## Troubleshooting

- Ensure Docker containers are running before running the app.
<!-- - If you see `KeyError: 'USER_DB_URL'`, check your `.env` file and environment variable setup. -->

---