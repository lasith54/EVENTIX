import bcrypt
from sqlalchemy.orm import Session
from models import User, Base

def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    hashed_bytes = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_bytes.decode('utf-8')

def create_admin_user(db: Session, admin_email: str, admin_password: str, admin_first_name: str, admin_last_name: str):
    """
    Creates an admin user if one does not already exist.
    """
    # Check if admin user already exists
    existing_admin = db.query(User).filter(User.email == admin_email).first()
    if existing_admin:
        print(f"Admin user with email '{admin_email}' already exists. Skipping creation.")
        return

    # Hash the password
    hashed_admin_password = hash_password(admin_password)

    # Create the new User object
    admin_user = User(
        email=admin_email,
        first_name=admin_first_name,
        last_name=admin_last_name,
        hashed_password=hashed_admin_password,
        role="admin",  # Set the role to 'admin'
        is_active=True,
        is_verified=True, # Admins should be verified by default
    )
    
    # Add the user to the session and commit
    db.add(admin_user)
    db.commit()
    print(f"Admin user with email '{admin_email}' created successfully.")