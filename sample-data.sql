-- sample-data.sql
-- Sample data for testing and demonstration

-- Insert sample venues
INSERT INTO events.venues (name, address, city, country, capacity, facilities) VALUES
('Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'USA', 20000, '{"parking": true, "restaurant": true, "accessibility": true, "vip_lounge": true}'),
('Wembley Stadium', 'Wembley', 'London', 'UK', 90000, '{"parking": true, "restaurant": true, "accessibility": true, "retail": true}'),
('Sydney Opera House', 'Bennelong Point', 'Sydney', 'Australia', 2679, '{"parking": false, "restaurant": true, "accessibility": true, "harbor_view": true}'),
('Red Rocks Amphitheatre', '18300 W Alameda Pkwy', 'Morrison', 'USA', 9525, '{"parking": true, "accessibility": true, "outdoor": true, "scenic": true}'),
('Royal Albert Hall', 'Kensington Gore', 'London', 'UK', 5272, '{"parking": false, "restaurant": true, "accessibility": true, "historic": true}')
ON CONFLICT DO NOTHING;

-- Insert seat sections for venues
INSERT INTO events.seat_sections (venue_id, section_name, seat_count, price_multiplier) VALUES
-- Madison Square Garden
(1, 'VIP Floor', 200, 3.00),
(1, 'Lower Bowl', 5000, 2.00),
(1, 'Upper Bowl', 10000, 1.50),
(1, 'Nosebleeds', 4800, 1.00),

-- Wembley Stadium
(2, 'Club Wembley', 500, 4.00),
(2, 'Lower Tier', 30000, 2.50),
(2, 'Upper Tier', 40000, 1.80),
(2, 'General Admission', 19500, 1.00),

-- Sydney Opera House
(3, 'Orchestra', 500, 2.50),
(3, 'Circle', 800, 2.00),
(3, 'Upper Circle', 700, 1.50),
(3, 'Gallery', 679, 1.00),

-- Red Rocks Amphitheatre
(4, 'Reserved Seating', 2000, 2.00),
(4, 'General Admission', 7525, 1.00),

-- Royal Albert Hall
(5, 'Stalls', 1000, 2.50),
(5, 'Dress Circle', 1200, 2.00),
(5, 'Upper Circle', 1500, 1.50),
(5, 'Gallery', 1572, 1.00)
ON CONFLICT DO NOTHING;

-- Insert sample events
INSERT INTO events.events (title, description, venue_id, start_datetime, end_datetime, category, status, total_seats, available_seats, base_price, currency, image_url, tags) VALUES
('Rock Legends 2024', 'The biggest rock concert of the year featuring legendary bands', 1, '2024-12-31T20:00:00', '2024-12-31T23:59:00', 'Music', 'active', 20000, 18500, 75.00, 'USD', 'https://example.com/rock-legends.jpg', '["rock", "music", "live", "legendary"]'),

('Premier League Final', 'Championship final match of the season', 2, '2024-06-15T15:00:00', '2024-06-15T17:00:00', 'Sports', 'active', 90000, 45000, 120.00, 'GBP', 'https://example.com/premier-final.jpg', '["football", "sports", "championship", "final"]'),

('Classical Symphony Night', 'An evening of beautiful classical music', 3, '2024-08-20T19:30:00', '2024-08-20T22:00:00', 'Music', 'active', 2679, 2200, 85.00, 'AUD', 'https://example.com/symphony.jpg', '["classical", "music", "symphony", "opera house"]'),

('Indie Music Festival', 'Three days of the best indie music under the stars', 4, '2024-07-12T18:00:00', '2024-07-14T23:00:00', 'Music', 'active', 9525, 8000, 150.00, 'USD', 'https://example.com/indie-fest.jpg', '["indie", "festival", "outdoor", "multi-day"]'),

('Royal Philharmonic Orchestra', 'A spectacular evening with the Royal Philharmonic', 5, '2024-09-05T19:00:00', '2024-09-05T21:30:00', 'Music', 'active', 5272, 4800, 65.00, 'GBP', 'https://example.com/royal-phil.jpg', '["classical", "orchestra", "royal", "elegant"]'),

-- Past event for testing history
('Summer Music Festival 2023', 'Last summer amazing music festival', 4, '2023-07-15T18:00:00', '2023-07-17T23:00:00', 'Music', 'completed', 9525, 0, 100.00, 'USD', 'https://example.com/summer-2023.jpg', '["summer", "festival", "completed"]'),

-- Future events
('Tech Conference 2025', 'The biggest technology conference of the year', 1, '2025-03-15T09:00:00', '2025-03-17T18:00:00', 'Conference', 'active', 15000, 15000, 299.00, 'USD', 'https://example.com/tech-conf.jpg', '["technology", "conference", "innovation", "networking"]'),

('Broadway Musical Night', 'Best of Broadway performed live', 5, '2024-11-20T19:30:00', '2024-11-20T22:30:00', 'Theatre', 'active', 5272, 5000, 95.00, 'GBP', 'https://example.com/broadway.jpg', '["theatre", "musical", "broadway", "live"]')
ON CONFLICT DO NOTHING;

-- Generate seats for events (sample for first event)
DO $$
DECLARE
    event_rec RECORD;
    section_rec RECORD;
    seat_count INT;
    i INT;
    seat_price DECIMAL(10,2);
BEGIN
    -- Only generate seats for first event to avoid too much data
    FOR event_rec IN SELECT * FROM events.events WHERE id = 1 LOOP
        FOR section_rec IN SELECT * FROM events.seat_sections WHERE venue_id = event_rec.venue_id LOOP
            seat_count := LEAST(section_rec.seat_count, 100); -- Limit to 100 seats per section for demo
            seat_price := event_rec.base_price * section_rec.price_multiplier;
            
            FOR i IN 1..seat_count LOOP
                INSERT INTO events.seats (event_id, section_id, seat_number, row_number, is_available, price)
                VALUES (
                    event_rec.id,
                    section_rec.id,
                    LPAD(i::text, 3, '0'),
                    CHR(65 + ((i-1) / 20)), -- Row A, B, C, etc.
                    true,
                    seat_price
                );
            END LOOP;
        END LOOP;
    END LOOP;
END $$;

-- Sample users (passwords are hashed for 'password123')
INSERT INTO users.users (email, password_hash, first_name, last_name, phone, is_active, is_admin) VALUES
('john.doe@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/ZgCFhV9f7VMLVFz2S', 'John', 'Doe', '+1234567890', true, false),
('jane.smith@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/ZgCFhV9f7VMLVFz2S', 'Jane', 'Smith', '+1234567891', true, false),
('bob.wilson@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/ZgCFhV9f7VMLVFz2S', 'Bob', 'Wilson', '+1234567892', true, false),
('alice.johnson@example.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/ZgCFhV9f7VMLVFz2S', 'Alice', 'Johnson', '+1234567893', true, false),
('manager@eventix.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/ZgCFhV9f7VMLVFz2S', 'Event', 'Manager', '+1234567894', true, true)
ON CONFLICT (email) DO NOTHING;

-- Sample user profiles
INSERT INTO users.user_profiles (user_id, date_of_birth, gender, address, city, country, postal_code, preferences) VALUES
(2, '1990-05-15', 'Male', '123 Main Street', 'New York', 'USA', '10001', '{"music_genres": ["rock", "pop"], "notifications": {"email": true, "sms": false}}'),
(3, '1985-08-22', 'Female', '456 Oak Avenue', 'Los Angeles', 'USA', '90210', '{"music_genres": ["classical", "jazz"], "notifications": {"email": true, "sms": true}}'),
(4, '1992-12-03', 'Male', '789 Pine Road', 'Chicago', 'USA', '60601', '{"music_genres": ["indie", "electronic"], "notifications": {"email": false, "sms": true}}'),
(5, '1988-03-18', 'Female', '321 Elm Street', 'San Francisco', 'USA', '94102', '{"music_genres": ["pop", "rock", "indie"], "notifications": {"email": true, "sms": true}}')
ON CONFLICT DO NOTHING;

-- Sample bookings
INSERT INTO bookings.bookings (user_id, event_id, booking_reference, status, total_amount, currency, booking_date, expiry_date, notes) VALUES
(2, 1, 'BK20241201001', 'confirmed', 150.00, 'USD', '2024-11-01T10:00:00', '2024-11-01T10:15:00', 'Birthday celebration'),
(3, 1, 'BK20241201002', 'confirmed', 225.00, 'USD', '2024-11-02T14:30:00', '2024-11-02T14:45:00', 'Date night'),
(4, 2, 'BK20241201003', 'pending', 240.00, 'GBP', '2024-11-03T09:15:00', '2024-11-03T09:30:00', 'Football match with friends'),
(5, 3, 'BK20241201004', 'confirmed', 170.00, 'AUD', '2024-11-04T16:45:00', '2024-11-04T17:00:00', 'Classical music lover')
ON CONFLICT DO NOTHING;

-- Sample booking seats (assuming seats exist)
INSERT INTO bookings.booking_seats (booking_id, seat_id, price) 
SELECT 1, s.id, s.price 
FROM events.seats s 
WHERE s.event_id = 1 AND s.section_id = 1 
LIMIT 2
ON CONFLICT DO NOTHING;

INSERT INTO bookings.booking_seats (booking_id, seat_id, price) 
SELECT 2, s.id, s.price 
FROM events.seats s 
WHERE s.event_id = 1 AND s.section_id = 2 
LIMIT 3
ON CONFLICT DO NOTHING;

-- Sample payments
INSERT INTO payments.payments (booking_id, user_id, amount, currency, payment_method, payment_gateway, gateway_transaction_id, status, payment_date, metadata) VALUES
(1, 2, 150.00, 'USD', 'credit_card', 'stripe', 'pi_1234567890abcdef', 'completed', '2024-11-01T10:05:00', '{"card_last4": "4242", "card_brand": "visa"}'),
(2, 3, 225.00, 'USD', 'credit_card', 'stripe', 'pi_0987654321fedcba', 'completed', '2024-11-02T14:35:00', '{"card_last4": "5555", "card_brand": "mastercard"}'),
(4, 5, 170.00, 'AUD', 'paypal', 'paypal', 'PAY-12345678901234567', 'completed', '2024-11-04T16:50:00', '{"paypal_email": "alice.johnson@example.com"}')
ON CONFLICT DO NOTHING;

-- Update available seats count for events with bookings
UPDATE events.events 
SET available_seats = total_seats - (
    SELECT COUNT(bs.seat_id) 
    FROM bookings.bookings b 
    JOIN bookings.booking_seats bs ON b.id = bs.booking_id 
    WHERE b.event_id = events.events.id AND b.status = 'confirmed'
)
WHERE id IN (1, 2, 3);

-- Sample system logs
INSERT INTO system_logs (service_name, log_level, message, metadata) VALUES
('user-service', 'INFO', 'User authentication successful', '{"user_id": 2, "ip": "192.168.1.100"}'),
('booking-service', 'INFO', 'Booking created successfully', '{"booking_id": 1, "user_id": 2, "event_id": 1}'),
('payment-service', 'INFO', 'Payment processed successfully', '{"payment_id": 1, "amount": 150.00, "gateway": "stripe"}'),
('api-gateway', 'WARNING', 'Rate limit approached for user', '{"user_id": 3, "endpoint": "/api/v1/events/", "requests": 95}'),
('event-service', 'INFO', 'Event created', '{"event_id": 8, "title": "Broadway Musical Night"}')
ON CONFLICT DO NOTHING;

-- Sample API metrics
INSERT INTO api_metrics (endpoint, method, response_time_ms, status_code, user_id, timestamp) VALUES
('/api/v1/events/', 'GET', 120, 200, NULL, '2024-11-01T10:00:00'),
('/api/v1/auth/login', 'POST', 250, 200, 2, '2024-11-01T09:58:00'),
('/api/v1/bookings/', 'POST', 450, 201, 2, '2024-11-01T10:00:30'),
('/api/v1/payments/', 'POST', 1200, 201, 2, '2024-11-01T10:05:00'),
('/api/v1/events/1', 'GET', 80, 200, 3, '2024-11-02T14:00:00'),
('/api/v1/bookings/', 'POST', 380, 201, 3, '2024-11-02T14:30:00'),
('/health', 'GET', 15, 200, NULL, '2024-11-05T12:00:00')
ON CONFLICT DO NOTHING;

-- Create some active seat reservations for demonstration
INSERT INTO bookings.seat_reservations (user_id, seat_id, reserved_until, status)
SELECT 
    4,
    s.id,
    NOW() + INTERVAL '10 minutes',
    'reserved'
FROM events.seats s 
WHERE s.event_id = 1 AND s.is_available = true
LIMIT 2
ON CONFLICT DO NOTHING;