# import sys
# import os
# sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# from datetime import datetime, timedelta
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, update
# from models import Payment, PaymentMethod, UserPaymentProfile, FraudAlert
# from database import get_async_db
# from shared.event_publisher import EventPublisher
# import logging

# logger = logging.getLogger(__name__)

# class PaymentServiceUserHandler:
#     def __init__(self):
#         self.event_publisher = EventPublisher("payment-service")
        
#     async def handle_user_event(self, event_data):
#         """Handle incoming user service events"""
#         event_type = event_data.get("event_type")
#         data = event_data.get("data", {})
        
#         logger.info(f"Payment service received user event: {event_type}")
        
#         try:
#             if event_type == "created":
#                 await self._handle_user_registration(data)
#             elif event_type == "login_successful":
#                 await self._handle_user_login(data)
#             elif event_type == "login_failed":
#                 await self._handle_failed_login(data)
#             elif event_type == "password_changed":
#                 await self._handle_password_change(data)
#             elif event_type == "account_deactivated":
#                 await self._handle_account_deactivation(data)
#             elif event_type == "session_revoked" or event_type == "sessions_bulk_revoked":
#                 await self._handle_session_security_event(data)
#             elif event_type == "profile_updated":
#                 await self._handle_profile_update(data)
                
#         except Exception as e:
#             logger.error(f"Error handling user event {event_type}: {str(e)}")

#     async def _handle_user_registration(self, data):
#         """When new user registers, create payment profile"""
#         user_id = data.get("user_id")
#         email = data.get("email")
        
#         async with get_async_db() as db:
#             # Create user payment profile with security settings
#             payment_profile = UserPaymentProfile(
#                 user_id=user_id,
#                 security_settings={
#                     "require_cvv": True,
#                     "enable_3d_secure": True,
#                     "fraud_protection": True,
#                     "max_daily_limit": 1000,
#                     "max_transaction_limit": 500
#                 },
#                 preferences={
#                     "default_currency": "USD",
#                     "save_payment_methods": True,
#                     "email_receipts": True,
#                     "sms_notifications": False
#                 },
#                 risk_score=0.1,  # New users start with low risk
#                 created_at=datetime.utcnow()
#             )
            
#             db.add(payment_profile)
#             await db.commit()
            
#             # Publish payment profile creation
#             await self.event_publisher.publish_payment_event("user_profile_created", {
#                 "user_id": user_id,
#                 "email": email,
#                 "payment_profile_created": True,
#                 "initial_risk_score": 0.1,
#                 "security_settings_applied": True,
#                 "timestamp": datetime.utcnow().isoformat()
#             })
            
#             logger.info(f"Created payment profile for user {user_id}")

#     async def _handle_user_login(self, data):
#         """When user logs in, check for payment security and pending transactions"""
#         user_id = data.get("user_id")
#         email = data.get("email")
#         last_login = data.get("last_login")
        
#         async with get_async_db() as db:
#             # Check for pending payments that might need attention
#             pending_payments = await db.execute(
#                 select(Payment)
#                 .where(Payment.user_id == user_id)
#                 .where(Payment.status == "pending")
#                 .where(Payment.created_at > datetime.utcnow() - timedelta(hours=24))
#             )
            
#             payments = pending_payments.scalars().all()
            
#             if payments:
#                 # Notify about pending payments
#                 await self.event_publisher.publish_payment_event("pending_payments_alert", {
#                     "user_id": user_id,
#                     "email": email,
#                     "pending_payments_count": len(payments),
#                     "payment_ids": [str(p.id) for p in payments],
#                     "total_pending_amount": sum(p.amount for p in payments),
#                     "timestamp": datetime.utcnow().isoformat()
#                 })
            
#             # Update login tracking for fraud detection
#             await self._update_login_pattern(user_id, data, db)

#     async def _handle_failed_login(self, data):
#         """When login fails, increase fraud monitoring"""
#         email = data.get("email")
#         reason = data.get("reason")
        
#         async with get_async_db() as db:
#             # Check if we have a user with this email
#             user_result = await db.execute(
#                 select(UserPaymentProfile).join(User).where(User.email == email)
#             )
#             profile = user_result.scalar_one_or_none()
            
#             if profile:
#                 # Increase risk score for failed login attempts
#                 current_risk = profile.risk_score or 0
#                 profile.risk_score = min(current_risk + 0.1, 1.0)
                
#                 # Create fraud alert if multiple failures
#                 failed_attempts = await self._count_recent_failed_attempts(email, db)
                
#                 if failed_attempts >= 3:
#                     fraud_alert = FraudAlert(
#                         user_id=profile.user_id,
#                         alert_type="multiple_failed_logins",
#                         risk_level="medium",
#                         details={
#                             "email": email,
#                             "failed_attempts": failed_attempts,
#                             "reason": reason
#                         },
#                         created_at=datetime.utcnow()
#                     )
#                     db.add(fraud_alert)
                
#                 await db.commit()
                
#                 # Publish fraud alert
#                 await self.event_publisher.publish_payment_event("fraud_alert_created", {
#                     "user_id": str(profile.user_id),
#                     "email": email,
#                     "alert_type": "failed_login_attempts",
#                     "failed_attempts": failed_attempts,
#                     "new_risk_score": profile.risk_score,
#                     "timestamp": datetime.utcnow().isoformat()
#                 })

#     async def _handle_password_change(self, data):
#         """When password changes, enhance payment security temporarily"""
#         user_id = data.get("user_id")
#         email = data.get("email")
        
#         async with get_async_db() as db:
#             # Get payment profile
#             profile_result = await db.execute(
#                 select(UserPaymentProfile).where(UserPaymentProfile.user_id == user_id)
#             )
#             profile = profile_result.scalar_one_or_none()
            
#             if profile:
#                 # Temporarily increase security requirements
#                 security_settings = profile.security_settings or {}
                
#                 # Enable enhanced security for 24 hours
#                 security_settings.update({
#                     "enhanced_verification": True,
#                     "enhanced_until": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
#                     "require_cvv": True,
#                     "max_transaction_limit": min(security_settings.get("max_transaction_limit", 500), 200)
#                 })
                
#                 profile.security_settings = security_settings
#                 profile.updated_at = datetime.utcnow()
#                 await db.commit()
                
#                 # Publish security enhancement
#                 await self.event_publisher.publish_payment_event("security_enhanced", {
#                     "user_id": user_id,
#                     "email": email,
#                     "reason": "password_change",
#                     "enhanced_security_duration": "24_hours",
#                     "reduced_transaction_limit": True,
#                     "timestamp": datetime.utcnow().isoformat()
#                 })

#     async def _handle_account_deactivation(self, data):
#         """When account is deactivated, secure payment data"""
#         user_id = data.get("user_id")
#         email = data.get("email")
        
#         async with get_async_db() as db:
#             # Cancel any pending payments
#             pending_payments = await db.execute(
#                 select(Payment)
#                 .where(Payment.user_id == user_id)
#                 .where(Payment.status.in_(["pending", "processing"]))
#             )
            
#             payments = pending_payments.scalars().all()
#             cancelled_payments = []
            
#             for payment in payments:
#                 payment.status = "cancelled_by_deactivation"
#                 payment.cancelled_at = datetime.utcnow()
#                 cancelled_payments.append(str(payment.id))
            
#             # Archive payment methods (don't delete for audit purposes)
#             await db.execute(
#                 update(PaymentMethod)
#                 .where(PaymentMethod.user_id == user_id)
#                 .values(is_active=False, archived_at=datetime.utcnow())
#             )
            
#             # Archive payment profile
#             await db.execute(
#                 update(UserPaymentProfile)
#                 .where(UserPaymentProfile.user_id == user_id)
#                 .values(is_active=False, deactivated_at=datetime.utcnow())
#             )
            
#             await db.commit()
            
#             # Publish deactivation handling
#             await self.event_publisher.publish_payment_event("account_deactivation_handled", {
#                 "user_id": user_id,
#                 "email": email,
#                 "cancelled_payments": cancelled_payments,
#                 "payment_methods_archived": True,
#                 "profile_archived": True,
#                 "timestamp": datetime.utcnow().isoformat()
#             })

#     async def _handle_session_security_event(self, data):
#         """When sessions are revoked, check for payment security implications"""
#         user_id = data.get("user_id")
#         revoked_count = data.get("revoked_sessions_count", 1)
        
#         # If multiple sessions were revoked, it might indicate security compromise
#         if revoked_count >= 3:
#             async with get_async_db() as db:
#                 # Temporarily freeze high-value transactions
#                 profile_result = await db.execute(
#                     select(UserPaymentProfile).where(UserPaymentProfile.user_id == user_id)
#                 )
#                 profile = profile_result.scalar_one_or_none()
                
#                 if profile:
#                     security_settings = profile.security_settings or {}
#                     security_settings.update({
#                         "temporary_freeze": True,
#                         "freeze_until": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
#                         "max_transaction_limit": 50  # Very low limit temporarily
#                     })
                    
#                     profile.security_settings = security_settings
#                     await db.commit()
                    
#                     # Publish security freeze
#                     await self.event_publisher.publish_payment_event("temporary_payment_freeze", {
#                         "user_id": user_id,
#                         "reason": "bulk_session_revocation",
#                         "freeze_duration": "2_hours",
#                         "revoked_sessions": revoked_count,
#                         "timestamp": datetime.utcnow().isoformat()
#                     })

#     async def _handle_profile_update(self, data):
#         """When user profile is updated, update payment profile accordingly"""
#         user_id = data.get("user_id")
#         updated_fields = data.get("updated_fields", [])
#         new_data = data.get("new_data", {})
        
#         # Check if contact or billing information was updated
#         billing_fields = ["email", "phone_number", "first_name", "last_name"]
#         if any(field in updated_fields for field in billing_fields):
#             async with get_async_db() as db:
#                 # Update billing information in payment profile
#                 profile_result = await db.execute(
#                     select(UserPaymentProfile).where(UserPaymentProfile.user_id == user_id)
#                 )
#                 profile = profile_result.scalar_one_or_none()
                
#                 if profile:
#                     billing_info = profile.billing_info or {}
                    
#                     for field in billing_fields:
#                         if field in new_data:
#                             billing_info[field] = new_data[field]
                    
#                     profile.billing_info = billing_info
#                     profile.updated_at = datetime.utcnow()
#                     await db.commit()
                    
#                     # Publish billing update
#                     await self.event_publisher.publish_payment_event("billing_info_updated", {
#                         "user_id": user_id,
#                         "updated_fields": [f for f in updated_fields if f in billing_fields],
#                         "timestamp": datetime.utcnow().isoformat()
#                     })

#     async def _update_login_pattern(self, user_id: str, login_data: dict, db: AsyncSession):
#         """Update login patterns for fraud detection"""
#         profile_result = await db.execute(
#             select(UserPaymentProfile).where(UserPaymentProfile.user_id == user_id)
#         )
#         profile = profile_result.scalar_one_or_none()
        
#         if profile:
#             login_history = profile.login_history or []
            
#             # Add new login record
#             login_record = {
#                 "timestamp": datetime.utcnow().isoformat(),
#                 "success": True
#             }
            
#             login_history.append(login_record)
            
#             # Keep only last 10 login records
#             if len(login_history) > 10:
#                 login_history = login_history[-10:]
            
#             profile.login_history = login_history
            
#             # Calculate risk score based on login patterns
#             await self._update_risk_score_from_patterns(profile)
            
#             await db.commit()

#     async def _update_risk_score_from_patterns(self, profile: UserPaymentProfile):
#         """Update user risk score based on login and payment patterns"""
#         login_history = profile.login_history or []
        
#         # Analyze login frequency and patterns
#         if len(login_history) >= 5:
#             recent_logins = login_history[-5:]
#             successful_logins = len([l for l in recent_logins if l.get("success")])
            
#             # Lower risk for consistent successful logins
#             if successful_logins == 5:
#                 profile.risk_score = max((profile.risk_score or 0.5) - 0.05, 0.0)
            
#         # Additional risk factors could be added here
#         # (payment history, dispute history, etc.)