import React from 'react';
import { authService } from '@/services/auth';
import { useNavigate, Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-50 via-background to-yellow-100/50">
      <nav className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-2xl font-display font-bold text-primary">
                Eventix
              </Link>
              <div className="ml-10 flex items-baseline space-x-8">
                <a href="#" className="text-foreground hover:text-primary px-3 py-2 rounded-md text-sm font-medium">
                  Dashboard
                </a>
                <a href="#" className="text-muted-foreground hover:text-foreground px-3 py-2 rounded-md text-sm font-medium">
                  Events
                </a>
                <a href="#" className="text-muted-foreground hover:text-foreground px-3 py-2 rounded-md text-sm font-medium">
                  Analytics
                </a>
              </div>
            </div>
            <div className="flex items-center">
              <button
                onClick={handleLogout}
                className="bg-destructive hover:bg-destructive/90 text-destructive-foreground px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <div className="mb-8">
            <h1 className="text-3xl font-display font-bold text-foreground">
              Welcome to your Dashboard!
            </h1>
            <p className="mt-2 text-muted-foreground">
              Manage your events and track your success from here.
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-card p-6 rounded-lg border border-border shadow-card">
              <div className="flex items-center">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-muted-foreground">Total Events</p>
                  <p className="text-2xl font-semibold text-foreground">12</p>
                </div>
              </div>
            </div>

            <div className="bg-card p-6 rounded-lg border border-border shadow-card">
              <div className="flex items-center">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-muted-foreground">Total Attendees</p>
                  <p className="text-2xl font-semibold text-foreground">1,234</p>
                </div>
              </div>
            </div>

            <div className="bg-card p-6 rounded-lg border border-border shadow-card">
              <div className="flex items-center">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-muted-foreground">Success Rate</p>
                  <p className="text-2xl font-semibold text-foreground">94%</p>
                </div>
              </div>
            </div>

            <div className="bg-card p-6 rounded-lg border border-border shadow-card">
              <div className="flex items-center">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                  </svg>
                </div>
                <div className="ml-4">
                  <p className="text-sm text-muted-foreground">Revenue</p>
                  <p className="text-2xl font-semibold text-foreground">$45,678</p>
                </div>
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="bg-card rounded-lg border border-border shadow-card p-8">
            <div className="text-center">
              <h2 className="text-2xl font-display font-bold text-foreground mb-4">
                Start Creating Amazing Events
              </h2>
              <p className="text-muted-foreground mb-8">
                Your event management dashboard is ready. Start by creating your first event or explore the features.
              </p>
              <div className="flex justify-center space-x-4">
                <button className="px-6 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors">
                  Create New Event
                </button>
                <button className="px-6 py-3 bg-secondary text-secondary-foreground rounded-lg font-medium hover:bg-secondary/90 transition-colors border border-border">
                  View All Events
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;