import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import React from 'react';
import authApi, { User, LoginCredentials, AuthResponse, MFASetupResponse, MFAStatusResponse } from '@/api/auth';

// Re-export types for convenience
export type { User, LoginCredentials, AuthResponse, MFASetupResponse, MFAStatusResponse };

// This is a custom hook that combines React Query with auth functionality
export function useAuth() {
  const queryClient = useQueryClient();
  const [token, setToken] = React.useState<string | null>(localStorage.getItem('token'));

  // Query for current user
  const { data: user, isLoading: isLoadingUser } = useQuery({
    queryKey: ['user'],
    queryFn: authApi.getMe,
    enabled: !!token,
    retry: 1,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    gcTime: 1000 * 60 * 60, // Keep in garbage collection for 1 hour
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
      if ('token' in data) {
        localStorage.setItem('token', data.token);
        setToken(data.token);
        await queryClient.invalidateQueries({ queryKey: ['user'] });
      }
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
    mutationFn: authApi.updateUser,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });

  // MFA Queries and Mutations
  const mfaStatus = useQuery({
    queryKey: ['mfa-status'],
    queryFn: authApi.getMFAStatus,
    enabled: !!token,
  });

  const setupMFA = useMutation({
    mutationFn: authApi.setupMFA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mfa-status'] });
    },
  });

  const verifyMFA = useMutation({
    mutationFn: authApi.verifyMFA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mfa-status'] });
    },
  });

  const disableMFA = useMutation({
    mutationFn: authApi.disableMFA,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mfa-status'] });
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
    mfaStatus,
    setupMFA,
    verifyMFA,
    disableMFA,
  };
} 