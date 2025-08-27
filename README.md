# 🎟️ Eventix

A comprehensive **microservices-based ticket booking platform** built with FastAPI, SQLAlchemy, and PostgreSQL.  
The system includes **User Service**, **Event Service**, **Booking Service**, **Payment Service**, and **API-Gateway** for complete ticket management.

---

## ⚡ Prerequisites

- 🐍 Python 3.12+
- 🐳 Docker & Docker Compose
- 🛢️ PostgreSQL (via Docker)
- 🐰 RabbitMQ (via Docker)
- 🛡️ (Recommended) Virtual environment

---

## 🚀 Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/your-org/eventix-user-service.git
   cd eventix-user-service
   ```

2. **Environment Setup**

   **Option A: Full Docker Development**
   ```bash
   # Change the production variable in mode.py
   production = True

   # Build and start all services with Docker
   docker-compose up --build -d
   ```
   
   **Option B: Hybrid Development (Databases in Docker, Services Local)**
   ```bash
   # 1. Start only databases and RabbitMQ
   docker-compose up -d user-db event-db booking-db payment-db rabbitmq

   # 2. Create virtual environment for each service
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac

   # 3. Install dependencies for each service
   cd services/user-service
   pip install -r requirements.txt

   # 4. Change the production variable in mode.py
   production = False

   # 5. Start services locally (in separate terminals)
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

      # Terminal 5 - API Gateway
      cd services/api-gateway
      uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

---

## 🗂️ Project Structure

```
Eventix/
├── 📁 services/
│   ├── 📁 user-service/
│   │   ├── main.py                 # 🚦 FastAPI app & lifespan management
│   │   ├── models.py               # 🧩 User, UserProfile, Session models
│   │   ├── schemas.py              # 📝 Pydantic request/response models
│   │   ├── database.py             # 🗄️ Database connection & session
│   │   ├── auth.py                 # 🔐 JWT authentication utilities
│   │   ├── admin.py                # 👑 Admin user creation
│   │   ├── requirements.txt        # 📦 Python dependencies
│   │   ├── Dockerfile              # 🐳 Container configuration
│   │   └── 📁 routes/
│   │       ├── auth.py             # 🔑 Authentication endpoints
│   │       ├── preference_routes.py # ⚙️ User preferences
│   │       ├── notification_routes.py # 📧 Notifications
│   │       └── session_routes.py   # 🔗 Session management
│   │
│   ├── 📁 event-service/
│   │   ├── main.py                 # 🎫 Event management API
│   │   ├── models.py               # 🧩 Event, Venue, Pricing models
│   │   ├── schemas.py              # 📝 Event schemas
│   │   ├── database.py             # 🗄️ Database configuration
│   │   ├── requirements.txt        # 📦 Dependencies
│   │   ├── Dockerfile              # 🐳 Container configuration
│   │   └── 📁 routes/
│   │       └── event_routes.py     # 🎪 Event CRUD operations
│   │
│   ├── 📁 booking-service/
│   │   ├── main.py                 # 📝 Booking management & saga pattern
│   │   ├── models.py               # 🧩 Booking, SeatReservation models
│   │   ├── schemas.py              # 📝 Booking schemas
│   │   ├── database.py             # 🗄️ Database configuration
│   │   ├── auth.py                 # 🔐 JWT token validation
│   │   ├── requirements.txt        # 📦 Dependencies
│   │   ├── Dockerfile              # 🐳 Container configuration
│   │   └── 📁 routes/
│   │       ├── booking_routes.py   # 🎟️ Booking operations
│   │       └── saga_routes.py      # 🔄 Saga transaction management
│   │
│   ├── 📁 payment-service/
│   │   ├── main.py                 # 💳 Payment processing
│   │   ├── models.py               # 🧩 Payment, Transaction models
│   │   ├── schemas.py              # 📝 Payment schemas
│   │   ├── database.py             # 🗄️ Database configuration
│   │   ├── auth.py                 # 🔐 JWT token validation
│   │   ├── requirements.txt        # 📦 Dependencies
│   │   ├── Dockerfile              # 🐳 Container configuration
│   │   └── 📁 routes/
│   │       └── payment_routes.py   # 💰 Payment operations
│   │
│   └── 📁 api-gateway/
│       ├── main.py                 # 🌐 API Gateway & request routing
│       ├── requirements.txt        # 📦 Dependencies
│       └── Dockerfile              # 🐳 Container configuration
│
├── 📁 shared/
│   ├── __init__.py                 # 📦 Shared module initialization
│   ├── rabbitmq_client.py          # 🐰 RabbitMQ connection & messaging
│   ├── event_publisher.py          # 📢 Event publishing utilities
│   └── event_handler.py            # 📥 Event handling base classes
│
├── docker-compose.yml              # 🐳 Complete system orchestration
├── .dockerignore                   # 🚫 Docker ignore patterns
└── README.md                       # 📚 This documentation
```

---

## 🎯 Core Features

### 🌐 API Gateway (Port 8080)
**Single entry point for all client requests:**
- **Request Routing**: Intelligent routing to microservices
- **Authentication**: Centralized JWT token validation  
- **Load Balancing**: Distribute requests across service instances
- **Health Monitoring**: Service availability checking

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

### 📡 API Endpoints

**Access via API Gateway (http://localhost:8080):**
- **User Routes**: `/api/v1/auth/*`, `/api/v1/users/*`
- **Event Routes**: `/api/v1/events/*`
- **Booking Routes**: `/api/v1/bookings/*`
- **Payment Routes**: `/api/v1/payments/*`

**Direct Service Access (Development):**
- **🌐 API Gateway**: http://localhost:8080/docs
- **👤 User Service**: http://localhost:8000/docs
- **🎫 Event Service**: http://localhost:8001/docs  
- **📝 Booking Service**: http://localhost:8002/docs
- **💳 Payment Service**: http://localhost:8003/docs
---

## 🗄️ Database Architecture

### 📊 Database Per Service Pattern
Each service has its own PostgreSQL database:

- **user-db** (Port 5432): User accounts, profiles, sessions
- **event-db** (Port 5433): Events, venues, seats, pricing
- **booking-db** (Port 5434): Bookings, reservations, history
- **payment-db** (Port 5435): Payments, transactions, refunds

### 🔄 Data Consistency
- **Event Sourcing**: All state changes are events
- **Saga Pattern**: Distributed transaction management
- **Eventual Consistency**: Cross-service data synchronization

---

## 🔐 Security Features

### 🛡️ Authentication & Authorization
- **JWT Tokens**: Stateless authentication
- **Role-Based Access**: User/Admin role separation
- **Token Validation**: Centralized in API Gateway
- **Session Management**: Active session tracking

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