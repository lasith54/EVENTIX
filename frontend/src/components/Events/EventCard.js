import React from 'react';
import { Link } from 'react-router-dom';
import './EventCard.css';

const EventCard = ({ event }) => {
  const getImageUrl = (event) => {
    if (event.poster_image_url) {
      return event.poster_image_url;
    }
    // Fallback to a placeholder image
    return 'https://images.pexels.com/photos/1763075/pexels-photo-1763075.jpeg?auto=compress&cs=tinysrgb&w=400';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Date TBA';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const getMinPrice = (event) => {
    if (event.pricing_tiers && event.pricing_tiers.length > 0) {
      const minPrice = Math.min(...event.pricing_tiers.map(tier => tier.price));
      return `LKR ${minPrice.toLocaleString()}`;
    }
    if (event.min_price) {
      return `LKR ${event.min_price.toLocaleString()}`;
    }
    return 'Price TBA';
  };

  return (
    <div className="event-card">
      <img src={getImageUrl(event)} alt={event.title} className="event-image" />
      <div className="event-content">
        <h3 className="event-title">{event.title}</h3>
        <p className="event-venue">{event.venue?.name}</p>
        <p className="event-date">
          {formatDate(event.schedules?.[0]?.start_datetime || event.next_schedule?.start_datetime)}
        </p>
        <p className="event-price">
          From {getMinPrice(event)}
        </p>
        <Link to={`/events/${event.id}`} className="view-details-btn">
          View Details
        </Link>
      </div>
    </div>
  );
};

export default EventCard;