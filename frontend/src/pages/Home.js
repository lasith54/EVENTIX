import React from 'react';
import { Link } from 'react-router-dom';
import './Home.css';

const Home = () => {
  return (
    <div className="home-page">
      <div className="hero-section">
        <div className="container">
          <h1>Welcome to Eventix</h1>
          <p>Your premier destination for booking tickets to amazing events</p>
          <Link to="/events" className="cta-button">
            Browse Events
          </Link>
        </div>
      </div>
      
      <div className="features-section">
        <div className="container">
          <h2>Why Choose Eventix?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <h3>Easy Booking</h3>
              <p>Simple and intuitive booking process</p>
            </div>
            <div className="feature-card">
              <h3>Secure Payments</h3>
              <p>Your payments are safe and secure</p>
            </div>
            <div className="feature-card">
              <h3>Best Events</h3>
              <p>Discover the hottest events in town</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;