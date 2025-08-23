import api from './api';

export const bookingService = {
  createBooking: (bookingData) => api.post('/bookings', bookingData),
  getBooking: (id) => api.get(`/bookings/${id}`),
  getUserBookings: () => api.get('/bookings/user'),
  updateBooking: (id, data) => api.put(`/bookings/${id}`, data),
  cancelBooking: (id) => api.delete(`/bookings/${id}`),
  reserveSeats: (eventId, seats) => api.post(`/events/${eventId}/reserve-seats`, { seats }),
};