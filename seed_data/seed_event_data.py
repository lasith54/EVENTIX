import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from decimal import Decimal
import uuid
import enum

# Add paths for each service
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import models from each service
from services.event_service.models import (
    Venue, VenueSection, EventCategory, Event, EventSchedule, 
    EventPricingTier, Seat, SeatReservation, VenueType, 
    EventType, EventStatus, SeatType, SeatStatus, ReservationStatus
)

# Database configurations
DATABASE_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5433/event-db'

def get_session(service_name):
    """Create database session for specific service."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def seed_event_service():
    """Add sample data to event service."""
    session = get_session('event')
    
    try:
        # Create sample venues
        venue = Venue(
            name="Madison Square Garden",
            description="Famous arena in New York City",
            venue_type=VenueType.ARENA,
            address="4 Pennsylvania Plaza",
            city="New York",
            state="NY",
            country="USA",
            postal_code="10001",
            capacity=20000,
            amenities=["parking", "wheelchair_access", "food_court"],
            contact_info={"phone": "+1234567890", "email": "info@msg.com"}
        )
        session.add(venue)
        session.flush()
        
        # Create venue sections
        sections = [
            VenueSection(
                venue_id=venue.id,
                name="Floor",
                capacity=5000,
                seat_map={"rows": 50, "seats_per_row": 100}
            ),
            VenueSection(
                venue_id=venue.id,
                name="Lower Bowl",
                capacity=8000,
                seat_map={"rows": 40, "seats_per_row": 200}
            ),
            VenueSection(
                venue_id=venue.id,
                name="Upper Bowl",
                capacity=7000,
                seat_map={"rows": 35, "seats_per_row": 200}
            )
        ]
        session.add_all(sections)
        session.flush()
        
        # Create event category
        category = EventCategory(
            name="Concerts",
            description="Musical performances and concerts"
        )
        session.add(category)
        session.flush()
        
        # Create sample event
        event = Event(
            title="Rock Concert 2024",
            description="Amazing rock concert featuring top artists",
            short_description="Don't miss this incredible rock concert!",
            event_type=EventType.CONCERT,
            status=EventStatus.PUBLISHED,
            venue_id=venue.id,
            category_id=category.id
        )
        session.add(event)
        session.flush()

        start_datetime = datetime.now() + timedelta(days=30)  # Event in 30 days
        end_datetime = start_datetime + timedelta(hours=3)
        
        # Create event schedule
        schedule = EventSchedule(
            event_id=event.id,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            doors_open_time=start_datetime - timedelta(hours=1)
        )
        session.add(schedule)
        
        # Create pricing tiers
        pricing_tiers = [
            EventPricingTier(
                event_id=event.id,
                venue_section_id=sections[0].id,
                tier_name="Floor - General",
                price=Decimal("150.00"),
                currency="USD",
                total_seats=5000,
                available_seats=5000
            ),
            EventPricingTier(
                event_id=event.id,
                venue_section_id=sections[1].id,
                tier_name="Lower Bowl",
                price=Decimal("100.00"),
                currency="USD",
                total_seats=5000,
                available_seats=8000
            ),
            EventPricingTier(
                event_id=event.id,
                venue_section_id=sections[2].id,
                tier_name="Upper Bowl",
                price=Decimal("75.00"),
                currency="USD",
                total_seats=5000,
                available_seats=7000
            )
        ]
        session.add_all(pricing_tiers)
        
        # Create sample seats
        for i, section in enumerate(sections[:2]):  # Create seats for first 2 sections only
            for row in range(1, 6):  # 5 rows per section
                for seat_num in range(1, 11):  # 10 seats per row
                    seat = Seat(
                        venue_section_id=section.id,
                        row_number=f"Row {row}",
                        seat_number=str(seat_num),
                        seat_type=SeatType.REGULAR,
                        status=SeatStatus.AVAILABLE
                    )
                    session.add(seat)
        
        session.commit()
        print("✓ Event service data seeded successfully")
        return {
            'event_id': event.id,
            'venue_id': venue.id,
            'section_ids': [s.id for s in sections]
        }
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding event service: {e}")
        return {}
    finally:
        session.close()
