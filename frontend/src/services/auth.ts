const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface SignUpRequest {
  email: string;
  password: string;
  confirmPassword?: string;
  firstName: string;
  lastName: string;
  phoneNumber?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user?: UserResponse;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'user';
  isActive: boolean;
  isVerified: boolean;
  createdAt: string;
  lastLogin?: string;
}

export interface UserResponse {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'admin' | 'user';
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  last_login?: string;
  phone_number?: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  bio?: string;
  location?: string;
  website?: string;
  date_of_birth?: string;
  phone_number?: string;
  created_at: string;
  updated_at: string;
}

export interface UserProfileUpdate {
  bio?: string;
  location?: string;
  website?: string;
  date_of_birth?: string;
  phone_number?: string;
}

export interface PasswordUpdate {
  current_password: string;
  new_password: string;
}

class AuthService {
  private authChangeCallbacks: (() => void)[] = [];

  private async makeRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const url = `${API_BASE_URL}${endpoint}`;
    
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (!response.ok) {
        if (response.status === 401) {
          // Token is expired or invalid, clear it and redirect to login
          this.clearAuth();
          this.notifyAuthChange();
          
          // Don't redirect if we're already on login/signup pages
          const currentPath = window.location.pathname;
          if (!currentPath.includes('/login') && !currentPath.includes('/signup') && currentPath !== '/') {
            window.location.href = '/login';
          }
          
          throw new Error('Authentication expired. Please login again.');
        }
        
        const errorData = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
      }

      return response.json();
    } catch (error) {
      if (error instanceof TypeError && error.message.includes('fetch')) {
        throw new Error('Network error. Please check your connection and try again.');
      }
      throw error;
    }
  }

  private getToken(): string | null {
    return localStorage.getItem('token');
  }

  private setToken(token: string): void {
    localStorage.setItem('token', token);
  }

  private clearAuth(): void {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  private setUser(user: User): void {
    localStorage.setItem('user', JSON.stringify(user));
  }

  private transformUserResponse(userResponse: any): User {
    console.log('Raw user response to transform:', userResponse);
    
    if (!userResponse) {
      throw new Error('No user data received');
    }

    // If it's already in the correct format, return as is
    if (userResponse.firstName && userResponse.lastName) {
      return userResponse as User;
    }

    // Handle different possible response structures
    const transformedUser: User = {
      id: userResponse.id || userResponse.user_id || '',
      email: userResponse.email || '',
      firstName: userResponse.first_name || userResponse.firstName || '',
      lastName: userResponse.last_name || userResponse.lastName || '',
      role: userResponse.role || 'user',
      isActive: userResponse.is_active !== undefined ? userResponse.is_active : userResponse.isActive !== undefined ? userResponse.isActive : true,
      isVerified: userResponse.is_verified !== undefined ? userResponse.is_verified : userResponse.isVerified !== undefined ? userResponse.isVerified : false,
      createdAt: userResponse.created_at || userResponse.createdAt || new Date().toISOString(),
      lastLogin: userResponse.last_login || userResponse.lastLogin || undefined,
    };

    console.log('Transformed user:', transformedUser);
    return transformedUser;
  }

  private notifyAuthChange(): void {
    this.authChangeCallbacks.forEach(callback => callback());
  }

  async login(credentials: LoginRequest): Promise<User> {
    try {
      // Clear any existing auth data first
      this.clearAuth();
      
      const loginData = {
        username: credentials.email,
        password: credentials.password,
      };

      console.log('Sending login request with data:', loginData);

      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(loginData as any).toString(),
      });

      console.log('Login response status:', response.status);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }));
        console.error('Login error response:', errorData);
        throw new Error(errorData.detail || errorData.message || 'Login failed');
      }

      const data = await response.json();
      console.log('Full login response:', data);
      
      let token: string;
      let userResponse: any;

      // Handle different possible response structures
      if (data.access_token) {
        token = data.access_token;
        
        // Check if user data is included in the response
        if (data.user) {
          userResponse = data.user;
        } else if (data.id || data.email) {
          // User data might be at the root level
          userResponse = data;
        } else {
          // Token only response, need to fetch user data
          console.log('No user data in login response, fetching user info...');
          this.setToken(token);
          try {
            // Fetch user data directly without checking authentication
            userResponse = await this.makeRequest<UserResponse>('/auth/me');
          } catch (err) {
            console.error('Failed to fetch user after login:', err);
            this.clearAuth();
            throw new Error('Login successful but failed to fetch user data');
          }
        }
      } else if (data.token) {
        token = data.token;
        userResponse = data.user || data;
      } else {
        console.error('No token in response:', data);
        throw new Error('Invalid login response format - no token received');
      }

      if (!userResponse) {
        throw new Error('No user data available after login');
      }
      
      // Store token and user data
      this.setToken(token);
      const user = this.transformUserResponse(userResponse);
      this.setUser(user);
      
      this.notifyAuthChange();
      return user;
    } catch (error) {
      this.clearAuth();
      throw error;
    }
  }

  async signup(userData: SignUpRequest): Promise<User> {
    try {
      // Clear any existing auth data first
      this.clearAuth();

      const { confirmPassword, ...signupData } = userData;
      
      // Transform frontend field names to backend expected format
      const backendData = {
        email: signupData.email,
        password: signupData.password,
        first_name: signupData.firstName,
        last_name: signupData.lastName,
        phone_number: signupData.phoneNumber || null,
      };

      console.log('Sending signup request with data:', backendData);

      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(backendData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }));
        console.error('Signup error response:', errorData);
        throw new Error(errorData.detail || errorData.message || 'Registration failed');
      }

      const registrationData = await response.json();
      console.log('Signup response:', registrationData);

      // After successful registration, log the user in
      const user = await this.login({
        email: userData.email,
        password: userData.password,
      });

      return user;
    } catch (error) {
      this.clearAuth();
      throw error;
    }
  }

  async getCurrentUser(): Promise<UserResponse> {
    // Only check for token, not full authentication status
    if (!this.getToken()) {
      throw new Error('Not authenticated');
    }

    try {
      return await this.makeRequest<UserResponse>('/auth/me');
    } catch (error) {
      // If getting current user fails due to auth error, clear auth state
      if (error instanceof Error && error.message.includes('Authentication expired')) {
        this.clearAuth();
        this.notifyAuthChange();
      }
      throw error;
    }
  }

  async getUserProfile(): Promise<UserProfile> {
    if (!this.isAuthenticated()) {
      throw new Error('Not authenticated');
    }

    try {
      return await this.makeRequest<UserProfile>('/auth/profile');
    } catch (error) {
      // If getting profile fails due to auth error, clear auth state
      if (error instanceof Error && error.message.includes('Authentication expired')) {
        this.clearAuth();
        this.notifyAuthChange();
      }
      throw error;
    }
  }

  async updateUserProfile(profileData: UserProfileUpdate): Promise<UserProfile> {
    return await this.makeRequest<UserProfile>('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async changePassword(passwordData: PasswordUpdate): Promise<{ message: string }> {
    return await this.makeRequest<{ message: string }>('/auth/change-password', {
      method: 'PUT',
      body: JSON.stringify(passwordData),
    });
  }

  logout(): void {
    this.clearAuth();
    this.notifyAuthChange();
    window.location.href = '/';
  }

  isAuthenticated(): boolean {
    const token = this.getToken();
    const user = this.getUser();
    return !!(token && user);
  }

  getUser(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      // If user data is corrupted, clear it
      this.clearAuth();
      return null;
    }
  }

  onAuthChange(callback: () => void): () => void {
    this.authChangeCallbacks.push(callback);
    
    // Return unsubscribe function
    return () => {
      this.authChangeCallbacks = this.authChangeCallbacks.filter(cb => cb !== callback);
    };
  }

  // Method to refresh token if needed (implement if your backend supports it)
  async refreshToken(): Promise<boolean> {
    try {
      // If your backend has a refresh endpoint, implement it here
      // For now, we'll just check if the current token is still valid
      await this.getCurrentUser();
      return true;
    } catch {
      this.clearAuth();
      this.notifyAuthChange();
      return false;
    }
  }

  // Method to validate current auth state
  async validateAuth(): Promise<boolean> {
    if (!this.isAuthenticated()) {
      return false;
    }

    try {
      await this.getCurrentUser();
      return true;
    } catch {
      this.clearAuth();
      this.notifyAuthChange();
      return false;
    }
  }
}

export const authService = new AuthService();