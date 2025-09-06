import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Search, Calendar, MapPin, Users, Star } from 'lucide-react';
import heroImage from '@/assets/hero-concert.jpg';

const HeroSection = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background Image with Overlay */}
      <div className="absolute inset-0">
        <img
          src={heroImage}
          alt="Concert venue with vibrant lighting"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-background/90 via-background/70 to-background/50"></div>
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent"></div>
      </div>

      {/* Floating Elements */}
      <div className="absolute top-20 left-10 hidden lg:block">
        <div className="glass-card p-4 floating-animation">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-primary" />
            <span className="text-sm text-foreground">50+ Events This Week</span>
          </div>
        </div>
      </div>

      <div className="absolute top-32 right-10 hidden lg:block">
        <div className="glass-card p-4 floating-animation" style={{ animationDelay: '2s' }}>
          <div className="flex items-center space-x-2">
            <Users className="h-5 w-5 text-accent" />
            <span className="text-sm text-foreground">10K+ Happy Customers</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center space-y-8 slide-in-up">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 glass-card px-4 py-2 rounded-full">
            <Star className="h-4 w-4 text-accent" />
            <span className="text-sm font-medium">Trusted by 50,000+ Event Organizers</span>
          </div>

          {/* Main Heading */}
          <div className="space-y-4">
            <h1 className="text-5xl md:text-7xl font-display font-bold leading-tight">
              Discover Amazing
              <span className="block gradient-text">Events Near You</span>
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              From intimate concerts to grand conferences, find and book tickets for 
              unforgettable experiences that matter to you.
            </p>
          </div>

          {/* Search Section */}
          <div className="max-w-3xl mx-auto">
            <Card className="p-6 glass-card border-white/20">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="md:col-span-2">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      placeholder="Search events, artists, venues..."
                      className="pl-10 h-12 bg-background/50 border-white/20 focus:border-primary text-lg"
                    />
                  </div>
                </div>
                <div>
                  <div className="relative">
                    <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-muted-foreground" />
                    <Input
                      placeholder="Location"
                      className="pl-10 h-12 bg-background/50 border-white/20 focus:border-primary"
                    />
                  </div>
                </div>
                <Button variant="gradient" className="h-12 text-lg font-semibold">
                  Search
                </Button>
              </div>
            </Card>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-4 sm:space-y-0 sm:space-x-6">
            <Button variant="gradient" size="lg" className="px-8 py-4 text-lg">
              Explore Events
            </Button>
            <Button size="lg" variant="outline" className="border-white/20 hover:bg-white/10 px-8 py-4 text-lg">
              Become an Organizer
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-8 pt-16">
            <div className="text-center space-y-2">
              <div className="text-3xl md:text-4xl font-bold gradient-text">50K+</div>
              <div className="text-muted-foreground">Events Hosted</div>
            </div>
            <div className="text-center space-y-2">
              <div className="text-3xl md:text-4xl font-bold gradient-text">1M+</div>
              <div className="text-muted-foreground">Tickets Sold</div>
            </div>
            <div className="text-center space-y-2">
              <div className="text-3xl md:text-4xl font-bold gradient-text">500+</div>
              <div className="text-muted-foreground">Cities Worldwide</div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
        <div className="animate-bounce">
          <div className="w-6 h-10 border-2 border-white/30 rounded-full p-1">
            <div className="w-1 h-3 bg-white/60 rounded-full mx-auto animate-pulse"></div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;