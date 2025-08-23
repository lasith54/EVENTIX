import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { eventService } from '../services/eventService';
import { bookingService } from '../services/bookingService';
import { useBooking } from '../context/BookingContext';
import SeatSelection from '../components/Booking/SeatSelection';
import BookingSummary from '../components/Booking/BookingSummary';
import CustomerDetails from '../components/Booking/CustomerDetails';
import './Booking.css';

const Booking = () => {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const { selectedSeats, setSelectedSeats, bookingStep, setBookingStep } = useBooking();
  const [event, setEvent] = useState(null);
  const [venue, setVenue] = useState(null);
  const [customerDetails, setCustomerDetails] = useState({
    name: '',
    email: '',
    phone: ''
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadEventData();
  }, [eventId]);

  const loadEventData = async () => {
    try {
      const response = await eventService.getEventById(eventId);
      setEvent(response.data);
    } catch (error) {
      console.error('Failed to load event data');
    }
  };

  const handleSeatSelection = (seats) => {
    setSelectedSeats(seats);
    if (seats.length > 0) {
      setBookingStep('customer-details');
    }
  };

  const handleCustomerSubmit = (details) => {
    setCustomerDetails(details);
    setBookingStep('summary');
  };

  const handleBookingConfirm = async () => {
    try {
      setLoading(true);
      const bookingData = {
        event_id: eventId,
        customer_name: customerDetails.name,
        customer_email: customerDetails.email,
        customer_phone: customerDetails.phone,
        booking_items: selectedSeats.map(seat => ({
          seat_id: seat.id,
          venue_section_id: seat.venue_section_id,
          unit_price: seat.price,
          quantity: 1,
          section_name: seat.section_name,
          seat_row: seat.row_number,
          seat_number: seat.seat_number
        })),
        total_amount: selectedSeats.reduce((sum, seat) => sum + seat.price, 0),
        currency: 'LKR'
      };

      const response = await bookingService.createBooking(bookingData);
      navigate(`/payment/${response.data.id}`);
    } catch (error) {
      console.error('Booking failed:', error);
      alert('Booking failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="booking-page">
      <div className="container">
        <div className="booking-header">
          <h1>Book Tickets</h1>
          {event && <h2>{event.title}</h2>}
        </div>

        <div className="booking-steps">
          <div className={`step ${bookingStep === 'seat-selection' ? 'active' : ''}`}>
            1. Select Seats
          </div>
          <div className={`step ${bookingStep === 'customer-details' ? 'active' : ''}`}>
            2. Customer Details
          </div>
          <div className={`step ${bookingStep === 'summary' ? 'active' : ''}`}>
            3. Summary
          </div>
        </div>

        <div className="booking-content">
          {bookingStep === 'seat-selection' && (
            <SeatSelection 
              eventId={eventId}
              onSeatSelection={handleSeatSelection}
              selectedSeats={selectedSeats}
            />
          )}

          {bookingStep === 'customer-details' && (
            <CustomerDetails 
              onSubmit={handleCustomerSubmit}
              initialData={customerDetails}
            />
          )}

          {bookingStep === 'summary' && (
            <BookingSummary 
              event={event}
              selectedSeats={selectedSeats}
              customerDetails={customerDetails}
              onConfirm={handleBookingConfirm}
              loading={loading}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Booking;