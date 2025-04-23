import axios from 'axios';
import { API_URL } from '@/config';

// Types
export interface LoginCredentials {
  email: string;
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
    const response = await axios.post(`${API_URL}/api/users/login`, {
      email: credentials.email,
      password: credentials.password
    }, {
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (response.data.data.Token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.data.Token}`;
    }

    return response.data.data;
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

  updateUser: async (token: string, userData: {
    first_name: string;
    last_name: string;
    email: string;
  }): Promise<User> => {
    const response = await axios.patch(`${API_URL}/auth/me`, userData, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return response.data;
  },
};

export default authApi; 