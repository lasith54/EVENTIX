const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://api-gateway:8080/api/v1';

export interface Event {
  id: string;
  title: string;
  short_description?: string;
  description?: string;
  event_type: 'concert' | 'conference' | 'sports' | 'theater' | 'workshop' | 'festival' | 'exhibition' | 'other';
  status: 'draft' | 'published' | 'cancelled' | 'postponed' | 'completed';
  venue_id: string;
  category_id?: string;
  artist_performer?: string;
  organizer?: string;
  duration_minutes?: number;
  age_restriction?: number;
  poster_image_url?: string;
  banner_image_url?: string;
  gallery_images?: string[];
  video_urls?: string[];
  slug?: string;
  tags?: string[];
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
  venue?: Venue;
  category?: EventCategory;
  schedules?: EventSchedule[];
  pricing_tiers?: EventPricingTier[];
  next_schedule?: EventSchedule;
  min_price?: number;
}

export interface Venue {
  id: string;
  name: string;
  description?: string;
  venue_type: 'stadium' | 'arena' | 'theater' | 'conference_center' | 'outdoor' | 'club' | 'other';
  address: string;
  city: string;
  state?: string;
  country: string;
  postal_code?: string;
  capacity: number;
  amenities?: string[];
  contact_info?: Record<string, any>;
  sections?: VenueSection[];
}

export interface VenueSection {
  id: string;
  venue_id: string;
  name: string;
  section_type: string;
  capacity: number;
  description?: string;
}

export interface EventCategory {
  id: string;
  name: string;
  description?: string;
  parent_id?: string;
  subcategories?: EventCategory[];
}

export interface EventSchedule {
  id: string;
  event_id: string;
  start_datetime: string;
  end_datetime?: string;
  doors_open?: string;
  is_main_event: boolean;
  notes?: string;
}

export interface EventPricingTier {
  id: string;
  event_id: string;
  venue_section_id: string;
  tier_name: string;
  price: number;
  total_seats: number;
  available_seats: number;
  early_bird_price?: number;
  early_bird_end_date?: string;
  is_active: boolean;
  venue_section?: VenueSection;
}

export interface EventListResponse {
  id: string;
  title: string;
  short_description?: string;
  event_type: Event['event_type'];
  status: Event['status'];
  artist_performer?: string;
  poster_image_url?: string;
  tags?: string[];
  created_at: string;
  venue?: Venue;
  next_schedule?: EventSchedule;
  min_price?: number;
}

export interface EventListPaginatedResponse {
  items: EventListResponse[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface EventFilters {
  status?: Event['status'];
  event_type?: Event['event_type'];
  venue_id?: string;
  category_id?: string;
  city?: string;
  date_from?: string;
  date_to?: string;
}

export interface SearchFilters {
  city?: string;
  country?: string;
  event_type?: Event['event_type'];
  category_id?: string;
  date_from?: string;
  date_to?: string;
  price_min?: number;
  price_max?: number;
}

export interface EventSearchResponse {
  events: EventListResponse[];
  total: number;
  filters_applied: SearchFilters;
}

class EventService {
  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = localStorage.getItem('token');
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    const response = await fetch(url, config);

    if (!response.ok) {
      if (response.status === 401) {
        // Token might be expired, redirect to login
        window.location.href = '/login';
        throw new Error('Authentication expired. Please login again.');
      }
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || error.message || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  async getEvents(filters: EventFilters = {}, skip: number = 0, limit: number = 20): Promise<EventListPaginatedResponse> {
    try {
      const params = new URLSearchParams();
      params.append('skip', skip.toString());
      params.append('limit', limit.toString());
      
      if (filters.status) params.append('status', filters.status);
      if (filters.event_type) params.append('event_type', filters.event_type);
      if (filters.venue_id) params.append('venue_id', filters.venue_id);
      if (filters.category_id) params.append('category_id', filters.category_id);
      if (filters.city) params.append('city', filters.city);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);

      return await this.makeRequest<EventListPaginatedResponse>(`/events?${params.toString()}`);
    } catch (error) {
      console.error('Failed to fetch events:', error);
      throw error;
    }
  }

  async searchEvents(
    query: string, 
    filters: SearchFilters = {}, 
    skip: number = 0, 
    limit: number = 20
  ): Promise<EventSearchResponse> {
    try {
      const params = new URLSearchParams();
      params.append('q', query);
      params.append('skip', skip.toString());
      params.append('limit', limit.toString());

      return await this.makeRequest<EventSearchResponse>(`/events/search?${params.toString()}`, {
        method: 'POST',
        body: JSON.stringify(filters),
      });
    } catch (error) {
      console.error('Failed to search events:', error);
      throw error;
    }
  }

  async getEvent(eventId: string): Promise<Event> {
    try {
      return await this.makeRequest<Event>(`/events/${eventId}`);
    } catch (error) {
      console.error('Failed to fetch event:', error);
      throw error;
    }
  }

  // Legacy method to maintain compatibility with existing code
  async joinEvent(eventId: string): Promise<{ message: string }> {
    // This would typically be handled by a booking service
    // For now, we'll simulate the response
    try {
      // You would implement this in your booking service
      console.log('Joining event:', eventId);
      return { message: 'Successfully joined event' };
    } catch (error) {
      console.error('Failed to join event:', error);
      throw error;
    }
  }
}

export const eventService = new EventService();