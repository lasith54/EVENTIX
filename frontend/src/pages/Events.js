import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { eventService } from '../services/eventService';
import EventCard from '../components/Events/EventCard';
import SearchFilter from '../components/Events/SearchFilter';
import './Events.css';

const Events = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    category: '',
    location: '',
    date: '',
    priceRange: ''
  });

  useEffect(() => {
    loadEvents();
  }, [filters]);

  const loadEvents = async () => {
    try {
      setLoading(true);
      
      // If we have filters, use search, otherwise get all events
      let response;
      if (Object.values(filters).some(value => value)) {
        response = await eventService.searchEvents({
          filters: filters,
          q: filters.search || 'events'
        });
        setEvents(response.data.events || []);
      } else {
        response = await eventService.getAllEvents();
        setEvents(response.data.items || []);
      }
    } catch (err) {
      setError('Failed to load events');
      console.error('Error loading events:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="loading">Loading events...</div>;
  if (error) return <div className="error">{error}</div>;

  return (
    <div className="events-page">
      <div className="container">
        <h1>Upcoming Events</h1>
        
        <SearchFilter filters={filters} setFilters={setFilters} />
        
        <div className="events-grid">
          {events.map(event => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
        
        {events.length === 0 && (
          <div className="no-events">
            <p>No events found matching your criteria.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Events;