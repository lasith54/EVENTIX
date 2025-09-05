import api from './api';

export const eventService = {
  getAllEvents: () => api.get('/api/v1/events'),
  getEventById: (id) => api.get(`/api/v1/events/${id}`),
  getEventSchedules: (eventId) => api.get(`/api/v1/events/${eventId}/schedules`),
  getVenueSeats: (venueId, sectionId) => api.get(`/api/v1/seats/venue-sections/${sectionId}/seats`),
  searchEvents: (params) => api.post('/api/v1/events/search', params),
};