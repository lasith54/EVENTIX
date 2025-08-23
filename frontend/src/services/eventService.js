import api from './api';

export const eventService = {
  getAllEvents: () => api.get('/events'),
  getEventById: (id) => api.get(`/events/${id}`),
  getEventSchedules: (eventId) => api.get(`/events/${eventId}/schedules`),
  getVenueSeats: (venueId, sectionId) => api.get(`/venues/${venueId}/sections/${sectionId}/seats`),
  searchEvents: (params) => api.get('/events/search', { params }),
};