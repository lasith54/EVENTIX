import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Calendar, MapPin, Users, Star, Clock } from 'lucide-react';
import concertImage from '@/assets/hero-concert.jpg';
import conferenceImage from '@/assets/conference-event.jpg';
import sportsImage from '@/assets/sports-event.jpg';
import artImage from '@/assets/art-event.jpg';

const FeaturedEvents = () => {
  const events = [
    {
      id: 1,
      title: "Summer Music Festival 2024",
      image: concertImage,
      category: "Music",
      date: "July 15, 2024",
      time: "7:00 PM",
      location: "Central Park, New York",
      price: "$89",
      attendees: "2.5K",
      rating: 4.9,
      organizer: "MusicLive Events",
      description: "Experience the hottest artists and bands in an unforgettable outdoor festival.",
      tags: ["Festival", "Outdoor", "Multi-day"]
    },
    {
      id: 2,
      title: "Tech Innovation Conference",
      image: conferenceImage,
      category: "Technology",
      date: "August 22, 2024",
      time: "9:00 AM",
      location: "Convention Center, San Francisco",
      price: "$299",
      attendees: "1.2K",
      rating: 4.8,
      organizer: "TechForward",
      description: "Join industry leaders discussing the future of technology and innovation.",
      tags: ["Conference", "Networking", "Professional"]
    },
    {
      id: 3,
      title: "Championship Soccer Match",
      image: sportsImage,
      category: "Sports",
      date: "September 10, 2024",
      time: "3:00 PM",
      location: "MetLife Stadium, New Jersey",
      price: "$156",
      attendees: "45K",
      rating: 4.7,
      organizer: "Premier League",
      description: "Watch the season's most anticipated match between top-tier teams.",
      tags: ["Sports", "Championship", "Stadium"]
    },
    {
      id: 4,
      title: "Contemporary Art Exhibition",
      image: artImage,
      category: "Art",
      date: "October 5, 2024",
      time: "6:00 PM",
      location: "Modern Art Museum, Los Angeles",
      price: "$45",
      attendees: "800",
      rating: 4.6,
      organizer: "ArtSpace Gallery",
      description: "Discover groundbreaking contemporary artworks from emerging artists.",
      tags: ["Exhibition", "Gallery", "Cultural"]
    }
  ];

  return (
    <section className="py-20 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-primary/5 to-transparent"></div>
      
      <div className="container mx-auto px-4 relative">
        {/* Section Header */}
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-primary/20 text-primary border-primary/30">
            Featured Events
          </Badge>
          <h2 className="text-4xl md:text-5xl font-display font-bold">
            Don't Miss These
            <span className="block gradient-text">Amazing Events</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Handpicked events that guarantee unforgettable experiences
          </p>
        </div>

        {/* Events Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {events.map((event, index) => (
            <Card 
              key={event.id} 
              className="group glass-card border-white/10 hover-glow overflow-hidden"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="relative">
                <img
                  src={event.image}
                  alt={event.title}
                  className="w-full h-48 object-cover transition-transform duration-500 group-hover:scale-105"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"></div>
                <div className="absolute top-4 left-4">
                  <Badge className="bg-primary/90 text-primary-foreground">
                    {event.category}
                  </Badge>
                </div>
                <div className="absolute top-4 right-4">
                  <div className="flex items-center space-x-1 bg-black/50 rounded-full px-2 py-1">
                    <Star className="h-3 w-3 text-yellow-400 fill-current" />
                    <span className="text-xs text-white">{event.rating}</span>
                  </div>
                </div>
                <div className="absolute bottom-4 right-4">
                  <div className="text-right">
                    <div className="text-2xl font-bold text-white">{event.price}</div>
                    <div className="text-xs text-white/80">per ticket</div>
                  </div>
                </div>
              </div>

              <CardContent className="p-6 space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-foreground group-hover:text-primary transition-colors mb-2">
                    {event.title}
                  </h3>
                  <p className="text-muted-foreground text-sm">
                    {event.description}
                  </p>
                </div>

                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{event.date}</span>
                    <Clock className="h-4 w-4 ml-2" />
                    <span>{event.time}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <MapPin className="h-4 w-4" />
                    <span>{event.location}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Users className="h-4 w-4" />
                    <span>{event.attendees} attending</span>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  {event.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-white/10">
                  <div className="text-sm text-muted-foreground">
                    by {event.organizer}
                  </div>
                  <Button variant="gradient">
                    Book Now
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* View All Button */}
        <div className="text-center">
          <Button size="lg" variant="outline" className="border-white/20 hover:bg-white/10 px-8 py-4">
            View All Events
          </Button>
        </div>
      </div>
    </section>
  );
};

export default FeaturedEvents;