import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService, UserResponse, UserProfile, UserProfileUpdate, PasswordUpdate } from '@/services/auth';
import { Navbar } from '@/components';

const ProfilePage: React.FC = () => {
  const navigate = useNavigate();
  const [user, setUser] = useState<UserResponse | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordForm, setShowPasswordForm] = useState(false);
  const [saving, setSaving] = useState(false);
  
  // Form states
  const [profileForm, setProfileForm] = useState<UserProfileUpdate>({
    bio: '',
    location: '',
    website: '',
    date_of_birth: '',
    phone_number: '',
  });
  
  const [passwordForm, setPasswordForm] = useState<PasswordUpdate>({
    current_password: '',
    new_password: '',
  });

  const fetchUserData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // First check if user is authenticated
      if (!authService.isAuthenticated()) {
        navigate('/login');
        return;
      }

      // Validate authentication before making requests
      const isValid = await authService.validateAuth();
      if (!isValid) {
        navigate('/login');
        return;
      }
      
      const [userData, profileData] = await Promise.all([
        authService.getCurrentUser(),
        authService.getUserProfile(),
      ]);
      
      setUser(userData);
      setProfile(profileData);
      
      // Initialize form with current profile data
      setProfileForm({
        bio: profileData.bio || '',
        location: profileData.location || '',
        website: profileData.website || '',
        date_of_birth: profileData.date_of_birth || '',
        phone_number: profileData.phone_number || '',
      });
      
    } catch (err) {
      console.error('Error fetching user data:', err);
      
      if (err instanceof Error) {
        if (err.message.includes('Authentication expired') || err.message.includes('Not authenticated')) {
          // Redirect to login for auth errors
          navigate('/login');
          return;
        }
        setError(err.message);
      } else {
        setError('Failed to fetch user data');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUserData();
  }, []);

  // Subscribe to auth changes
  useEffect(() => {
    const unsubscribe = authService.onAuthChange(() => {
      // If user logged out, redirect to home
      if (!authService.isAuthenticated()) {
        navigate('/');
      }
    });

    return unsubscribe;
  }, [navigate]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      const updatedProfile = await authService.updateUserProfile(profileForm);
      setProfile(updatedProfile);
      setIsEditing(false);
      alert('Profile updated successfully!');
    } catch (err) {
      console.error('Error updating profile:', err);
      if (err instanceof Error && err.message.includes('Authentication expired')) {
        navigate('/login');
        return;
      }
      alert(err instanceof Error ? err.message : 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    
    try {
      await authService.changePassword(passwordForm);
      setPasswordForm({ current_password: '', new_password: '' });
      setShowPasswordForm(false);
      alert('Password changed successfully!');
    } catch (err) {
      console.error('Error changing password:', err);
      if (err instanceof Error && err.message.includes('Authentication expired')) {
        navigate('/login');
        return;
      }
      alert(err instanceof Error ? err.message : 'Failed to change password');
    } finally {
      setSaving(false);
    }
  };

  const handleProfileFormChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setProfileForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handlePasswordFormChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setPasswordForm(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="mt-2 text-muted-foreground">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive mb-4">{error}</p>
          <div className="space-x-4">
            <button 
              onClick={fetchUserData}
              className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90"
            >
              Try Again
            </button>
            <button 
              onClick={() => navigate('/login')}
              className="bg-secondary text-secondary-foreground px-4 py-2 rounded-md hover:bg-secondary/80"
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Convert user data for navbar
  const navbarUser = user ? {
    firstName: user.first_name,
    lastName: user.last_name,
    role: user.role as 'admin' | 'user'
  } : null;

  return (
    <div className="min-h-screen bg-background">
      <Navbar user={navbarUser} isAuthenticated={true} />

      <main className="max-w-4xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* Profile Header */}
        <div className="bg-card border border-border rounded-lg shadow-card p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center">
                <span className="text-2xl font-bold text-primary">
                  {user?.first_name?.charAt(0)}{user?.last_name?.charAt(0)}
                </span>
              </div>
              <div>
                <h1 className="text-2xl font-display font-bold text-foreground">
                  {user?.first_name} {user?.last_name}
                </h1>
                <p className="text-muted-foreground">{user?.email}</p>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  user?.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-blue-100 text-blue-800'
                }`}>
                  {user?.role}
                </span>
              </div>
            </div>
            <div className="flex space-x-2">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="bg-secondary text-secondary-foreground px-4 py-2 rounded-md hover:bg-secondary/80 text-sm font-medium"
              >
                {isEditing ? 'Cancel' : 'Edit Profile'}
              </button>
              <button
                onClick={() => setShowPasswordForm(!showPasswordForm)}
                className="bg-primary text-primary-foreground px-4 py-2 rounded-md hover:bg-primary/90 text-sm font-medium"
              >
                Change Password
              </button>
            </div>
          </div>
          
          {/* User Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-muted-foreground">Status:</span>
              <span className={`ml-2 ${user?.is_active ? 'text-green-600' : 'text-red-600'}`}>
                {user?.is_active ? 'Active' : 'Inactive'}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Verified:</span>
              <span className={`ml-2 ${user?.is_verified ? 'text-green-600' : 'text-yellow-600'}`}>
                {user?.is_verified ? 'Verified' : 'Not Verified'}
              </span>
            </div>
            <div>
              <span className="text-muted-foreground">Member Since:</span>
              <span className="ml-2">{new Date(user?.created_at || '').toLocaleDateString()}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Last Login:</span>
              <span className="ml-2">
                {user?.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
              </span>
            </div>
          </div>
        </div>

        {/* Profile Details */}
        <div className="bg-card border border-border rounded-lg shadow-card p-6 mb-6">
          <h2 className="text-xl font-display font-semibold text-foreground mb-4">
            Profile Details
          </h2>
          
          {isEditing ? (
            <form onSubmit={handleProfileSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Bio
                </label>
                <textarea
                  name="bio"
                  value={profileForm.bio}
                  onChange={handleProfileFormChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Tell us about yourself..."
                />
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Location
                  </label>
                  <input
                    type="text"
                    name="location"
                    value={profileForm.location}
                    onChange={handleProfileFormChange}
                    className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="City, Country"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Website
                  </label>
                  <input
                    type="url"
                    name="website"
                    value={profileForm.website}
                    onChange={handleProfileFormChange}
                    className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="https://yourwebsite.com"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Date of Birth
                  </label>
                  <input
                    type="date"
                    name="date_of_birth"
                    value={profileForm.date_of_birth}
                    onChange={handleProfileFormChange}
                    className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Phone Number
                  </label>
                  <input
                    type="tel"
                    name="phone_number"
                    value={profileForm.phone_number}
                    onChange={handleProfileFormChange}
                    className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="+1 (555) 123-4567"
                  />
                </div>
              </div>
              
              <div className="flex space-x-2 pt-4">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-primary text-primary-foreground px-6 py-2 rounded-md hover:bg-primary/90 disabled:opacity-50 font-medium"
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="bg-secondary text-secondary-foreground px-6 py-2 rounded-md hover:bg-secondary/80 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              {profile?.bio && (
                <div>
                  <h3 className="text-sm font-medium text-foreground mb-1">Bio</h3>
                  <p className="text-muted-foreground">{profile.bio}</p>
                </div>
              )}
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {profile?.location && (
                  <div>
                    <h3 className="text-sm font-medium text-foreground mb-1">Location</h3>
                    <p className="text-muted-foreground">{profile.location}</p>
                  </div>
                )}
                
                {profile?.website && (
                  <div>
                    <h3 className="text-sm font-medium text-foreground mb-1">Website</h3>
                    <a 
                      href={profile.website} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      {profile.website}
                    </a>
                  </div>
                )}
                
                {profile?.date_of_birth && (
                  <div>
                    <h3 className="text-sm font-medium text-foreground mb-1">Date of Birth</h3>
                    <p className="text-muted-foreground">
                      {new Date(profile.date_of_birth).toLocaleDateString()}
                    </p>
                  </div>
                )}
                
                {profile?.phone_number && (
                  <div>
                    <h3 className="text-sm font-medium text-foreground mb-1">Phone</h3>
                    <p className="text-muted-foreground">{profile.phone_number}</p>
                  </div>
                )}
              </div>
              
              {!profile?.bio && !profile?.location && !profile?.website && !profile?.date_of_birth && !profile?.phone_number && (
                <p className="text-muted-foreground italic">No additional profile information available. Click "Edit Profile" to add details.</p>
              )}
            </div>
          )}
        </div>

        {/* Password Change Form */}
        {showPasswordForm && (
          <div className="bg-card border border-border rounded-lg shadow-card p-6">
            <h2 className="text-xl font-display font-semibold text-foreground mb-4">
              Change Password
            </h2>
            
            <form onSubmit={handlePasswordSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  Current Password
                </label>
                <input
                  type="password"
                  name="current_password"
                  value={passwordForm.current_password}
                  onChange={handlePasswordFormChange}
                  required
                  className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-foreground mb-2">
                  New Password
                </label>
                <input
                  type="password"
                  name="new_password"
                  value={passwordForm.new_password}
                  onChange={handlePasswordFormChange}
                  required
                  minLength={8}
                  className="w-full px-3 py-2 border border-input bg-background text-foreground rounded-md focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
              
              <div className="flex space-x-2 pt-4">
                <button
                  type="submit"
                  disabled={saving}
                  className="bg-primary text-primary-foreground px-6 py-2 rounded-md hover:bg-primary/90 disabled:opacity-50 font-medium"
                >
                  {saving ? 'Changing...' : 'Change Password'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowPasswordForm(false)}
                  className="bg-secondary text-secondary-foreground px-6 py-2 rounded-md hover:bg-secondary/80 font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </main>
    </div>
  );
};

export default ProfilePage;