import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

export const DASHBOARD_METRICS_QUERY_KEY = ['dashboard_metrics'];

export const useDashboardMetrics = () =>
  useQuery({
    queryKey: DASHBOARD_METRICS_QUERY_KEY,
    queryFn: async () => {
      const token = localStorage.getItem('token');
      
      if (!token) {
        throw new Error('No auth token found in localStorage');
      }
      
      try {
        console.log('Fetching dashboard metrics...');
        const res = await axios.get('http://localhost:8001/dashboard/metrics', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        console.log('Dashboard metrics received:', res.data);
        return res.data;
      } catch (error) {
        console.error('Failed to fetch dashboard metrics:', error);
        throw error;
      }
    },
    staleTime: 0, // Mark data as immediately stale
    refetchOnMount: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
  });