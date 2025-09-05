import api from './api';

export const bookingService = {
  createBooking: (bookingData) => api.post('/api/v1/bookings', bookingData),
  getBooking: (id) => api.get(`/api/v1/bookings/${id}`),
  getUserBookings: () => api.get('/api/v1/bookings'),
  updateBooking: (id, data) => api.put(`/api/v1/bookings/${id}`, data),
  cancelBooking: (id) => api.put(`/api/v1/bookings/${id}/cancel`),
  reserveSeats: (reservationData) => api.post('/api/v1/reservations/reservations', reservationData),
};