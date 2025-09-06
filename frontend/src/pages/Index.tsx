import Header from '@/components/layout/Header';
import Footer from '@/components/layout/Footer';
import HeroSection from '@/components/sections/HeroSection';
import FeaturedEvents from '@/components/sections/FeaturedEvents';
import Categories from '@/components/sections/Categories';
import WhyChooseUs from '@/components/sections/WhyChooseUs';

const Index = () => {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <HeroSection />
        <FeaturedEvents />
        <Categories />
        <WhyChooseUs />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
