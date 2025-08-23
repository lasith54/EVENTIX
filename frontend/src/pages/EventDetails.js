import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { eventService } from '../services/eventService';
import { useAuth } from '../context/AuthContext';
import './EventDetails.css';

const EventDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadEventDetails();
  }, [id]);

  const loadEventDetails = async () => {
    try {
      // For now, we'll use mock data since backend might not be ready
      setEvent({
        id: id,
        title: "Sample Concert Event",
        description: "This is a sample event description.",
        venue: { name: "Sample Venue" },
        schedules: [{ 
          id: 1, 
          start_datetime: new Date().toISOString(),
          is_sold_out: false 
        }]
      });
    } catch (error) {
      console.error('Failed to load event details');
    } finally {
      setLoading(false);
    }
  };

  const handleBookNow = () => {
    if (!user) {
      navigate('/login', { state: { returnTo: `/booking/${id}` } });
      return;
    }
    navigate(`/booking/${id}`);
  };

  if (loading) return <div className="loading">Loading...</div>;
  if (!event) return <div className="error">Event not found</div>;

  return (
    <div className="event-details">
      <div className="container">
        <div className="event-header">
          <div className="event-info">
            <h1>{event.title}</h1>
            <p className="event-description">{event.description}</p>
            
            <div className="event-meta">
              <div className="meta-item">
                <strong>Venue:</strong> {event.venue?.name}
              </div>
            </div>
          </div>
        </div>

        <div className="booking-section">
          <button 
            className="book-now-btn"
            onClick={handleBookNow}
          >
            Book Tickets
          </button>
        </div>
      </div>
    </div>
  );
};

export default EventDetails;