import React from 'react';
import { Link } from 'react-router-dom';
import './EventCard.css';

const EventCard = ({ event }) => {
  return (
    <div className="event-card">
      <img src={event.poster_image_url} alt={event.title} className="event-image" />
      <div className="event-content">
        <h3 className="event-title">{event.title}</h3>
        <p className="event-venue">{event.venue?.name}</p>
        <p className="event-date">
          {new Date(event.schedules?.[0]?.start_datetime).toLocaleDateString()}
        </p>
        <p className="event-price">
          From LKR {event.pricing_tiers?.[0]?.price || 'TBA'}
        </p>
        <Link to={`/events/${event.id}`} className="view-details-btn">
          View Details
        </Link>
      </div>
    </div>
  );
};

export default EventCard;