import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Shield, 
  Clock, 
  CreditCard, 
  Users, 
  Star, 
  Headphones,
  Globe,
  Smartphone
} from 'lucide-react';

const WhyChooseUs = () => {
  const features = [
    {
      icon: Shield,
      title: "Secure & Trusted",
      description: "Bank-level security with encrypted transactions and verified event organizers.",
      stats: "99.9% Security Score"
    },
    {
      icon: Clock,
      title: "Instant Booking",
      description: "Get your tickets immediately with our lightning-fast booking system.",
      stats: "< 30 Second Booking"
    },
    {
      icon: CreditCard,
      title: "Flexible Payments",
      description: "Multiple payment options including buy-now-pay-later and installments.",
      stats: "20+ Payment Methods"
    },
    {
      icon: Users,
      title: "Trusted Community",
      description: "Join millions of event-goers and verified reviews from real attendees.",
      stats: "2M+ Happy Customers"
    },
    {
      icon: Star,
      title: "Best Price Guarantee",
      description: "We ensure you get the best prices with our price-match guarantee.",
      stats: "100% Price Match"
    },
    {
      icon: Headphones,
      title: "24/7 Support",
      description: "Round-the-clock customer support to help you with any questions.",
      stats: "24/7 Live Chat"
    },
    {
      icon: Globe,
      title: "Global Reach",
      description: "Access events worldwide with local currency and language support.",
      stats: "500+ Cities"
    },
    {
      icon: Smartphone,
      title: "Mobile First",
      description: "Seamless experience across all devices with our mobile-optimized platform.",
      stats: "4.9★ App Rating"
    }
  ];

  return (
    <section className="py-20 relative overflow-hidden">
      {/* Background Pattern */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute top-0 left-0 w-72 h-72 bg-primary/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-0 w-96 h-96 bg-accent/20 rounded-full blur-3xl"></div>
      </div>

      <div className="container mx-auto px-4 relative">
        {/* Section Header */}
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-primary/20 text-primary border-primary/30">
            Why Choose EVENTIX
          </Badge>
          <h2 className="text-4xl md:text-5xl font-display font-bold">
            The Most Trusted
            <span className="block gradient-text">Event Platform</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            We've revolutionized event booking with cutting-edge technology, 
            unmatched security, and exceptional customer service.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature, index) => {
            const IconComponent = feature.icon;
            return (
              <Card 
                key={feature.title} 
                className="group glass-card border-white/10 hover-glow"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <CardContent className="p-6 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="w-12 h-12 rounded-xl bg-gradient-primary flex items-center justify-center group-hover:scale-110 transition-transform duration-300">
                      <IconComponent className="h-6 w-6 text-white" />
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {feature.stats}
                    </Badge>
                  </div>
                  
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Trust Indicators */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          <div className="text-center space-y-2">
            <div className="text-3xl font-bold gradient-text">2M+</div>
            <div className="text-sm text-muted-foreground">Active Users</div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-3xl font-bold gradient-text">50K+</div>
            <div className="text-sm text-muted-foreground">Events Hosted</div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-3xl font-bold gradient-text">4.9★</div>
            <div className="text-sm text-muted-foreground">Customer Rating</div>
          </div>
          <div className="text-center space-y-2">
            <div className="text-3xl font-bold gradient-text">99.9%</div>
            <div className="text-sm text-muted-foreground">Uptime</div>
          </div>
        </div>

        {/* Testimonial Section */}
        <div className="glass-card p-8 rounded-2xl text-center">
          <div className="flex justify-center mb-4">
            {[...Array(5)].map((_, i) => (
              <Star key={i} className="h-5 w-5 text-yellow-400 fill-current" />
            ))}
          </div>
          <blockquote className="text-xl text-foreground mb-4 max-w-3xl mx-auto">
            "EVENTIX has completely transformed how we discover and attend events. 
            The platform is incredibly user-friendly, secure, and the customer service is outstanding."
          </blockquote>
          <div className="flex items-center justify-center space-x-4">
            <div className="w-12 h-12 rounded-full bg-gradient-primary flex items-center justify-center">
              <span className="text-white font-semibold">JD</span>
            </div>
            <div className="text-left">
              <div className="font-semibold text-foreground">Jessica Davis</div>
              <div className="text-sm text-muted-foreground">Event Enthusiast</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default WhyChooseUs;