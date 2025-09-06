# 🎟️ Eventix

A comprehensive **microservices-based ticket booking platform** built with FastAPI, SQLAlchemy, and PostgreSQL.  
The system includes **User Service**, **Event Service**, **Booking Service**, **Payment Service**, and **API-Gateway** for complete ticket management.

---

## ✨ Key Features

- 🏗️ **Microservices Architecture** - Scalable, distributed system design
- 🔐 **JWT Authentication** - Secure user authentication and authorization
- 🎫 **Event Management** - Complete event lifecycle management
- 💺 **Real-time Seat Booking** - Live seat availability and reservations
- 💳 **Payment Processing** - Integrated payment gateway with transaction tracking
- 🔄 **Saga Pattern** - Distributed transaction management
- 📧 **Event-driven Architecture** - RabbitMQ message queuing
- 🐳 **Docker Support** - Containerized deployment
- 📊 **Database per Service** - Independent data storage per microservice

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
2. **Configure for production:**
   ```bash
   # Set production mode in mode.py
   production = True
   ```

3. **Start all services:**
   ```bash
   docker-compose up --build -d
   ```
4. **Access the application:**
   - 🌐 **API Gateway**: http://localhost:8080/docs
   - 👤 **User Service**: http://localhost:8000/docs
   - 🎫 **Event Service**: http://localhost:8001/docs
   - 📝 **Booking Service**: http://localhost:8002/docs
   - 💳 **Payment Service**: http://localhost:8003/docs

### Option B: Hybrid Development (Local Services)

1. **Start infrastructure services:**
   ```bash
   docker-compose up -d user-db event-db booking-db payment-db rabbitmq
   ```

2. **Configure for development:**
   ```bash
   # Set development mode in mode.py
   production = False
   ```

3. **Setup each service** (repeat for each service):
   ```bash
   # Create virtual environment
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac

   # Install dependencies
   cd services/[service-name]
   pip install -r requirements.txt
   ```

4. **Start services** (in separate terminals):
   ```bash
   # User Service (Terminal 1)
   cd services/user-service && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

   # Event Service (Terminal 2)
   cd services/event-service && uvicorn main:app --host 0.0.0.0 --port 8001 --reload

   # Booking Service (Terminal 3)
   cd services/booking-service && uvicorn main:app --host 0.0.0.0 --port 8002 --reload

   # Payment Service (Terminal 4)
   cd services/payment-service && uvicorn main:app --host 0.0.0.0 --port 8003 --reload

   # API Gateway (Terminal 5)
   cd services/api-gateway && uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

---

## 🏗️ Architecture Overview

### 🧩 Microservices

| Service | Port | Database | Description |
|---------|------|----------|-------------|
| 🌐 **API Gateway** | 8080 | - | Single entry point, request routing, authentication |
| 👤 **User Service** | 8000 | user-db:5432 | Authentication, user management, profiles |
| 🎫 **Event Service** | 8001 | event-db:5433 | Event management, venues, pricing |
| 📝 **Booking Service** | 8002 | booking-db:5434 | Seat reservations, booking management |
| 💳 **Payment Service** | 8003 | payment-db:5435 | Payment processing, transactions |

### 📡 API Endpoints

**Via API Gateway (Recommended):**
```
http://localhost:8080/api/v1/auth/*      # Authentication
http://localhost:8080/api/v1/users/*     # User management
http://localhost:8080/api/v1/events/*    # Event operations
http://localhost:8080/api/v1/bookings/*  # Booking operations
http://localhost:8080/api/v1/payments/*  # Payment operations
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

## 🔐 Security & Authentication

### 🛡️ Security Features
- **JWT Authentication**: Stateless token-based authentication
- **Role-based Access Control**: User/Admin role separation
- **Centralized Authentication**: Token validation at API Gateway
- **Session Management**: Active session tracking
- **Database per Service**: Data isolation between services

### 👑 Default Admin Access
```
Email: admin@eventix.com
Password: admin123
```
*The admin user is automatically created when the user service starts.*

---

## 🗄️ Database Architecture

### 📊 Database Per Service Pattern
Each microservice maintains its own PostgreSQL database for data independence:

| Database | Port | Service | Purpose |
|----------|------|---------|---------|
| **user-db** | 5432 | User Service | Users, profiles, sessions |
| **event-db** | 5433 | Event Service | Events, venues, seats |
| **booking-db** | 5434 | Booking Service | Bookings, reservations |
| **payment-db** | 5435 | Payment Service | Payments, transactions |

### 🔄 Data Consistency Patterns
- **Event Sourcing**: All state changes captured as events
- **Saga Pattern**: Distributed transaction coordination
- **Eventual Consistency**: Cross-service data synchronization via events
- **Message Queue**: RabbitMQ for reliable inter-service communication

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

---

## Troubleshooting

- Ensure Docker containers are running before running the app.
<!-- - If you see `KeyError: 'USER_DB_URL'`, check your `.env` file and environment variable setup. -->

---