import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios, { AxiosError } from 'axios';
import React from 'react';

export interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  timezone: string;
  locale: string;
  mfa_enabled: boolean;
  failed_login_attempts: number;
  force_password_change: boolean;
  max_sessions: number;
  avatar?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  token: string;
}

const API_URL = 'https://localhost:8000/api';

const authApi = {
  login: async (credentials: LoginCredentials): Promise<AuthResponse> => {
    const response = await axios.post(`${API_URL}/auth/login`, credentials);
    return response.data;
  },
  logout: async () => {
    await axios.post(`${API_URL}/users/logout`);
  },
  getMe: async (): Promise<User> => {
    const response = await axios.get(`${API_URL}/users/profile`);
    return response.data.user;
  },
  updateUser: async (userData: Partial<User>): Promise<User> => {
    const response = await axios.put(`${API_URL}/users/profile`, userData);
    return response.data.user;
  },
};

// This is a custom hook that combines React Query with auth functionality
export function useAuth() {
  const queryClient = useQueryClient();
  const [token, setToken] = React.useState<string | null>(localStorage.getItem('token'));

  // Query for current user
  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getMe,
    enabled: !!token,
    retry: false,
    staleTime: 0,
    gcTime: 0,
  });

  // Handle unauthorized errors
  React.useEffect(() => {
    const subscription = queryClient.getQueryCache().subscribe((event) => {
      const error = event?.query?.state?.error as AxiosError;
      if (error?.response?.status === 401) {
        localStorage.removeItem('token');
        setToken(null);
        queryClient.clear();
      }
    });

    return () => {
      subscription();
    };
  }, [queryClient]);

  // Login mutation
  const login = useMutation({
    mutationFn: (credentials: LoginCredentials) => authApi.login(credentials),
    onSuccess: async (data) => {
      localStorage.setItem('token', data.token);
      setToken(data.token);
      await queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });

  // Logout mutation
  const logout = useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      localStorage.removeItem('token');
      setToken(null);
      queryClient.clear();
    },
  });

  const updateUser = useMutation({
    mutationFn: (userData: Partial<User>) => authApi.updateUser(userData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });

  return {
    user,
    login,
    logout,
    updateUser,
    isAuthenticated: !!token,
    isLoadingUser,
    queryClient,
  };
} 