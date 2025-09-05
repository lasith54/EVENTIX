-- Create schemas for better organization
CREATE SCHEMA IF NOT EXISTS users;
CREATE SCHEMA IF NOT EXISTS events;
CREATE SCHEMA IF NOT EXISTS bookings;
CREATE SCHEMA IF NOT EXISTS payments;

-- Users Schema Tables
CREATE TABLE IF NOT EXISTS users.users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users.user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users.users(id) ON DELETE CASCADE,
    date_of_birth DATE,
    gender VARCHAR(10),
    address TEXT,
    city VARCHAR(100),
    country VARCHAR(100),
    postal_code VARCHAR(20),
    preferences JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users.user_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users.users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- Events Schema Tables
CREATE TABLE IF NOT EXISTS events.venues (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    address TEXT NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL,
    capacity INTEGER NOT NULL,
    facilities JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events.events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    venue_id INTEGER REFERENCES events.venues(id),
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    total_seats INTEGER NOT NULL,
    available_seats INTEGER NOT NULL,
    base_price DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    image_url TEXT,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events.seat_sections (
    id SERIAL PRIMARY KEY,
    venue_id INTEGER REFERENCES events.venues(id),
    section_name VARCHAR(100) NOT NULL,
    seat_count INTEGER NOT NULL,
    price_multiplier DECIMAL(3, 2) DEFAULT 1.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events.seats (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events.events(id),
    section_id INTEGER REFERENCES events.seat_sections(id),
    seat_number VARCHAR(20) NOT NULL,
    row_number VARCHAR(10),
    is_available BOOLEAN DEFAULT true,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(event_id, section_id, seat_number)
);

-- Bookings Schema Tables
CREATE TABLE IF NOT EXISTS bookings.bookings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users.users(id),
    event_id INTEGER REFERENCES events.events(id),
    booking_reference VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    total_amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expiry_date TIMESTAMP,
    payment_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings.booking_seats (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings.bookings(id) ON DELETE CASCADE,
    seat_id INTEGER REFERENCES events.seats(id),
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookings.seat_reservations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users.users(id),
    seat_id INTEGER REFERENCES events.seats(id),
    booking_id INTEGER REFERENCES bookings.bookings(id),
    reserved_until TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'reserved',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(seat_id, status) -- Prevent double reservation
);

-- Payments Schema Tables
CREATE TABLE IF NOT EXISTS payments.payments (
    id SERIAL PRIMARY KEY,
    booking_id INTEGER REFERENCES bookings.bookings(id),
    user_id INTEGER REFERENCES users.users(id),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    payment_gateway VARCHAR(50),
    gateway_transaction_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    payment_date TIMESTAMP,
    failure_reason TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS payments.refunds (
    id SERIAL PRIMARY KEY,
    payment_id INTEGER REFERENCES payments.payments(id),
    booking_id INTEGER REFERENCES bookings.bookings(id),
    amount DECIMAL(10, 2) NOT NULL,
    reason TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    gateway_refund_id VARCHAR(255),
    processed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Tables for Monitoring and Auditing
CREATE TABLE IF NOT EXISTS system_logs (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100),
    log_level VARCHAR(20),
    message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS api_metrics (
    id SERIAL PRIMARY KEY,
    endpoint VARCHAR(255),
    method VARCHAR(10),
    response_time_ms INTEGER,
    status_code INTEGER,
    user_id INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users.users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users.users(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON users.user_sessions(token_hash);
CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON users.user_sessions(is_active, expires_at);

CREATE INDEX IF NOT EXISTS idx_events_status ON events.events(status);
CREATE INDEX IF NOT EXISTS idx_events_datetime ON events.events(start_datetime, end_datetime);
CREATE INDEX IF NOT EXISTS idx_events_category ON events.events(category);
CREATE INDEX IF NOT EXISTS idx_seats_event_available ON events.seats(event_id, is_available);

CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings.bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_event ON bookings.bookings(event_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings.bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_reference ON bookings.bookings(booking_reference);
CREATE INDEX IF NOT EXISTS idx_reservations_expiry ON bookings.seat_reservations(reserved_until, status);

CREATE INDEX IF NOT EXISTS idx_payments_booking ON payments.payments(booking_id);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments.payments(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments.payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_gateway ON payments.payments(payment_gateway, gateway_transaction_id);

CREATE INDEX IF NOT EXISTS idx_system_logs_service ON system_logs(service_name, log_level);
CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint ON api_metrics(endpoint, timestamp);

-- Insert Sample Data
INSERT INTO users.users (email, password_hash, first_name, last_name, is_admin) 
VALUES ('admin@eventix.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/ZgCFhV9f7VMLVFz2S', 'Admin', 'User', true)
ON CONFLICT (email) DO NOTHING;

INSERT INTO events.venues (name, address, city, country, capacity, facilities)
VALUES 
    ('Grand Concert Hall', '123 Music Street', 'New York', 'USA', 2000, '{"parking": true, "restaurant": true, "accessibility": true}'),
    ('Sports Arena', '456 Stadium Ave', 'Los Angeles', 'USA', 5000, '{"parking": true, "concessions": true, "vip_lounge": true}'),
    ('Theater District', '789 Broadway', 'New York', 'USA', 800, '{"coat_check": true, "bar": true, "accessibility": true}')
ON CONFLICT DO NOTHING;

INSERT INTO events.seat_sections (venue_id, section_name, seat_count, price_multiplier)
VALUES 
    (1, 'VIP', 100, 2.00),
    (1, 'Premium', 300, 1.50),
    (1, 'Standard', 1600, 1.00),
    (2, 'Court Side', 50, 3.00),
    (2, 'Lower Bowl', 1000, 2.00),
    (2, 'Upper Bowl', 3950, 1.00),
    (3, 'Orchestra', 200, 1.80),
    (3, 'Mezzanine', 300, 1.40),
    (3, 'Balcony', 300, 1.00)
ON CONFLICT DO NOTHING;

-- Trigger for updating timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users.users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON users.user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events.events FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON bookings.bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments.payments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_refunds_updated_at BEFORE UPDATE ON payments.refunds FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();