import { useQuery, useMutation, useQueryClient, Query } from '@tanstack/react-query';
import authApi, { LoginCredentials, User } from '@/api/auth';
import React from 'react';
import axios, { AxiosError } from 'axios';

// This is a custom hook that combines React Query with auth functionality
export function useAuth() {
  const queryClient = useQueryClient();
  const [token, setToken] = React.useState<string | null>(localStorage.getItem('token'));

  // Query for current user
  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: ['user'],
    queryFn: () => authApi.getMe(token!),
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