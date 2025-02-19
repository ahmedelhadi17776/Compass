import axios from 'axios';
import { API_URL } from '@/config';

// Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  avatar_url?: string;
}

// API client
const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await axios.post(`${API_URL}/auth/login`, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    // Set the token in axios defaults for future requests
    if (response.data.access_token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
    }

    return response.data;
  },

  getMe: async (token: string): Promise<User> => {
    const response = await axios.get(`${API_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },

  logout: async (token: string): Promise<void> => {
    await axios.post(`${API_URL}/auth/logout`, null, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};

export default authApi; 