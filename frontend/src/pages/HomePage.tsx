import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { authService } from '@/services/auth';
import { Navbar } from '@/components';

const HomePage: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());
  const [user, setUser] = useState(authService.getUser());

  useEffect(() => {
    // Subscribe to auth changes
    const unsubscribe = authService.onAuthChange(() => {
      setIsAuthenticated(authService.isAuthenticated());
      setUser(authService.getUser());
    });

    // Cleanup subscription on unmount
    return unsubscribe;
  }, []);

  // Safe role checking with fallback
  const isAdmin = user?.role === 'admin';
  const isValidUser = user && user.role;

  const getDashboardLink = () => {
    return isAdmin ? '/dashboard' : '/events';
  };

  const getDashboardText = () => {
    return isAdmin ? 'Go to Dashboard' : 'Browse Events';
  };

  // Transform user data for navbar to ensure consistent format
  const navbarUser = user ? {
    firstName: user.firstName,
    lastName: user.lastName,
    role: user.role
  } : null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-background to-yellow-100/50">
      {/* Header */}
      <div className="relative z-10 bg-background/90 backdrop-blur-sm border-b border-border">
        <Navbar user={navbarUser} isAuthenticated={isAuthenticated} />
      </div>

      {/* Hero Section */}
      <main className="relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <div className="mb-8">
              <h2 className="text-5xl md:text-6xl font-display font-bold text-foreground mb-6">
                Create Amazing
                <span className="block bg-gradient-to-r from-primary via-yellow-500 to-secondary bg-clip-text text-transparent">
                  Events
                </span>
              </h2>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
                The ultimate platform for event planning, management, and execution. 
                From small gatherings to large conferences, make every event extraordinary.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mb-16">
              {!isAuthenticated || !isValidUser ? (
                <>
                  <Link
                    to="/signup"
                    className="px-8 py-4 bg-gradient-to-r from-primary to-yellow-600 text-white rounded-lg font-semibold hover:from-primary/90 hover:to-yellow-600/90 transition-all duration-300 transform hover:scale-105 shadow-lg"
                  >
                    Start Booking Tickets
                  </Link>
                  <Link
                    to="/login"
                    className="px-8 py-4 bg-secondary text-secondary-foreground rounded-lg font-semibold hover:bg-secondary/90 transition-all duration-300 border border-border"
                  >
                    Sign In
                  </Link>
                </>
              ) : (
                <Link
                  to={getDashboardLink()}
                  className="px-8 py-4 bg-gradient-to-r from-primary to-yellow-600 text-white rounded-lg font-semibold hover:from-primary/90 hover:to-yellow-600/90 transition-all duration-300 transform hover:scale-105 shadow-lg"
                >
                  {getDashboardText()}
                </Link>
              )}
            </div>

            {/* Features Grid */}
            <div className="grid md:grid-cols-3 gap-8 mt-20">
              <div className="bg-card/80 backdrop-blur-sm border border-border rounded-lg p-8 shadow-card hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-100 to-primary/10 rounded-lg flex items-center justify-center mb-6 mx-auto">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-display font-semibold text-foreground mb-4">
                  Easy Planning
                </h3>
                <p className="text-muted-foreground">
                  Intuitive tools to plan your events from start to finish. Set dates, manage venues, and coordinate with your team.
                </p>
              </div>

              <div className="bg-card/80 backdrop-blur-sm border border-border rounded-lg p-8 shadow-card hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-100 to-primary/10 rounded-lg flex items-center justify-center mb-6 mx-auto">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
                <h3 className="text-xl font-display font-semibold text-foreground mb-4">
                  Guest Management
                </h3>
                <p className="text-muted-foreground">
                  Manage attendees, send invitations, and track RSVPs all in one place. Make guest management effortless.
                </p>
              </div>

              <div className="bg-card/80 backdrop-blur-sm border border-border rounded-lg p-8 shadow-card hover:shadow-lg transition-shadow">
                <div className="w-12 h-12 bg-gradient-to-br from-yellow-100 to-primary/10 rounded-lg flex items-center justify-center mb-6 mx-auto">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-xl font-display font-semibold text-foreground mb-4">
                  Real-time Analytics
                </h3>
                <p className="text-muted-foreground">
                  Track your event performance with detailed analytics and insights. Make data-driven decisions.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Background decorations with yellow gradients */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 rounded-full bg-gradient-to-br from-yellow-200/30 to-primary/10 blur-3xl"></div>
          <div className="absolute -bottom-40 -left-40 w-80 h-80 rounded-full bg-gradient-to-tr from-yellow-100/40 to-secondary/10 blur-3xl"></div>
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 rounded-full bg-gradient-to-r from-yellow-50/20 to-yellow-100/20 blur-3xl"></div>
        </div>
      </main>
    </div>
  );
};

export default HomePage;