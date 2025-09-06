import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { authService } from '@/services/auth';

interface NavbarProps {
  user?: {
    firstName?: string;
    lastName?: string;
    role?: 'admin' | 'user';
  } | null;
  isAuthenticated?: boolean;
}

const Navbar: React.FC<NavbarProps> = ({ user, isAuthenticated = false }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/');
  };

  const isActivePage = (path: string) => {
    return location.pathname === path;
  };

  const getDashboardLink = () => {
    return user?.role === 'admin' ? '/dashboard' : '/events';
  };

  const getDashboardText = () => {
    return user?.role === 'admin' ? 'Dashboard' : 'Events';
  };

  return (
    <nav className="bg-card shadow-sm border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="text-2xl font-display font-bold text-primary">
              Eventix
            </Link>
            
            {isAuthenticated && (
              <div className="ml-10 flex items-baseline space-x-8">
                {/* Events Link */}
                <Link
                  to="/events"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActivePage('/events')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Events
                </Link>

                {/* Dashboard Link (for admin) */}
                {user?.role === 'admin' && (
                  <Link
                    to="/dashboard"
                    className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActivePage('/dashboard')
                        ? 'text-primary'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    Dashboard
                  </Link>
                )}

                {/* My Bookings Link */}
                <Link
                  to="/my-bookings"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActivePage('/my-bookings')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  My Bookings
                </Link>

                {/* Profile Link */}
                <Link
                  to="/profile"
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActivePage('/profile')
                      ? 'text-primary'
                      : 'text-muted-foreground hover:text-foreground'
                  }`}
                >
                  Profile
                </Link>
              </div>
            )}
          </div>

          <div className="flex items-center">
            {isAuthenticated && user ? (
              <div className="flex items-center space-x-4">
                <span className="text-sm text-muted-foreground">
                  Welcome, {user.firstName || 'User'}
                </span>
                {user.role && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                  }`}>
                    {user.role}
                  </span>
                )}
                <button
                  onClick={handleLogout}
                  className="bg-destructive hover:bg-destructive/90 text-destructive-foreground px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-4">
                <Link
                  to="/login"
                  className="text-foreground hover:text-primary transition-colors"
                >
                  Sign in
                </Link>
                <Link
                  to="/signup"
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;