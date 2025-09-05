import React from 'react';
import './BookingSummary.css';

const BookingSummary = ({ event, selectedSeats, customerDetails, onConfirm, loading }) => {
  const totalAmount = selectedSeats.reduce((sum, seat) => sum + (seat.price || 0), 0);

  return (
    <div className="booking-summary">
      <h3>Booking Summary</h3>
      
      <div className="summary-section">
        <h4>Event Details</h4>
        <div className="event-info">
          <div className="info-row">
            <span className="label">Event:</span>
            <span className="value">{event?.title}</span>
          </div>
          <div className="info-row">
            <span className="label">Venue:</span>
            <span className="value">{event?.venue?.name}</span>
          </div>
          <div className="info-row">
            <span className="label">Date:</span>
            <span className="value">
              {event?.schedules?.[0] && new Date(event.schedules[0].start_datetime).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </span>
          </div>
          <div className="info-row">
            <span className="label">Time:</span>
            <span className="value">
              {event?.schedules?.[0] && new Date(event.schedules[0].start_datetime).toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </span>
          </div>
        </div>
      </div>

      <div className="summary-section">
        <h4>Selected Seats</h4>
        <div className="seats-list">
          {selectedSeats.map((seat, index) => (
            <div key={seat.id || index} className="seat-item">
              <div className="seat-details">
                <span className="seat-info">
                  {seat.section_name} - Row {seat.row_number}, Seat {seat.seat_number}
                </span>
                <span className="seat-type">{seat.seat_type}</span>
              </div>
              <div className="seat-price">
                LKR {seat.price?.toLocaleString() || '0'}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="summary-section">
        <h4>Customer Information</h4>
        <div className="customer-info">
          <div className="info-row">
            <span className="label">Name:</span>
            <span className="value">{customerDetails.name}</span>
          </div>
          <div className="info-row">
            <span className="label">Email:</span>
            <span className="value">{customerDetails.email}</span>
          </div>
          <div className="info-row">
            <span className="label">Phone:</span>
            <span className="value">{customerDetails.phone}</span>
          </div>
          {customerDetails.specialRequests && (
            <div className="info-row">
              <span className="label">Special Requests:</span>
              <span className="value">{customerDetails.specialRequests}</span>
            </div>
          )}
        </div>
      </div>

      <div className="summary-section total-section">
        <div className="total-breakdown">
          <div className="breakdown-row">
            <span>Tickets ({selectedSeats.length})</span>
            <span>LKR {totalAmount.toLocaleString()}</span>
          </div>
          <div className="breakdown-row">
            <span>Service Fee</span>
            <span>LKR 0</span>
          </div>
          <div className="breakdown-row total-row">
            <span>Total Amount</span>
            <span>LKR {totalAmount.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <div className="summary-actions">
        <button 
          className="btn btn-success"
          onClick={onConfirm}
          disabled={loading}
        >
          {loading ? 'Processing...' : 'Confirm Booking'}
        </button>
      </div>

      <div className="terms-notice">
        <p>
          By clicking "Confirm Booking", you agree to our 
          <a href="/terms" target="_blank"> Terms & Conditions</a> and 
          <a href="/privacy" target="_blank"> Privacy Policy</a>.
        </p>
      </div>
    </div>
  );
};

export default BookingSummary;