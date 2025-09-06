import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from '@/pages/HomePage';
import LoginPage from '@/pages/LoginPage';
import SignUpPage from '@/pages/SignUpPage';
import Dashboard from '@/pages/Dashboard';
import EventsPage from '@/pages/EventsPage';
import ProfilePage from '@/pages/ProfilePage';
import BookingPage from '@/pages/BookingPage';
import ProtectedRoute from '@/components/ProtectedRoute';
import PaymentPage from '@/pages/PaymentPage';
import PaymentSuccessPage from '@/pages/PaymentSuccessPage';
import { authService } from '@/services/auth';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());
  const [user, setUser] = useState(authService.getUser());
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Initialize auth state
    setIsAuthenticated(authService.isAuthenticated());
    setUser(authService.getUser());
    setIsLoading(false);

    // Subscribe to auth changes
    const unsubscribe = authService.onAuthChange(() => {
      setIsAuthenticated(authService.isAuthenticated());
      setUser(authService.getUser());
    });

    return unsubscribe;
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <Router future={{ v7_relativeSplatPath: true }}>
      <div className="App">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<HomePage />} />
          
          <Route 
            path="/login" 
            element={
              isAuthenticated ? 
                <Navigate to={user?.role === 'admin' ? '/dashboard' : '/events'} replace /> : 
                <LoginPage />
            } 
          />
          <Route 
            path="/signup" 
            element={
              isAuthenticated ? 
                <Navigate to={user?.role === 'admin' ? '/dashboard' : '/events'} replace /> : 
                <SignUpPage />
            } 
          />
          
          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                {isAuthenticated && user?.role === 'admin' ? (
                  <Dashboard />
                ) : (
                  <Navigate to="/events" replace />
                )}
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/events"
            element={
              <ProtectedRoute>
                <EventsPage />
              </ProtectedRoute>
            }
          />
          
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <ProfilePage />
              </ProtectedRoute>
            }
          />

          <Route 
            path="/booking/:eventId" 
            element={
              <ProtectedRoute>
                <BookingPage />
              </ProtectedRoute>
            } 
          />

          <Route path="/payment/:bookingId" element={<PaymentPage />} />
          <Route path="/payment/success" element={<PaymentSuccessPage />} />
          
          {/* Catch all route */}
          <Route 
            path="*" 
            element={<Navigate to="/" replace />} 
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;