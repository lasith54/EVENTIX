import React, { useState, useEffect } from 'react';
import { eventService } from '../../services/eventService';
import './SeatSelection.css';

const SeatSelection = ({ eventId, onSeatSelection, selectedSeats }) => {
  const [seats, setSeats] = useState([]);
  const [sections, setSections] = useState([]);
  const [selectedSection, setSelectedSection] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVenueData();
  }, [eventId]);

  const loadVenueData = async () => {
    try {
      // Load venue sections and seats
      const response = await eventService.getEventById(eventId);
      const venue = response.data.venue;
      setSections(venue.sections);
      setSelectedSection(venue.sections[0]);
      loadSeats(venue.sections[0].id);
    } catch (error) {
      console.error('Failed to load venue data');
    }
  };

  const loadSeats = async (sectionId) => {
    try {
      setLoading(true);
      const response = await eventService.getVenueSeats(selectedSection.venue_id, sectionId);
      setSeats(response.data);
    } catch (error) {
      console.error('Failed to load seats');
    } finally {
      setLoading(false);
    }
  };

  const handleSeatClick = (seat) => {
    if (seat.status !== 'AVAILABLE') return;

    const isSelected = selectedSeats.find(s => s.id === seat.id);
    let newSelection;

    if (isSelected) {
      newSelection = selectedSeats.filter(s => s.id !== seat.id);
    } else {
      newSelection = [...selectedSeats, seat];
    }

    onSeatSelection(newSelection);
  };

  const renderSeat = (seat) => {
    const isSelected = selectedSeats.find(s => s.id === seat.id);
    const seatClass = `seat ${seat.status.toLowerCase()} ${isSelected ? 'selected' : ''}`;

    return (
      <div
        key={seat.id}
        className={seatClass}
        onClick={() => handleSeatClick(seat)}
        title={`Row ${seat.row_number}, Seat ${seat.seat_number}`}
      >
        {seat.seat_number}
      </div>
    );
  };

  return (
    <div className="seat-selection">
      <div className="section-selector">
        <h3>Select Section</h3>
        <div className="sections">
          {sections.map(section => (
            <button
              key={section.id}
              className={`section-btn ${selectedSection?.id === section.id ? 'active' : ''}`}
              onClick={() => {
                setSelectedSection(section);
                loadSeats(section.id);
              }}
            >
              {section.name}
            </button>
          ))}
        </div>
      </div>

      <div className="seat-map">
        <div className="stage">STAGE</div>
        {loading ? (
          <div className="loading">Loading seats...</div>
        ) : (
          <div className="seats-grid">
            {seats.map(renderSeat)}
          </div>
        )}
      </div>

      <div className="seat-legend">
        <div className="legend-item">
          <div className="seat available"></div>
          <span>Available</span>
        </div>
        <div className="legend-item">
          <div className="seat selected"></div>
          <span>Selected</span>
        </div>
        <div className="legend-item">
          <div className="seat occupied"></div>
          <span>Occupied</span>
        </div>
      </div>

      <div className="selection-summary">
        <h4>Selected Seats: {selectedSeats.length}</h4>
        <div className="selected-seats-list">
          {selectedSeats.map(seat => (
            <span key={seat.id} className="selected-seat-tag">
              Row {seat.row_number}, Seat {seat.seat_number}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SeatSelection;