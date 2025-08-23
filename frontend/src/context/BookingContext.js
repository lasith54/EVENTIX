import React, { createContext, useContext, useState } from 'react';

const BookingContext = createContext();

export const useBooking = () => {
  const context = useContext(BookingContext);
  if (!context) {
    throw new Error('useBooking must be used within a BookingProvider');
  }
  return context;
};

export const BookingProvider = ({ children }) => {
  const [currentBooking, setCurrentBooking] = useState(null);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [bookingStep, setBookingStep] = useState('seat-selection');

  const resetBooking = () => {
    setCurrentBooking(null);
    setSelectedSeats([]);
    setBookingStep('seat-selection');
  };

  const value = {
    currentBooking,
    setCurrentBooking,
    selectedSeats,
    setSelectedSeats,
    bookingStep,
    setBookingStep,
    resetBooking
  };

  return (
    <BookingContext.Provider value={value}>
      {children}
    </BookingContext.Provider>
  );
};