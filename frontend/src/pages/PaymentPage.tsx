import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation, useParams } from 'react-router-dom';
import { authService } from '@/services/auth';
import { paymentService } from '@/services/payment';
import { Navbar } from '@/components';
import type {CreatePaymentMethodData} from '@/services/payment';
import { create } from 'domain';

interface BookingData {
  id: string;
  event_id: string;
  total_amount: number;
  currency: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  items: any[];
  event_title?: string;
}

interface PaymentMethod {
  id: string; // UUID
  name: string;
  type: string;
  description: string;
  is_active: boolean;
}

interface RawBookingData extends Partial<BookingData> {
  id?: string;
  booking_id?: string;
  _id?: string;
  uuid?: string;
  [key: string]: any;
}

interface PaymentFormData {
  cardNumber: string;
  cardName: string;
  expiryDate: string;
  cvv: string;
  bankAccount?: string;
  walletEmail?: string;
}

const PaymentPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { bookingId } = useParams<{ bookingId: string }>();
  
  const [booking, setBooking] = useState<BookingData | null>(null);
  const [selectedPaymentMethod, setSelectedPaymentMethod] = useState<string>('credit_card');
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user] = useState(authService.getUser());
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
  const [selectedPaymentMethodId, setSelectedPaymentMethodId] = useState<string>('');

  // Payment form data
  const [paymentForm, setPaymentForm] = useState<PaymentFormData>({
    cardNumber: '',
    cardName: '',
    expiryDate: '',
    cvv: '',
    bankAccount: '',
    walletEmail: '',
  });

  // Agreement checkbox
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  useEffect(() => {
    const initializePayment = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Get booking data from navigation state
        const rawBookingData = location.state?.booking as RawBookingData;
        const paymentMethod = location.state?.selectedPaymentMethod as string;

        if (rawBookingData && paymentMethod) {
          console.log('Booking data from state:', rawBookingData);

          const bookingId = rawBookingData.id || 
                         rawBookingData.booking_id || 
                         rawBookingData._id || 
                         rawBookingData.uuid ||
                         null;
          
          if (!bookingId) {
            console.error('No booking ID found in any expected field:', Object.keys(rawBookingData));
            throw new Error('Booking ID is missing. Please try creating the booking again.');
          }
          
          const normalizedBooking = {
            id: bookingId,
            event_id: rawBookingData.event_id || '',
            total_amount: rawBookingData.total_amount || 0,
            currency: rawBookingData.currency || 'LKR',
            customer_name: rawBookingData.customer_name || 'Unknown Customer',
            customer_email: rawBookingData.customer_email || '',
            customer_phone: rawBookingData.customer_phone || '',
            items: rawBookingData.items || [],
            event_title: rawBookingData.event_title || 'Event Booking',
          };
          
          setBooking(normalizedBooking);
          setSelectedPaymentMethod(paymentMethod);
          
        } else if (bookingId) {
          throw new Error('Direct booking access not implemented. Please start from the booking page.');
        } else {
          throw new Error('No booking information found. Please start from the booking page.');
        }
      } catch (err) {
        console.error('Payment initialization error:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize payment');
      } finally {
        setLoading(false);
      }
    };

    initializePayment();
  }, [bookingId, location.state]);

  const handleFormChange = (field: keyof PaymentFormData, value: string) => {
    setPaymentForm(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const validatePaymentForm = (): string | null => {
    if (!agreedToTerms) {
      return 'Please agree to the terms and conditions';
    }

    switch (selectedPaymentMethod) {
      case 'credit_card':
        if (!paymentForm.cardNumber || paymentForm.cardNumber.length < 16) {
          return 'Please enter a valid card number';
        }
        if (!paymentForm.cardName.trim()) {
          return 'Please enter the cardholder name';
        }
        if (!paymentForm.expiryDate || !/^\d{2}\/\d{2}$/.test(paymentForm.expiryDate)) {
          return 'Please enter expiry date in MM/YY format';
        }
        if (!paymentForm.cvv || paymentForm.cvv.length < 3) {
          return 'Please enter a valid CVV';
        }
        break;
      
      case 'bank_transfer':
        if (!paymentForm.bankAccount?.trim()) {
          return 'Please enter your bank account number';
        }
        break;
      
      case 'digital_wallet':
        if (!paymentForm.walletEmail?.trim() || !paymentForm.walletEmail.includes('@')) {
          return 'Please enter a valid wallet email address';
        }
        break;
    }

    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!booking) {
      setError('Booking information not available');
      return;
    }

    const validationError = validatePaymentForm();
    if (validationError) {
      setError(validationError);
      return;
    }

    setProcessing(true);
    setError(null);

    try {
        console.log('Starting payment process...');

        // Step 1: Create payment method first
    let paymentMethodData;
    
    switch (selectedPaymentMethod) {
      case 'credit_card':
        paymentMethodData = {
          method_type: 'CREDIT_CARD' as const,
          provider: 'stripe', // or your payment provider
          card_last_four: paymentForm.cardNumber.slice(-4),
          card_expiry: paymentForm.expiryDate,
          billing_details: {
            name: paymentForm.cardName,
            card_number: paymentForm.cardNumber, // This should be encrypted in production
          }
        };
        break;
        
      case 'bank_transfer':
        paymentMethodData = {
          method_type: 'BANK_TRANSFER' as const,
          provider: 'bank',
          billing_details: {
            account_number: paymentForm.bankAccount,
            customer_name: booking.customer_name,
          }
        };
        break;

      case 'digital_wallet':
        paymentMethodData = {
          method_type: 'DIGITAL_WALLET' as const,
          provider: 'paypal', // or your wallet provider
          billing_details: {
            email: paymentForm.walletEmail,
            customer_name: booking.customer_name,
          }
        };
        break;
        
        default:
            throw new Error('Invalid payment method selected');
      }

      console.log('Creating payment method:', paymentMethodData);
      const createdPaymentMethod = await paymentService.createPaymentMethod(paymentMethodData);
    
      console.log('Payment method created:', createdPaymentMethod);

      // Create payment
      const paymentData = {
        booking_id: booking.id,
        amount: booking.total_amount,
        currency: booking.currency,
        payment_method_id: createdPaymentMethod.id,
        description: `Payment for ${booking.event_title} - Booking ${booking.id}`,
      };

      console.log('Creating payment:', paymentData);

      const payment = await paymentService.createPayment(paymentData);
      
      console.log('Payment created successfully:', payment);

      // Navigate to success page
      navigate('/payment/success', {
        state: {
          booking,
          payment,
          message: 'Payment successful! Your booking has been confirmed.'
        }
      });

    } catch (err) {
      console.error('Payment error:', err);
      setError(err instanceof Error ? err.message : 'Failed to process payment');
    } finally {
      setProcessing(false);
    }
  };

  const formatCardNumber = (value: string) => {
    // Remove non-digits and limit to 16 characters
    const digits = value.replace(/\D/g, '').slice(0, 16);
    // Add spaces every 4 digits
    return digits.replace(/(\d{4})(?=\d)/g, '$1 ');
  };

  const handleCardNumberChange = (value: string) => {
    const formatted = formatCardNumber(value);
    handleFormChange('cardNumber', formatted.replace(/\s/g, ''));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} isAuthenticated={!!user} />
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-2 text-muted-foreground">Preparing payment...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !booking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-background to-yellow-100/50">
        <Navbar user={user} isAuthenticated={!!user} />
        <div className="flex items-center justify-center py-20">
          <div className="text-center max-w-md mx-auto">
            <div className="mb-4">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100 mb-4">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 15.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-foreground mb-2">Payment Setup Failed</h3>
              <p className="text-destructive text-sm mb-4">{error}</p>
            </div>
            <div className="space-y-2">
              <button 
                onClick={() => navigate('/events')}
                className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
              >
                Back to Events
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} isAuthenticated={!!user} />
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <p className="text-muted-foreground mb-4">Payment information not available</p>
            <button 
              onClick={() => navigate('/events')}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
            >
              Back to Events
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar user={user} isAuthenticated={!!user} />

      <main className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <button
            onClick={() => navigate('/events')}
            className="flex items-center text-primary hover:text-primary/80 mb-4"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Events
          </button>
          
          <h1 className="text-3xl font-display font-bold text-foreground mb-2">
            Complete Payment
          </h1>
          <p className="text-muted-foreground">
            Secure payment processing for your booking
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Payment Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Payment Method Display */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Payment Method
                </h2>
                <div className="flex items-center p-3 bg-secondary/20 border border-border rounded-lg">
                  <div className="w-8 h-5 mr-3 flex items-center justify-center">
                    {selectedPaymentMethod === 'credit_card' && <span className="text-lg">💳</span>}
                    {selectedPaymentMethod === 'bank_transfer' && <span className="text-lg">🏦</span>}
                    {selectedPaymentMethod === 'digital_wallet' && <span className="text-lg">📱</span>}
                  </div>
                  <div>
                    <p className="font-medium">
                      {selectedPaymentMethod === 'credit_card' && 'Credit/Debit Card'}
                      {selectedPaymentMethod === 'bank_transfer' && 'Bank Transfer'}
                      {selectedPaymentMethod === 'digital_wallet' && 'Digital Wallet'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Payment Details Form */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Payment Details
                </h2>

                {/* Credit Card Form */}
                {selectedPaymentMethod === 'credit_card' && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Card Number *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="1234 5678 9012 3456"
                        value={formatCardNumber(paymentForm.cardNumber)}
                        onChange={(e) => handleCardNumberChange(e.target.value)}
                        className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                        maxLength={19}
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Cardholder Name *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="John Doe"
                        value={paymentForm.cardName}
                        onChange={(e) => handleFormChange('cardName', e.target.value)}
                        className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          Expiry Date *
                        </label>
                        <input
                          type="text"
                          required
                          placeholder="MM/YY"
                          value={paymentForm.expiryDate}
                          onChange={(e) => {
                            let value = e.target.value.replace(/\D/g, '');
                            if (value.length >= 2) {
                              value = value.substring(0, 2) + '/' + value.substring(2, 4);
                            }
                            handleFormChange('expiryDate', value);
                          }}
                          className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                          maxLength={5}
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-foreground mb-2">
                          CVV *
                        </label>
                        <input
                          type="text"
                          required
                          placeholder="123"
                          value={paymentForm.cvv}
                          onChange={(e) => {
                            const value = e.target.value.replace(/\D/g, '').slice(0, 4);
                            handleFormChange('cvv', value);
                          }}
                          className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                          maxLength={4}
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Bank Transfer Form */}
                {selectedPaymentMethod === 'bank_transfer' && (
                  <div className="space-y-4">
                    <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                      <h3 className="font-medium text-blue-900 mb-2">Bank Transfer Instructions</h3>
                      <div className="text-sm text-blue-800 space-y-1">
                        <p><strong>Bank:</strong> Eventix Payment Bank</p>
                        <p><strong>Account Name:</strong> Eventix Payments Ltd</p>
                        <p><strong>Account Number:</strong> 1234567890</p>
                        <p><strong>Routing Number:</strong> 987654321</p>
                        <p><strong>Reference:</strong> {booking.id}</p>
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Your Bank Account Number *
                      </label>
                      <input
                        type="text"
                        required
                        placeholder="Enter your bank account number"
                        value={paymentForm.bankAccount}
                        onChange={(e) => handleFormChange('bankAccount', e.target.value)}
                        className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        For verification purposes only
                      </p>
                    </div>
                  </div>
                )}

                {/* Digital Wallet Form */}
                {selectedPaymentMethod === 'digital_wallet' && (
                  <div className="space-y-4">
                    <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg">
                      <h3 className="font-medium text-purple-900 mb-2">Digital Wallet Payment</h3>
                      <p className="text-sm text-purple-800">
                        You will be redirected to complete payment via your chosen digital wallet.
                      </p>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-foreground mb-2">
                        Wallet Email Address *
                      </label>
                      <input
                        type="email"
                        required
                        placeholder="your.wallet@email.com"
                        value={paymentForm.walletEmail}
                        onChange={(e) => handleFormChange('walletEmail', e.target.value)}
                        className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Terms and Agreement */}
              <div className="bg-card border border-border rounded-lg p-6">
                <div className="flex items-start">
                  <input
                    type="checkbox"
                    id="terms"
                    checked={agreedToTerms}
                    onChange={(e) => setAgreedToTerms(e.target.checked)}
                    className="mt-1 mr-3"
                    required
                  />
                  <label htmlFor="terms" className="text-sm text-foreground">
                    I agree to the <a href="#" className="text-primary hover:underline">Terms and Conditions</a> and <a href="#" className="text-primary hover:underline">Privacy Policy</a>. 
                    I understand that this payment is for event tickets and is subject to the event's refund policy.
                  </label>
                </div>
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md">
                  <p className="text-sm">{error}</p>
                </div>
              )}

              {/* Submit Button */}
              <button
                type="submit"
                disabled={processing || !agreedToTerms}
                className="w-full bg-primary text-primary-foreground py-3 px-4 rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
              >
                {processing ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Processing Payment...
                  </div>
                ) : (
                  `Complete Payment - ${booking.currency} ${booking.total_amount.toFixed(2)}`
                )}
              </button>
            </form>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-lg p-6 sticky top-6">
              <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                Order Summary
              </h2>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-foreground">{booking.event_title}</h3>
                  <p className="text-sm text-muted-foreground">Booking ID: {booking.id}</p>
                </div>

                <div className="space-y-2">
                  {booking.items?.length > 0 ? booking.items.map((item, index) => (
                    <div key={index} className="flex justify-between text-sm">
                      <span>{item.pricing_tier || 'Ticket'} × {item.quantity || 1}</span>
                      <span>{booking.currency} {((item.unit_price || 0) * (item.quantity || 1)).toFixed(2)}</span>
                    </div>
                  )) : (
                    <div className="text-sm text-muted-foreground">No item details available</div>
                  )}
                </div>

                <hr className="border-border" />

                <div className="flex justify-between items-center">
                  <p className="text-lg font-semibold text-foreground">Total</p>
                  <p className="text-lg font-semibold text-foreground">
                    {booking.currency} {booking.total_amount.toFixed(2)}
                  </p>
                </div>

                <div className="text-xs text-muted-foreground">
                  <p>Customer: {booking.customer_name}</p>
                  <p>Email: {booking.customer_email}</p>
                  {booking.customer_phone && (
                    <p>Phone: {booking.customer_phone}</p>
                  )}
                </div>

                {/* Security Icons */}
                <div className="pt-4 border-t border-border">
                  <div className="flex items-center justify-center space-x-4 text-xs text-muted-foreground">
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                      </svg>
                      Secure
                    </div>
                    <div className="flex items-center">
                      <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      Verified
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default PaymentPage;