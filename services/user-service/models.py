from sqlalchemy import String
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as SQLEnum
import uuid
from datetime import datetime
from enum import Enum


Base = declarative_base()

class NotificationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class NotificationType(str, Enum):
    BOOKING_CONFIRMATION = "booking_confirmation"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILED = "payment_failed"
    EVENT_REMINDER = "event_reminder"
    EVENT_CANCELLED = "event_cancelled"
    EVENT_UPDATED = "event_updated"
    BOOKING_CANCELLED = "booking_cancelled"
    REFUND_PROCESSED = "refund_processed"
    PROMOTIONAL = "promotional"
    SYSTEM = "system"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"


class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)  # e.g., "admin", "user"
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    phone_number = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)

    profile = relationship("UserProfile", uselist=False, back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", uselist=False, back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date_of_birth = Column(DateTime, nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="profile")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="refresh_tokens")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(500), nullable=False, unique=True, index=True)
    device_info = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Support both IPv4 and IPv6
    user_agent = Column(Text, nullable=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_accessed = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    # Indexes
    __table_args__ = (
        Index('idx_user_sessions_user_expires', 'user_id', 'expires_at'),
        Index('idx_user_sessions_token_active', 'session_token', 'is_active'),
    )


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    
    # Notification Preferences
    email_notifications = Column(Boolean, default=True, nullable=False)
    sms_notifications = Column(Boolean, default=False, nullable=False)
    push_notifications = Column(Boolean, default=True, nullable=False)
    in_app_notifications = Column(Boolean, default=True, nullable=False)
    
    # Marketing Preferences
    marketing_emails = Column(Boolean, default=False, nullable=False)
    promotional_sms = Column(Boolean, default=False, nullable=False)
    
    # Event Preferences
    event_reminders = Column(Boolean, default=True, nullable=False)
    booking_updates = Column(Boolean, default=True, nullable=False)
    payment_alerts = Column(Boolean, default=True, nullable=False)
    
    # Localization
    preferred_language = Column(String(10), default='en', nullable=False)
    timezone = Column(String(50), default='UTC', nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    
    # Privacy Settings
    profile_visibility = Column(String(20), default='private', nullable=False)  # public, private, friends
    data_sharing_consent = Column(Boolean, default=False, nullable=False)
    
    # Additional preferences as JSON
    custom_preferences = Column(JSONB, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="preferences")


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Notification Content
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status and Delivery
    status = Column(SQLEnum(NotificationStatus), default=NotificationStatus.PENDING, nullable=False, index=True)
    
    # Related Data
    related_entity_type = Column(String(50), nullable=True)  # 'booking', 'event', 'payment'
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)  # ID from other services
    
    # Metadata and Context
    notification_metadata = Column(JSONB, nullable=True)  # Additional data like booking_id, event_id, etc.
    action_url = Column(String(500), nullable=True)  # Deep link or URL for action
    
    # Scheduling and Delivery
    scheduled_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    
    # Retry Logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime, nullable=True)
    
    # External Service Data
    external_id = Column(String(200), nullable=True)  # ID from email/SMS provider
    external_response = Column(JSONB, nullable=True)  # Response from external service
    
    # Priority and Grouping
    priority = Column(String(10), default='normal', nullable=False)  # high, normal, low
    group_key = Column(String(100), nullable=True)  # For grouping related notifications
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="notifications")

    # Indexes
    __table_args__ = (
        Index('idx_notifications_user_status', 'user_id', 'status'),
        Index('idx_notifications_type_channel', 'type', 'channel'),
        Index('idx_notifications_scheduled_status', 'scheduled_at', 'status'),
        Index('idx_notifications_retry', 'next_retry_at', 'retry_count'),
        Index('idx_notifications_related_entity', 'related_entity_type', 'related_entity_id'),
    )


class NotificationTemplate(Base):
    __tablename__ = "notification_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Template Identity
    name = Column(String(100), nullable=False, unique=True, index=True)
    type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    channel = Column(SQLEnum(NotificationChannel), nullable=False, index=True)
    
    # Template Content
    subject_template = Column(String(200), nullable=True)  # For email
    title_template = Column(String(200), nullable=False)
    body_template = Column(Text, nullable=False)
    
    # Template Configuration
    variables = Column(JSONB, nullable=True)  # Available template variables
    default_values = Column(JSONB, nullable=True)  # Default values for variables
    
    # Localization
    language = Column(String(10), default='en', nullable=False)
    
    # Template Settings
    is_active = Column(Boolean, default=True, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    
    # Styling (for email templates)
    html_template = Column(Text, nullable=True)  # HTML version for emails
    css_styles = Column(Text, nullable=True)  # CSS styles for HTML emails
    
    # Usage Tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    tags = Column(JSONB, nullable=True)  # Array of tags for organization
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)  # Admin user ID who created template

    # Indexes
    __table_args__ = (
        Index('idx_notification_templates_type_channel', 'type', 'channel'),
        Index('idx_notification_templates_active', 'is_active', 'language'),
        Index('idx_notification_templates_name_version', 'name', 'version'),
    )