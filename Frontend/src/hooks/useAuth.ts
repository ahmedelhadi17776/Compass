import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import authApi, { LoginCredentials, User } from '@/api/auth';
import React from 'react';

// This is a custom hook that combines React Query with auth functionality
export function useAuth() {
  const queryClient = useQueryClient();
  const [token, setToken] = React.useState<string | null>(localStorage.getItem('token'));

  // Query for current user
  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: ['user'],
    queryFn: () => authApi.getMe(token!),
    enabled: !!token,
  });

  // Login mutation
  const login = useMutation({
    mutationFn: (credentials: LoginCredentials) => authApi.login(credentials),
    onSuccess: async (data) => {
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
      await queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });

  // Logout mutation
  const logout = useMutation({
    mutationFn: () => authApi.logout(token!),
    onSuccess: () => {
      localStorage.removeItem('token');
      setToken(null);
      queryClient.clear();
    },
  });

  const updateUser = useMutation({
    mutationFn: (userData: {
      first_name: string
      last_name: string
      email: string
    }) => authApi.updateUser(token!, userData),
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