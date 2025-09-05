import React from 'react';
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { paymentService, bookingService } from '../services/paymentService';
import { useAuth } from '../context/AuthContext';
import './Payment.css';

const Payment = () => {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    loadBookingDetails();
  }, [bookingId]);

  const loadBookingDetails = async () => {
    try {
      const response = await bookingService.getBooking(bookingId);
      setBooking(response.data);
    } catch (error) {
      console.error('Failed to load booking details:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    try {
      setProcessing(true);
      
      // Create a mock payment method for demo purposes
      const paymentMethodData = {
        method_type: 'CREDIT_CARD',
        provider: 'demo',
        card_last_four: '1234',
        card_expiry: '12/25'
      };
      
      const paymentMethodResponse = await paymentService.addPaymentMethod(paymentMethodData);
      
      // Process payment
      const paymentData = {
        booking_id: bookingId,
        payment_method_id: paymentMethodResponse.data.id,
        amount: booking.total_amount,
        currency: booking.currency,
        description: `Payment for booking ${booking.booking_reference}`
      };
      
      await paymentService.createPayment(paymentData);
      
      alert('Payment successful!');
      navigate('/profile');
      
    } catch (error) {
      console.error('Payment failed:', error);
      alert('Payment failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  if (loading) {
    return (
      <div className="payment-page">
        <div className="container">
          <div className="payment-placeholder">
            <p>Loading booking details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!booking) {
    return (
      <div className="payment-page">
        <div className="container">
          <div className="payment-placeholder">
            <p>Booking not found.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="payment-page">
      <div className="container">
        <h1>Payment</h1>
        
        <div className="payment-summary">
          <h2>Booking Summary</h2>
          <div className="summary-details">
            <p><strong>Booking Reference:</strong> {booking.booking_reference}</p>
            <p><strong>Total Amount:</strong> {booking.currency} {booking.total_amount}</p>
            <p><strong>Items:</strong> {booking.items?.length || 0} ticket(s)</p>
          </div>
        </div>
        
        <div className="payment-form">
          <h3>Payment Method</h3>
          <div className="payment-method-demo">
            <p>Demo Payment Method</p>
            <p>Card ending in 1234</p>
          </div>
          
          <button 
            className="btn btn-success payment-btn"
            onClick={handlePayment}
            disabled={processing}
          >
            {processing ? 'Processing Payment...' : `Pay ${booking.currency} ${booking.total_amount}`}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Payment;