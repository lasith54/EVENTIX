import React, { useState, useEffect } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { authService } from '@/services/auth';
import { Navbar } from '@/components';

// Types based on actual API response
interface VenueSection {
  id: string;
  venue_id: string;
  name: string;
  description: string;
  capacity: number;
  seat_map: any;
  created_at: string;
}

interface Venue {
  id: string;
  name: string;
  description: string;
  venue_type: string;
  address: string;
  city: string;
  state: string;
  country: string;
  postal_code: string;
  latitude: string;
  longitude: string;
  capacity: number;
  image_urls: string[];
  amenities: string[];
  contact_info: any;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  sections: VenueSection[];
}

interface Category {
  id: string;
  name: string;
  description: string;
  parent_id: string;
  is_active: boolean;
  created_at: string;
  subcategories: string[];
}

interface EventSchedule {
  id: string;
  event_id: string;
  start_datetime: string;
  end_datetime: string;
  doors_open_time: string;
  timezone: string;
  booking_opens_at: string;
  booking_closes_at: string;
  early_bird_ends_at: string;
  is_cancelled: boolean;
  cancellation_reason: string;
  is_sold_out: boolean;
  special_notes: string;
  created_at: string;
  updated_at: string;
}

interface PricingTier {
  id: string;
  event_id: string;
  venue_section_id: string;
  tier_name: string;
  price: string;
  currency: string;
  total_seats: number;
  available_seats: number;
  min_purchase: number;
  max_purchase: number;
  sale_starts_at: string;
  sale_ends_at: string;
  includes_benefits: string[];
  seat_type: string;
  is_active: boolean;
  is_sold_out: boolean;
  created_at: string;
  updated_at: string;
  venue_section: VenueSection;
}

interface Event {
  id: string;
  title: string;
  description: string;
  short_description: string;
  event_type: string;
  status: string;
  venue_id: string;
  category_id: string;
  artist_performer: string;
  organizer: string;
  duration_minutes: number;
  age_restriction: string;
  poster_image_url: string;
  banner_image_url: string;
  gallery_images: string[];
  video_urls: string[];
  slug: string;
  tags: string[];
  metadata: any;
  created_at: string;
  updated_at: string;
  venue: Venue;
  category: Category;
  schedules: EventSchedule[];
  pricing_tiers: PricingTier[];
}

// Booking types based on the actual API structure
interface BookingItem {
  seat_id: string;
  venue_section_id: string;
  unit_price: number;
  quantity: number;
  section_name: string;
  seat_row: string;
  seat_number: string;
  pricing_tier: string;
}

interface BookingCreate {
  event_id: string;
  total_amount: number;
  currency: string;
  special_requests?: string;
  customer_email: string;
  customer_phone: string;
  customer_name: string;
  items: BookingItem[];
  payment_method: string;
}

const BookingPage: React.FC = () => {
  const navigate = useNavigate();
  const { eventId } = useParams<{ eventId: string }>();
  
  // State management
  const [event, setEvent] = useState<Event | null>(null);
  const [selectedSchedule, setSelectedSchedule] = useState<EventSchedule | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState(authService.getUser());

  // Booking form state
  const [selectedTickets, setSelectedTickets] = useState<{ [key: string]: number }>({});
  const [specialRequests, setSpecialRequests] = useState('');
  const [paymentMethod, setPaymentMethod] = useState<string>('credit_card'); // Fixed: Changed from 'string' literal to string type
  
  // Contact information state
  const [contactInfo, setContactInfo] = useState({
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
    email: user?.email || '',
    phone: '',
  });

  // Fetch event details
  useEffect(() => {
    const fetchEventData = async () => {
      if (!eventId) {
        setError('Event ID not provided');
        setLoading(false);
        return;
      }

      if (!authService.isAuthenticated()) {
        setError('Please log in to continue booking');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const token = authService.getToken();
        if (!token) {
          throw new Error('Authentication token not found');
        }

        console.log('Fetching event details for ID:', eventId);

        const response = await fetch(`http://localhost:8001/api/v1/events/${eventId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        console.log('Event API response status:', response.status);

        if (!response.ok) {
          if (response.status === 404) {
            throw new Error('Event not found');
          } else if (response.status === 401) {
            throw new Error('Authentication required');
          } else {
            const errorText = await response.text();
            throw new Error(`Failed to fetch event: ${response.status} ${errorText}`);
          }
        }

        const eventData: Event = await response.json();
        console.log('Event data received:', eventData);

        setEvent(eventData);

        // Set the first active schedule as default
        const activeSchedules = eventData.schedules?.filter(s => !s.is_cancelled && !s.is_sold_out) || [];
        if (activeSchedules.length > 0) {
          setSelectedSchedule(activeSchedules[0]);
        }

      } catch (err) {
        console.error('Error fetching event data:', err);
        const errorMessage = err instanceof Error ? err.message : 'Failed to load event data';
        setError(`Unable to load event details: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchEventData();
  }, [eventId]);

  // Get available pricing tiers for selected schedule
  const getAvailablePricingTiers = (): PricingTier[] => {
    if (!event || !selectedSchedule) return [];

    const now = new Date();
    return event.pricing_tiers?.filter(tier => {
      if (!tier.is_active || tier.is_sold_out || tier.available_seats <= 0) {
        return false;
      }

      // Check sale dates
      const saleStartsAt = tier.sale_starts_at ? new Date(tier.sale_starts_at) : null;
      const saleEndsAt = tier.sale_ends_at ? new Date(tier.sale_ends_at) : null;

      if (saleStartsAt && now < saleStartsAt) return false;
      if (saleEndsAt && now > saleEndsAt) return false;

      return true;
    }) || [];
  };

  // Generate seat ID (simplified - in real implementation, this would come from seat selection)
  const generateSeatId = (tier: PricingTier, index: number): string => {
    return `${tier.venue_section_id}-${tier.seat_type}-${index + 1}`;
  };

  // Generate seat row and number (simplified)
  const generateSeatInfo = (tier: PricingTier, index: number) => {
    const rowLetter = String.fromCharCode(65 + Math.floor(index / 10)); // A, B, C, etc.
    const seatNumber = (index % 10) + 1;
    return {
      seat_row: `Row ${rowLetter}`,
      seat_number: seatNumber.toString(),
    };
  };

  // Handle ticket quantity change
  const handleTicketQuantityChange = (tierId: string, quantity: number) => {
    const tier = event?.pricing_tiers?.find(t => t.id === tierId);
    if (!tier) return;

    const maxAllowed = Math.min(tier.available_seats, tier.max_purchase || tier.available_seats);
    const minRequired = tier.min_purchase || 0;

    // Ensure quantity is within bounds
    const validQuantity = Math.max(0, Math.min(quantity, maxAllowed));

    setSelectedTickets(prev => ({
      ...prev,
      [tierId]: validQuantity,
    }));
  };

  // Calculate total price
  const calculateTotal = () => {
    const availableTiers = getAvailablePricingTiers();
    return availableTiers.reduce((total, tier) => {
      const quantity = selectedTickets[tier.id] || 0;
      return total + (quantity * parseFloat(tier.price));
    }, 0);
  };

  // Get total tickets selected
  const getTotalTickets = () => {
    return Object.values(selectedTickets).reduce((total, quantity) => total + quantity, 0);
  };

  const handleTokenExpiration = () => {
    authService.logout();
    navigate('/login', { 
      state: { 
        returnTo: `/booking/${eventId}`,
        message: 'Your session has expired. Please log in again to continue booking.'
      }
    });
  };

  // Validate ticket selection
  const validateTicketSelection = (): string | null => {
    const totalTickets = getTotalTickets();
    if (totalTickets === 0) {
      return 'Please select at least one ticket';
    }

    // Check min purchase requirements
    const availableTiers = getAvailablePricingTiers();
    for (const tier of availableTiers) {
      const quantity = selectedTickets[tier.id] || 0;
      if (quantity > 0 && tier.min_purchase && quantity < tier.min_purchase) {
        return `${tier.tier_name} requires minimum ${tier.min_purchase} tickets`;
      }
    }

    // Validate contact information
    if (!contactInfo.firstName.trim() || !contactInfo.lastName.trim()) {
      return 'Please enter your full name';
    }

    if (!contactInfo.email.trim() || !contactInfo.email.includes('@')) {
      return 'Please enter a valid email address';
    }

    return null;
  };

  // Handle form submission - Fixed syntax and logic
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!event || !eventId || !selectedSchedule) {
      setError('Event or schedule information not available');
      return;
    }

    const validationError = validateTicketSelection();
    if (validationError) {
      setError(validationError);
      return;
    }

    // Check if user is still authenticated and token is valid
    if (!authService.isAuthenticated()) {
      setError('Please log in to complete booking');
      return;
    }

    // Validate token before proceeding
    try {
      const isValid = await authService.validateAuth();
      if (!isValid) {
        handleTokenExpiration();
        return;
      }
    } catch (error) {
      console.error('Token validation failed:', error);
      handleTokenExpiration();
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const availableTiers = getAvailablePricingTiers();
      
      // Prepare booking items with seat information
      const items: BookingItem[] = [];
      let seatIndex = 0;

      availableTiers.forEach(tier => {
        const quantity = selectedTickets[tier.id] || 0;
        if (quantity > 0) {
          // Create items for each ticket in this tier
          for (let i = 0; i < quantity; i++) {
            const seatInfo = generateSeatInfo(tier, seatIndex + i);
            items.push({
              seat_id: generateSeatId(tier, seatIndex + i),
              venue_section_id: tier.venue_section_id,
              unit_price: parseFloat(tier.price),
              quantity: 1, // Each item represents one seat
              section_name: tier.venue_section?.name || `Section ${tier.tier_name}`,
              seat_row: seatInfo.seat_row,
              seat_number: seatInfo.seat_number,
              pricing_tier: tier.tier_name,
            });
          }
          seatIndex += quantity;
        }
      });

      // Get currency from the first available tier
      const currency = availableTiers[0]?.currency || 'LKR';
      const totalAmount = calculateTotal();
      const customerName = `${contactInfo.firstName.trim()} ${contactInfo.lastName.trim()}`;

      const bookingData: BookingCreate = {
        event_id: eventId,
        total_amount: totalAmount,
        currency: currency,
        special_requests: specialRequests || undefined,
        customer_email: contactInfo.email.trim(),
        customer_phone: contactInfo.phone.trim() || '',
        customer_name: customerName,
        items: items,
        payment_method: paymentMethod,
      };

      console.log('Submitting booking:', bookingData);

      const token = authService.getToken();
      if (!token) {
        throw new Error('Authentication token not found');
      }

      const response = await fetch('http://localhost:8002/api/v1/bookings/create', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(bookingData),
      });

      console.log('Booking response status:', response.status);

      if (!response.ok) {
        if (response.status === 401) {
          handleTokenExpiration();
          return;
        }
        const errorData = await response.json().catch(() => ({ detail: 'Booking failed' }));
        throw new Error(errorData.detail || errorData.message || `Booking failed with status: ${response.status}`);
      }

      const booking = await response.json();
      console.log('Booking created successfully:', booking);

      // Debug: Log the booking response to see its structure
      console.log('Booking response structure:', JSON.stringify(booking, null, 2));

      // Create a normalized booking object for the payment page
      const paymentBookingData = {
        id: booking.id || booking.booking_id || booking._id || null, // Try different possible ID fields
        event_id: eventId,
        total_amount: totalAmount,
        currency: currency,
        customer_name: customerName,
        customer_email: contactInfo.email.trim(),
        customer_phone: contactInfo.phone.trim() || '',
        items: items,
        event_title: event.title,
        // Include the entire booking response for debugging
        _raw_booking_response: booking,
      };

      console.log('Navigating to payment with data:', paymentBookingData);

      // Validate that we have an ID before navigating
      if (!paymentBookingData.id) {
        console.error('No booking ID found in response. Available fields:', Object.keys(booking));
        setError('Booking was created but no booking ID was returned. Please contact support.');
        return;
      }

      // Navigate to payment page regardless of payment method (removed stripe condition)
      navigate(`/payment/${paymentBookingData.id}`, {
        state: {
          booking: paymentBookingData,
          selectedPaymentMethod: paymentMethod
        }
      });

    } catch (err) {
      console.error('Booking error:', err);
      if (err instanceof Error && err.message.includes('Could not validate credentials')) {
        handleTokenExpiration();
        return;
      }
      setError(err instanceof Error ? err.message : 'Failed to create booking');
    } finally {
      setSubmitting(false);
    }
  }; // Fixed: Properly closed the handleSubmit function

  // Handle contact info change
  const handleContactInfoChange = (field: string, value: string) => {
    setContactInfo(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Format date helper
  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Invalid date';
    }
  };

  const formatTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleTimeString();
    } catch {
      return 'Invalid time';
    }
  };

  const formatDateTime = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Invalid date/time';
    }
  };

  // Check if booking is open
  const isBookingOpen = (schedule: EventSchedule): boolean => {
    const now = new Date();
    const bookingOpensAt = schedule.booking_opens_at ? new Date(schedule.booking_opens_at) : null;
    const bookingClosesAt = schedule.booking_closes_at ? new Date(schedule.booking_closes_at) : null;

    if (bookingOpensAt && now < bookingOpensAt) return false;
    if (bookingClosesAt && now > bookingClosesAt) return false;

    return !schedule.is_cancelled && !schedule.is_sold_out;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} isAuthenticated={!!user} />
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <p className="mt-2 text-muted-foreground">Loading event details...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !event) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-background to-yellow-100/50">
        <Navbar user={user} isAuthenticated={!!user} />
        <div className="flex items-center justify-center py-20">
          <div className="text-center max-w-md mx-auto">
            <p className="text-destructive mb-4">{error}</p>
            <div className="space-y-2">
              <button 
                onClick={() => {
                  setError(null);
                  setLoading(true);
                  window.location.reload();
                }}
                className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 mr-2"
              >
                Retry
              </button>
              <button 
                onClick={() => navigate('/events')}
                className="bg-secondary text-secondary-foreground px-4 py-2 rounded-md hover:bg-secondary/80"
              >
                Back to Events
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!event) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar user={user} isAuthenticated={!!user} />
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <p className="text-muted-foreground">Event not found</p>
          </div>
        </div>
      </div>
    );
  }

  const availableTiers = getAvailablePricingTiers();
  const activeSchedules = event.schedules?.filter(s => isBookingOpen(s)) || [];

  return (
    <div className="min-h-screen bg-background">
      <Navbar user={user} isAuthenticated={!!user} />

      <main className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate('/events')}
            className="flex items-center text-primary hover:text-primary/80 mb-4"
          >
            <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to Events
          </button>
          
          <h1 className="text-3xl font-display font-bold text-foreground mb-2">
            Book Event
          </h1>
          <p className="text-muted-foreground">
            Complete your booking for this amazing event
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Booking Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Event Summary */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Event Details
                </h2>
                
                {/* Event Image */}
                {event.poster_image_url && (
                  <img 
                    src={event.poster_image_url} 
                    alt={event.title}
                    className="w-full h-48 object-cover rounded-md mb-4"
                  />
                )}
                
                <div className="space-y-3">
                  <h3 className="text-lg font-medium text-foreground">{event.title}</h3>
                  
                  {event.short_description && (
                    <p className="text-muted-foreground text-sm">
                      {event.short_description}
                    </p>
                  )}

                  {event.artist_performer && (
                    <p className="text-sm">
                      <span className="font-medium">Artist:</span> {event.artist_performer}
                    </p>
                  )}

                  {event.duration_minutes > 0 && (
                    <p className="text-sm">
                      <span className="font-medium">Duration:</span> {event.duration_minutes} minutes
                    </p>
                  )}

                  {event.age_restriction && (
                    <p className="text-sm">
                      <span className="font-medium">Age Restriction:</span> {event.age_restriction}
                    </p>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Category:</span>
                      <span className="ml-2">{event.category?.name || 'N/A'}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Event Type:</span>
                      <span className="ml-2 capitalize">{event.event_type}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Venue:</span>
                      <span className="ml-2">{event.venue?.name}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Location:</span>
                      <span className="ml-2">{event.venue?.city}, {event.venue?.state}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Schedule Selection */}
              {activeSchedules.length > 1 && (
                <div className="bg-card border border-border rounded-lg p-6">
                  <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                    Select Schedule
                  </h2>
                  <div className="space-y-2">
                    {activeSchedules.map((schedule) => (
                      <label 
                        key={schedule.id} 
                        className="flex items-center p-3 border border-border rounded-lg cursor-pointer hover:bg-secondary/50"
                      >
                        <input
                          type="radio"
                          name="schedule"
                          checked={selectedSchedule?.id === schedule.id}
                          onChange={() => setSelectedSchedule(schedule)}
                          className="mr-3"
                        />
                        <div>
                          <p className="font-medium">{formatDateTime(schedule.start_datetime)}</p>
                          {schedule.doors_open_time && (
                            <p className="text-sm text-muted-foreground">
                              Doors open: {formatTime(schedule.doors_open_time)}
                            </p>
                          )}
                          {schedule.special_notes && (
                            <p className="text-sm text-muted-foreground">
                              {schedule.special_notes}
                            </p>
                          )}
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              {/* Schedule Info for Single Schedule */}
              {activeSchedules.length === 1 && selectedSchedule && (
                <div className="bg-card border border-border rounded-lg p-6">
                  <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                    Event Schedule
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Start:</span>
                      <span className="ml-2">{formatDateTime(selectedSchedule.start_datetime)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">End:</span>
                      <span className="ml-2">{formatDateTime(selectedSchedule.end_datetime)}</span>
                    </div>
                    {selectedSchedule.doors_open_time && (
                      <div>
                        <span className="text-muted-foreground">Doors Open:</span>
                        <span className="ml-2">{formatTime(selectedSchedule.doors_open_time)}</span>
                      </div>
                    )}
                    {selectedSchedule.timezone && (
                      <div>
                        <span className="text-muted-foreground">Timezone:</span>
                        <span className="ml-2">{selectedSchedule.timezone}</span>
                      </div>
                    )}
                  </div>
                  {selectedSchedule.special_notes && (
                    <div className="mt-3">
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium">Note:</span> {selectedSchedule.special_notes}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Ticket Selection */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Select Tickets
                </h2>
                {availableTiers.length > 0 ? (
                  <div className="space-y-4">
                    {availableTiers.map((tier) => (
                      <div key={tier.id} className="p-4 border border-border rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex-1">
                            <h3 className="font-medium text-foreground">{tier.tier_name}</h3>
                            <p className="text-sm text-muted-foreground">
                              {tier.venue_section?.name} - {tier.seat_type}
                            </p>
                            {tier.includes_benefits && tier.includes_benefits.length > 0 && (
                              <div className="mt-1">
                                <p className="text-xs text-muted-foreground">Includes:</p>
                                <ul className="text-xs text-muted-foreground list-disc list-inside">
                                  {tier.includes_benefits.slice(0, 3).map((benefit, index) => (
                                    <li key={index}>{benefit}</li>
                                  ))}
                                  {tier.includes_benefits.length > 3 && (
                                    <li>+{tier.includes_benefits.length - 3} more benefits</li>
                                  )}
                                </ul>
                              </div>
                            )}
                          </div>
                          <div className="text-right">
                            <span className="font-semibold text-foreground text-lg">
                              {tier.currency} {parseFloat(tier.price).toFixed(2)}
                            </span>
                          </div>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="text-sm text-muted-foreground">
                            <p>Available: {tier.available_seats}</p>
                            {tier.min_purchase > 0 && (
                              <p>Min purchase: {tier.min_purchase}</p>
                            )}
                            {tier.max_purchase > 0 && tier.max_purchase < tier.available_seats && (
                              <p>Max purchase: {tier.max_purchase}</p>
                            )}
                          </div>

                          <div className="flex items-center space-x-2">
                            <button
                              type="button"
                              onClick={() => handleTicketQuantityChange(
                                tier.id, 
                                (selectedTickets[tier.id] || 0) - 1
                              )}
                              className="w-8 h-8 rounded-full border border-border flex items-center justify-center hover:bg-secondary disabled:opacity-50"
                              disabled={!selectedTickets[tier.id] || selectedTickets[tier.id] <= 0}
                            >
                              -
                            </button>
                            <span className="w-12 text-center font-medium">
                              {selectedTickets[tier.id] || 0}
                            </span>
                            <button
                              type="button"
                              onClick={() => handleTicketQuantityChange(
                                tier.id, 
                                (selectedTickets[tier.id] || 0) + 1
                              )}
                              className="w-8 h-8 rounded-full border border-border flex items-center justify-center hover:bg-secondary disabled:opacity-50"
                              disabled={(selectedTickets[tier.id] || 0) >= Math.min(tier.available_seats, tier.max_purchase || tier.available_seats)}
                            >
                              +
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <p className="text-muted-foreground">
                      {activeSchedules.length === 0 
                        ? 'No active schedules available for booking'
                        : 'No tickets available for this event'
                      }
                    </p>
                  </div>
                )}
              </div>

              {/* Contact Information */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Contact Information
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      First Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={contactInfo.firstName}
                      onChange={(e) => handleContactInfoChange('firstName', e.target.value)}
                      className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Last Name *
                    </label>
                    <input
                      type="text"
                      required
                      value={contactInfo.lastName}
                      onChange={(e) => handleContactInfoChange('lastName', e.target.value)}
                      className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Email *
                    </label>
                    <input
                      type="email"
                      required
                      value={contactInfo.email}
                      onChange={(e) => handleContactInfoChange('email', e.target.value)}
                      className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-foreground mb-2">
                      Phone Number
                    </label>
                    <input
                      type="tel"
                      value={contactInfo.phone}
                      onChange={(e) => handleContactInfoChange('phone', e.target.value)}
                      className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                      placeholder="Optional"
                    />
                  </div>
                </div>
              </div>

              {/* Payment Method - Fixed all the type comparisons and state updates */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Payment Method
                </h2>
                <div className="space-y-3">
                  <label className="flex items-center p-3 border border-border rounded-lg cursor-pointer hover:bg-secondary/50">
                    <input
                      type="radio"
                      name="paymentMethod"
                      value="credit_card"
                      checked={paymentMethod === 'credit_card'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="mr-3"
                    />
                    <div className="flex items-center">
                      <div className="w-8 h-5 bg-blue-600 rounded mr-3 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">💳</span>
                      </div>
                      <div>
                        <p className="font-medium">Credit/Debit Card</p>
                        <p className="text-sm text-muted-foreground">Visa, Mastercard, American Express</p>
                      </div>
                    </div>
                  </label>
                  
                  <label className="flex items-center p-3 border border-border rounded-lg cursor-pointer hover:bg-secondary/50">
                    <input
                      type="radio"
                      name="paymentMethod"
                      value="bank_transfer"
                      checked={paymentMethod === 'bank_transfer'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="mr-3"
                    />
                    <div className="flex items-center">
                      <div className="w-8 h-5 bg-green-600 rounded mr-3 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">🏦</span>
                      </div>
                      <div>
                        <p className="font-medium">Bank Transfer</p>
                        <p className="text-sm text-muted-foreground">Direct bank transfer</p>
                      </div>
                    </div>
                  </label>

                  <label className="flex items-center p-3 border border-border rounded-lg cursor-pointer hover:bg-secondary/50">
                    <input
                      type="radio"
                      name="paymentMethod"
                      value="digital_wallet"
                      checked={paymentMethod === 'digital_wallet'}
                      onChange={(e) => setPaymentMethod(e.target.value)}
                      className="mr-3"
                    />
                    <div className="flex items-center">
                      <div className="w-8 h-5 bg-purple-600 rounded mr-3 flex items-center justify-center">
                        <span className="text-white text-xs font-bold">📱</span>
                      </div>
                      <div>
                        <p className="font-medium">Digital Wallet</p>
                        <p className="text-sm text-muted-foreground">PayPal, Apple Pay, Google Pay</p>
                      </div>
                    </div>
                  </label>
                </div>
              </div>

              {/* Special Requests */}
              <div className="bg-card border border-border rounded-lg p-6">
                <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                  Special Requests
                </h2>
                <textarea
                  value={specialRequests}
                  onChange={(e) => setSpecialRequests(e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Any special requirements or requests for your booking..."
                />
              </div>

              {/* Error Message */}
              {error && (
                <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-md">
                  <p className="text-sm">{error}</p>
                </div>
              )}
            </form>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-card border border-border rounded-lg p-6 sticky top-6">
              <h2 className="text-xl font-display font-semibold text-foreground mb-4">
                Order Summary
              </h2>
              
              {getTotalTickets() > 0 ? (
                <div className="space-y-4">
                  {availableTiers
                    .filter(tier => selectedTickets[tier.id] > 0)
                    .map(tier => (
                      <div key={tier.id} className="space-y-2">
                        <div className="flex justify-between">
                          <div>
                            <p className="font-medium text-foreground">{tier.tier_name}</p>
                            <p className="text-sm text-muted-foreground">
                              {selectedTickets[tier.id]} × {tier.currency} {parseFloat(tier.price).toFixed(2)}
                            </p>
                          </div>
                          <p className="font-medium text-foreground">
                            {tier.currency} {(selectedTickets[tier.id] * parseFloat(tier.price)).toFixed(2)}
                          </p>
                        </div>
                        
                        {/* Show seat assignments */}
                        <div className="text-xs text-muted-foreground pl-2">
                          {Array.from({ length: selectedTickets[tier.id] }, (_, i) => {
                            const seatInfo = generateSeatInfo(tier, i);
                            return (
                              <div key={i}>
                                {tier.venue_section?.name} - {seatInfo.seat_row} - Seat {seatInfo.seat_number}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))}
                  
                  <hr className="border-border" />
                  
                  <div className="flex justify-between items-center">
                    <p className="text-lg font-semibold text-foreground">Total</p>
                    <p className="text-lg font-semibold text-foreground">
                      {availableTiers[0]?.currency || 'LKR'} {calculateTotal().toFixed(2)}
                    </p>
                  </div>
                  
                  <div className="text-xs text-muted-foreground">
                    <p>Payment Method: {
                      paymentMethod === 'credit_card' ? 'Credit/Debit Card' : 
                      paymentMethod === 'bank_transfer' ? 'Bank Transfer' :
                      paymentMethod === 'digital_wallet' ? 'Digital Wallet' : 'Unknown'
                    }</p>
                    {contactInfo.firstName && contactInfo.lastName && (
                      <p>Customer: {contactInfo.firstName} {contactInfo.lastName}</p>
                    )}
                  </div>
                  
                  <button
                    type="submit"
                    onClick={handleSubmit}
                    disabled={submitting || getTotalTickets() === 0 || !selectedSchedule || availableTiers.length === 0}
                    className="w-full bg-primary text-primary-foreground py-3 px-4 rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {submitting ? (
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </div>
                    ) : (
                      `Complete Booking - ${availableTiers[0]?.currency || 'LKR'} ${calculateTotal().toFixed(2)}`
                    )}
                  </button>

                  {!selectedSchedule && activeSchedules.length > 1 && (
                    <p className="text-xs text-muted-foreground text-center">
                      Please select a schedule to continue
                    </p>
                  )}
                </div>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No tickets selected</p>
                  <p className="text-sm text-muted-foreground mt-2">
                    {availableTiers.length > 0 
                      ? 'Select tickets to see your order summary'
                      : 'No tickets available for booking'
                    }
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default BookingPage;