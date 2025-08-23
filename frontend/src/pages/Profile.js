import React from 'react';
import { useAuth } from '../context/AuthContext';
import './Profile.css';

const Profile = () => {
  const { user } = useAuth();

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
          </div>
        </div>

        <div className="profile-section">
          <h2>My Bookings</h2>
          <div className="bookings-placeholder">
            <p>Your booking history will appear here.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;