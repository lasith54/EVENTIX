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
from services.user_service.models import (
    User, UserProfile, RefreshToken, UserSession, UserPreferences, 
    Notification, NotificationTemplate, NotificationStatus, 
    NotificationType, NotificationChannel
)

# Database configurations
DATABASE_URL = 'postgresql+psycopg2://postgres:postgres@localhost:5432/user-db'

def get_session(service_name):
    """Create database session for specific service."""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def seed_user_service():
    """Add sample data to user service."""
    session = get_session('user')
    
    try:
        # Create sample users
        users_data = [
            {
                'email': 'john.doe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'hashed_password': 'hashed_password_123',
                'role': 'user',
                'is_active': True,
                'is_verified': True,
                'phone_number': '+1234567890'
            },
            {
                'email': 'jane.smith@example.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'hashed_password': 'hashed_password_456',
                'role': 'admin',
                'is_active': True,
                'is_verified': True,
                'phone_number': '+1234567891'
            }
        ]
        
        users = []
        for user_data in users_data:
            user = User(**user_data)
            users.append(user)
            session.add(user)
        
        session.flush()
        
        # Create user profiles
        for i, user in enumerate(users):
            profile = UserProfile(
                user_id=user.id,
                bio=f"Bio for {user.first_name} {user.last_name}",
                avatar_url=f"https://example.com/avatar_{i+1}.jpg"
            )
            session.add(profile)
            
            # Create user preferences
            preferences = UserPreferences(
                user_id=user.id,
                email_notifications=True,
                sms_notifications=False,
                push_notifications=True,
                marketing_emails=True,
                preferred_language='en',
                timezone='UTC',
                currency='USD'
            )
            session.add(preferences)
            
            # Create notifications
            notification = Notification(
                user_id=user.id,
                type=NotificationType.BOOKING_CONFIRMATION,
                title="Welcome to Eventix!",
                message="Your account has been created successfully.",
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT
            )
            session.add(notification)
        
        session.commit()
        print("✓ User service data seeded successfully")
        return [user.id for user in users]
        
    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding user service: {e}")
        return []
    finally:
        session.close()