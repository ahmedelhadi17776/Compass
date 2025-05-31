import axios from 'axios';
import { GO_API_URL } from '@/config';

// Types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  user: {
    id: string;
    email: string;
    username: string;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
    updated_at: string;
    mfa_enabled: boolean;
    failed_login_attempts: number;
    force_password_change: boolean;
    max_sessions: number;
  };
  expires_at: string;
}

export interface User {
  id: string;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  avatar_url: string;
  bio: string;
  timezone: string;
  locale: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  mfa_enabled: boolean;
  failed_login_attempts: number;
  force_password_change: boolean;
  max_sessions: number;
}

// API client
const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await axios.post(`${GO_API_URL}/users/login`, {
      email: credentials.email,
      password: credentials.password
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const data = response.data;
    
    const token = data.token || data.access_token;
    
    if (token) {
      // Set axios default headers
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Store token in localStorage with consistent name
      localStorage.setItem('token', token);
      console.log('Token saved:', token.substring(0, 15) + '...');
    } else {
      console.error('No token received in auth response');
    }

    return data;
  },

  getMe: async (): Promise<User> => {
    const response = await axios.get(`${GO_API_URL}/users/profile`);
    return response.data.data;
  },

  logout: async (): Promise<void> => {
    await axios.post(`${GO_API_URL}/users/logout`, null);
    delete axios.defaults.headers.common['Authorization'];
  },

  updateUser: async (userData: {
    first_name?: string;
    last_name?: string;
    email?: string;
  }): Promise<User> => {
    const response = await axios.patch(`${GO_API_URL}/users/profile`, userData);
    return response.data.data;
  },
};

export default authApi; 