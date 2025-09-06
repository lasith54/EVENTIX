import React, { useState, useEffect } from 'react';
import { authService } from '@/services/auth';
import { eventService, EventListResponse, EventFilters, Event } from '@/services/events';
import { useNavigate } from 'react-router-dom';
import { Navbar } from '@/components';

const EventsPage: React.FC = () => {
  const navigate = useNavigate();
  const [events, setEvents] = useState<EventListResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | Event['status']>('all');
  const [joiningEventId, setJoiningEventId] = useState<string | null>(null);
  const [user, setUser] = useState(authService.getUser());
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    size: 20,
    total: 0,
    pages: 0
  });

  const fetchEvents = async (statusFilter?: Event['status'], page: number = 1) => {
    try {
      setLoading(true);
      setError(null);
      
      const filters: EventFilters = {};
      if (statusFilter) {
        filters.status = statusFilter;
      }
      
      const skip = (page - 1) * pagination.size;
      const response = await eventService.getEvents(filters, skip, pagination.size);
      
      setEvents(response.items);
      setPagination({
        page: response.page,
        size: response.size,
        total: response.total,
        pages: response.pages
      });
    } catch (err) {
      console.error('Error fetching events:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch events');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (query: string, page: number = 1) => {
    if (!query.trim()) {
      setIsSearching(false);
      fetchEvents(filter === 'all' ? undefined : filter, page);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setIsSearching(true);
      
      const filters = {};
      const skip = (page - 1) * pagination.size;
      const response = await eventService.searchEvents(query, filters, skip, pagination.size);
      
      setEvents(response.events);
      setPagination({
        page,
        size: pagination.size,
        total: response.total,
        pages: Math.ceil(response.total / pagination.size)
      });
    } catch (err) {
      console.error('Error searching events:', err);
      setError(err instanceof Error ? err.message : 'Failed to search events');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isSearching && searchQuery) {
      handleSearch(searchQuery, 1);
    } else {
      const statusFilter = filter === 'all' ? undefined : filter;
      fetchEvents(statusFilter, 1);
    }
  }, [filter]);

  useEffect(() => {
    // Subscribe to auth changes to update user info
    const unsubscribe = authService.onAuthChange(() => {
      setUser(authService.getUser());
    });

    return unsubscribe;
  }, []);

  const handleJoinEvent = async (eventId: string) => {
    try {
      setJoiningEventId(eventId);
      await eventService.joinEvent(eventId);
      
      // Refresh events to show updated attendee count
      if (isSearching && searchQuery) {
        await handleSearch(searchQuery, pagination.page);
      } else {
        const statusFilter = filter === 'all' ? undefined : filter;
        await fetchEvents(statusFilter, pagination.page);
      }
      
      alert('Successfully joined the event!');
    } catch (err) {
      console.error('Error joining event:', err);
      alert(err instanceof Error ? err.message : 'Failed to join event');
    } finally {
      setJoiningEventId(null);
    }
  };

  const handleEventDetails = async (eventId: string) => {
    try {
      const event = await eventService.getEvent(eventId);
      console.log('Event details:', event);
      // You could navigate to a detailed event page or show a modal
      // navigate(`/events/${eventId}`);
    } catch (err) {
      console.error('Error fetching event details:', err);
      alert(err instanceof Error ? err.message : 'Failed to fetch event details');
    }
  };

  const getStatusColor = (status: Event['status']) => {
    switch (status) {
      case 'published': return 'text-green-600 bg-green-100';
      case 'draft': return 'text-yellow-600 bg-yellow-100';
      case 'cancelled': return 'text-red-600 bg-red-100';
      case 'postponed': return 'text-orange-600 bg-orange-100';
      case 'completed': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: Event['status']) => {
    switch (status) {
      case 'published': return 'Published';
      case 'draft': return 'Draft';
      case 'cancelled': return 'Cancelled';
      case 'postponed': return 'Postponed';
      case 'completed': return 'Completed';
      default: return status;
    }
  };

  const isEventAvailable = (event: EventListResponse) => {
    return event.status === 'published' && event.next_schedule;
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const handlePageChange = (newPage: number) => {
    if (isSearching && searchQuery) {
      handleSearch(searchQuery, newPage);
    } else {
      const statusFilter = filter === 'all' ? undefined : filter;
      fetchEvents(statusFilter, newPage);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSearch(searchQuery, 1);
  };

  const handleFilterChange = (newFilter: 'all' | Event['status']) => {
    setFilter(newFilter);
    setSearchQuery('');
    setIsSearching(false);
  };

  // Transform user data for navbar to ensure consistent format
  const navbarUser = user ? {
    firstName: user.firstName,
    lastName: user.lastName,
    role: user.role
  } : null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar user={navbarUser} isAuthenticated={true} />

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8 gap-4">
            <div>
              <h1 className="text-3xl font-display font-bold text-foreground">
                {isSearching ? `Search Results for "${searchQuery}"` : 'Available Events'}
              </h1>
              <p className="mt-2 text-muted-foreground">
                {isSearching 
                  ? `Found ${pagination.total} events matching your search`
                  : 'Discover and join exciting events in your area.'
                }
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 w-full lg:w-auto">
              {/* Search Form */}
              <form onSubmit={handleSearchSubmit} className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search events..."
                  className="px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Search
                </button>
                {isSearching && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery('');
                      setIsSearching(false);
                      setFilter('all');
                    }}
                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors"
                  >
                    Clear
                  </button>
                )}
              </form>
              
              {/* Filter Buttons */}
              {!isSearching && (
                <div className="flex flex-wrap gap-2">
                  {(['all', 'published', 'draft', 'cancelled', 'postponed', 'completed'] as const).map((status) => (
                    <button
                      key={status}
                      onClick={() => handleFilterChange(status)}
                      className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                        filter === status
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                      }`}
                    >
                      {status === 'all' ? 'All' : getStatusText(status)}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-6 bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md">
              <p className="font-medium">Error loading events:</p>
              <p className="text-sm">{error}</p>
              <button 
                onClick={() => {
                  if (isSearching && searchQuery) {
                    handleSearch(searchQuery, pagination.page);
                  } else {
                    fetchEvents(filter === 'all' ? undefined : filter, pagination.page);
                  }
                }}
                className="mt-2 text-sm underline hover:no-underline"
              >
                Try again
              </button>
            </div>
          )}

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              <p className="mt-2 text-muted-foreground">Loading events...</p>
            </div>
          ) : (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {events.map((event) => (
                  <div key={event.id} className="bg-card border border-border rounded-lg shadow-card hover:shadow-lg transition-shadow p-6">
                    <div className="flex justify-between items-start mb-4">
                      <h3 className="text-xl font-display font-semibold text-foreground">
                        {event.title}
                      </h3>
                      <span className={`px-2 py-1 rounded-md text-xs font-medium ${getStatusColor(event.status)}`}>
                        {getStatusText(event.status)}
                      </span>
                    </div>
                    
                    {event.poster_image_url && (
                      <img 
                        src={event.poster_image_url} 
                        alt={event.title}
                        className="w-full h-48 object-cover rounded-md mb-4"
                      />
                    )}
                    
                    <p className="text-muted-foreground mb-4 text-sm">
                      {event.short_description || 'No description available'}
                    </p>
                    
                    <div className="space-y-2 mb-4">
                      {event.next_schedule && (
                        <div className="flex items-center text-sm text-muted-foreground">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          {formatDateTime(event.next_schedule.start_datetime)}
                        </div>
                      )}
                      
                      {event.venue && (
                        <div className="flex items-center text-sm text-muted-foreground">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          {event.venue.name}, {event.venue.city}
                        </div>
                      )}
                      
                      {event.artist_performer && (
                        <div className="flex items-center text-sm text-muted-foreground">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                          </svg>
                          {event.artist_performer}
                        </div>
                      )}

                      {event.min_price && (
                        <div className="flex items-center text-sm text-muted-foreground">
                          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                          </svg>
                          From ${event.min_price}
                        </div>
                      )}

                      {event.tags && event.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {event.tags.slice(0, 3).map((tag, index) => (
                            <span key={index} className="text-xs bg-primary/10 text-primary px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                          {event.tags.length > 3 && (
                            <span className="text-xs text-muted-foreground">+{event.tags.length - 3} more</span>
                          )}
                        </div>
                      )}
                    </div>
                    
                    <div className="flex space-x-2">
                      <button 
                        onClick={() => handleJoinEvent(event.id)}
                        disabled={!isEventAvailable(event) || joiningEventId === event.id}
                        className="flex-1 bg-primary text-primary-foreground py-2 px-4 rounded-md hover:bg-primary/90 transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {joiningEventId === event.id ? 'Joining...' : 
                         !isEventAvailable(event) ? 'Not Available' : 'Join Event'}
                      </button>
                      <button 
                        onClick={() => handleEventDetails(event.id)}
                        className="bg-secondary text-secondary-foreground py-2 px-4 rounded-md hover:bg-secondary/80 transition-colors text-sm font-medium"
                      >
                        Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              {pagination.pages > 1 && (
                <div className="flex justify-center items-center space-x-2 mt-8">
                  <button
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <span className="px-4 py-2 text-sm text-muted-foreground">
                    Page {pagination.page} of {pagination.pages} ({pagination.total} total events)
                  </span>
                  
                  <button
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page >= pagination.pages}
                    className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}

          {events.length === 0 && !loading && !error && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                {isSearching ? 'No events found matching your search criteria.' : 'No events found for the selected filter.'}
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default EventsPage;