import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Navbar } from '@/components';
import { authService } from '@/services/auth';

interface PaymentSuccessProps {
  booking?: any;
  payment?: any;
  message?: string;
}

const PaymentSuccessPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const user = authService.getUser();
  
  const { booking, payment, message } = location.state || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-background to-yellow-100/50">
      <Navbar user={user} isAuthenticated={!!user} />

      <main className="max-w-2xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          {/* Success Icon */}
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-6">
            <svg className="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          {/* Success Title */}
          <h1 className="text-3xl font-display font-bold text-foreground mb-4">
            Payment Successful!
          </h1>
          
          {/* Success Message */}
          <p className="text-lg text-muted-foreground mb-8">
            {message || 'Your booking has been confirmed and payment processed successfully.'}
          </p>

          {/* Booking Details Card */}
          {booking && (
            <div className="bg-card border border-border rounded-lg p-6 mb-8 text-left">
              <h2 className="text-xl font-semibold text-foreground mb-4">Booking Details</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground font-medium">Booking ID</p>
                  <p className="font-mono text-xs break-all">{booking.id}</p>
                </div>
                
                <div>
                  <p className="text-muted-foreground font-medium">Event</p>
                  <p>{booking.event_title || 'Event Booking'}</p>
                </div>
                
                <div>
                  <p className="text-muted-foreground font-medium">Customer</p>
                  <p>{booking.customer_name || 'N/A'}</p>
                </div>
                
                <div>
                  <p className="text-muted-foreground font-medium">Email</p>
                  <p className="break-all">{booking.customer_email || 'N/A'}</p>
                </div>
                
                <div>
                  <p className="text-muted-foreground font-medium">Total Amount</p>
                  <p className="font-semibold text-lg">
                    {booking.currency || 'LKR'} {booking.total_amount?.toFixed(2) || '0.00'}
                  </p>
                </div>
                
                {payment && (
                  <div>
                    <p className="text-muted-foreground font-medium">Payment ID</p>
                    <p className="font-mono text-xs break-all">{payment.id}</p>
                  </div>
                )}

                {booking.customer_phone && (
                  <div className="md:col-span-2">
                    <p className="text-muted-foreground font-medium">Phone</p>
                    <p>{booking.customer_phone}</p>
                  </div>
                )}
              </div>

              {/* Ticket Details */}
              {booking.items && booking.items.length > 0 && (
                <div className="mt-6 pt-4 border-t border-border">
                  <p className="font-medium text-muted-foreground mb-3">Tickets</p>
                  <div className="space-y-2">
                    {booking.items.map((item: any, index: number) => (
                      <div key={index} className="flex justify-between items-start text-sm">
                        <div className="flex-1">
                          <span className="font-medium">{item.pricing_tier || 'Ticket'}</span>
                          {item.section_name && (
                            <span className="text-muted-foreground"> - {item.section_name}</span>
                          )}
                          {item.seat_row && item.seat_number && (
                            <div className="text-xs text-muted-foreground">
                              {item.seat_row}, Seat {item.seat_number}
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <div>×{item.quantity || 1}</div>
                          <div className="text-xs text-muted-foreground">
                            {booking.currency} {((item.unit_price || 0) * (item.quantity || 1)).toFixed(2)}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Payment Method */}
              {payment && payment.payment_method_id && (
                <div className="mt-4 pt-4 border-t border-border">
                  <p className="text-muted-foreground font-medium">Payment Method</p>
                  <p className="capitalize">
                    {payment.payment_method_id.replace('_', ' ')}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Status: <span className="capitalize">{payment.status || 'Completed'}</span>
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Confirmation Notice */}
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-center text-blue-800 text-sm">
                <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z" />
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z" />
                </svg>
                <span>A confirmation email has been sent to your registered email address.</span>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/events')}
                className="bg-primary text-primary-foreground px-6 py-3 rounded-md hover:bg-primary/90 font-medium transition-colors"
              >
                Browse More Events
              </button>
              
              <button
                onClick={() => navigate('/profile')}
                className="bg-secondary text-secondary-foreground px-6 py-3 rounded-md hover:bg-secondary/80 font-medium transition-colors"
              >
                View My Profile
              </button>
            </div>

            {/* Additional Info */}
            <div className="text-xs text-muted-foreground space-y-1">
              <p>💾 Your booking details have been saved to your account</p>
              <p>📱 You can access your tickets anytime from your profile</p>
              <p>❓ Need help? Contact our support team</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default PaymentSuccessPage;