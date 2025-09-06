import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Music, 
  Briefcase, 
  Trophy, 
  Palette, 
  GraduationCap,
  Heart,
  Utensils,
  Gamepad2
} from 'lucide-react';

const Categories = () => {
  const categories = [
    {
      icon: Music,
      name: "Music & Concerts",
      count: "2,850 events",
      color: "text-purple-400",
      bgColor: "bg-purple-400/20",
      description: "Live concerts, festivals, and musical performances"
    },
    {
      icon: Briefcase,
      name: "Business & Professional",
      count: "1,240 events",
      color: "text-blue-400",
      bgColor: "bg-blue-400/20",
      description: "Conferences, workshops, and networking events"
    },
    {
      icon: Trophy,
      name: "Sports & Fitness",
      count: "892 events",
      color: "text-green-400",
      bgColor: "bg-green-400/20",
      description: "Sporting events, tournaments, and fitness activities"
    },
    {
      icon: Palette,
      name: "Arts & Culture",
      count: "1,156 events",
      color: "text-pink-400",
      bgColor: "bg-pink-400/20",
      description: "Art exhibitions, theater, and cultural events"
    },
    {
      icon: GraduationCap,
      name: "Education & Learning",
      count: "634 events",
      color: "text-indigo-400",
      bgColor: "bg-indigo-400/20",
      description: "Workshops, seminars, and educational programs"
    },
    {
      icon: Heart,
      name: "Health & Wellness",
      count: "428 events",
      color: "text-red-400",
      bgColor: "bg-red-400/20",
      description: "Wellness retreats, health seminars, and mindfulness"
    },
    {
      icon: Utensils,
      name: "Food & Drink",
      count: "756 events",
      color: "text-orange-400",
      bgColor: "bg-orange-400/20",
      description: "Food festivals, wine tastings, and culinary experiences"
    },
    {
      icon: Gamepad2,
      name: "Gaming & Tech",
      count: "312 events",
      color: "text-cyan-400",
      bgColor: "bg-cyan-400/20",
      description: "Gaming tournaments, tech meetups, and digital events"
    }
  ];

  return (
    <section className="py-20 relative">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center space-y-4 mb-16">
          <Badge className="bg-accent/20 text-accent border-accent/30">
            Event Categories
          </Badge>
          <h2 className="text-4xl md:text-5xl font-display font-bold">
            Find Events by
            <span className="block gradient-text">Your Interest</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Browse thousands of events across different categories and find your perfect match
          </p>
        </div>

        {/* Categories Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {categories.map((category, index) => {
            const IconComponent = category.icon;
            return (
              <Card 
                key={category.name} 
                className="group glass-card border-white/10 hover-glow cursor-pointer transition-all duration-300"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <CardContent className="p-6 text-center space-y-4">
                  <div className={`mx-auto w-16 h-16 rounded-2xl ${category.bgColor} flex items-center justify-center group-hover:scale-110 transition-transform duration-300`}>
                    <IconComponent className={`h-8 w-8 ${category.color}`} />
                  </div>
                  
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                      {category.name}
                    </h3>
                    <p className="text-sm text-muted-foreground">
                      {category.description}
                    </p>
                    <Badge variant="secondary" className="mt-2">
                      {category.count}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="glass-card p-8 rounded-2xl max-w-2xl mx-auto">
            <h3 className="text-2xl font-bold text-foreground mb-4">
              Can't find your category?
            </h3>
            <p className="text-muted-foreground mb-6">
              We're constantly adding new event categories. Request a custom category 
              or browse all events to discover something new.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button variant="gradient" className="px-6 py-3">
                Browse All Events
              </Button>
              <Button variant="outline" className="px-6 py-3">
                Request Category
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Categories;