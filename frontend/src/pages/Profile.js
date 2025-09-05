import React from 'react';
import { useState, useEffect } from 'react';
import { bookingService } from '../services/bookingService';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const Profile = () => {
  const { user } = useAuth();
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadBookings();
  }, []);

  const loadBookings = async () => {
    try {
      const response = await bookingService.getUserBookings();
      setBookings(response.data || []);
    } catch (error) {
      console.error('Failed to load bookings:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="profile-page">
      <div className="container">
        <h1>My Profile</h1>
        
        <div className="profile-section">
          <h2>Personal Information</h2>
          <div className="profile-info">
            <div className="info-item">
              <label>Name:</label>
              <span>{user?.first_name} {user?.last_name}</span>
            </div>
            <div className="info-item">
              <label>Email:</label>
              <span>{user?.email}</span>
            </div>
            <div className="info-item">
              <label>Phone:</label>
              <span>{user?.phone_number || 'Not provided'}</span>
            </div>
            <div className="info-item">
              <label>Member Since:</label>
              <span>{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}</span>
            </div>
          </div>
        </div>

        <div className="profile-section">
          <h2>My Bookings</h2>
          {loading ? (
            <div className="bookings-placeholder">
              <p>Loading bookings...</p>
            </div>
          ) : bookings.length > 0 ? (
            <div className="bookings-list">
              {bookings.map((booking) => (
                <div key={booking.id} className="booking-item">
                  <div className="booking-header">
                    <h3>Booking #{booking.booking_reference}</h3>
                    <span className={`booking-status ${booking.status.toLowerCase()}`}>
                      {booking.status}
                    </span>
                  </div>
                  <div className="booking-details">
                    <p><strong>Event ID:</strong> {booking.event_id}</p>
                    <p><strong>Total Amount:</strong> {booking.currency} {booking.total_amount}</p>
                    <p><strong>Booking Date:</strong> {new Date(booking.booking_date).toLocaleDateString()}</p>
                    <p><strong>Items:</strong> {booking.items?.length || 0} ticket(s)</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bookings-placeholder">
              <p>No bookings found. <a href="/events">Browse events</a> to make your first booking!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Profile;