import sys
import os
from datetime import datetime

base_dir = os.path.dirname(os.path.abspath(__file__))
services_dir = os.path.join(base_dir, '..', 'services')

# Add each service directory to Python path
service_names = ['user_service', 'event_service', 'booking_service', 'payment_service']
for service_name in service_names:
    service_path = os.path.join(services_dir, service_name)
    if os.path.exists(service_path) and service_path not in sys.path:
        sys.path.insert(0, service_path)

# Import individual seeding functions
from seed_user_data import seed_user_service
from seed_event_data import seed_event_service
from seed_booking_data import seed_booking_service
from seed_payment_data import seed_payment_service

def main():
    """Master function to seed all services in correct order."""
    print("🌱 Starting database seeding for all services...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    try:
        # Seed services in order (due to dependencies)
        print("1️⃣ Seeding user service...")
        user_ids = seed_user_service()
        
        if not user_ids:
            print("❌ Failed to seed user service. Stopping.")
            return
        
        print("2️⃣ Seeding event service...")
        event_data = seed_event_service()
        
        if not event_data:
            print("❌ Failed to seed event service. Stopping.")
            return
        
        print("3️⃣ Seeding booking service...")
        booking_ids = seed_booking_service(user_ids, event_data)
        
        if not booking_ids:
            print("❌ Failed to seed booking service. Stopping.")
            return
        
        print("4️⃣ Seeding payment service...")
        seed_payment_service(user_ids, booking_ids)
        
        print("-" * 60)
        print("🎉 Database seeding completed successfully!")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Summary
        print("\n📊 Seeding Summary:")
        print(f"  • Users created: {len(user_ids)}")
        print(f"  • Events created: 1")
        print(f"  • Venues created: 1") 
        print(f"  • Bookings created: {len(booking_ids)}")
        print(f"  • Payment methods created: {len(booking_ids)}")
        
    except Exception as e:
        print(f"💥 Critical error during seeding: {e}")
        return

if __name__ == "__main__":
    main()