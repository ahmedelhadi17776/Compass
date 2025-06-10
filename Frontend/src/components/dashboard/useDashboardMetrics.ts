import { useQuery } from "@tanstack/react-query";
import { useWebSocket, QUERY_KEYS, DashboardMetrics } from "@/contexts/websocket-provider";

const API_BASE_URL = "http://localhost:8001";

const fetchDashboardMetrics = async (): Promise<DashboardMetrics> => {
  const token = localStorage.getItem("token");
  
  if (!token) {
    throw new Error("No authentication token found");
  }

  const response = await fetch(`${API_BASE_URL}/dashboard/metrics`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const useDashboardMetrics = () => {
  const { requestRefresh, isConnected } = useWebSocket();

  const query = useQuery<DashboardMetrics, Error>({
    queryKey: QUERY_KEYS.DASHBOARD_METRICS,
    queryFn: fetchDashboardMetrics,
    staleTime: 5000, 
    gcTime: 300000, 
    refetchOnWindowFocus: false, // Disable refetch on window focus since we have WebSocket
    refetchOnMount: true,
    refetchInterval: false, 
    refetchIntervalInBackground: false,
    // Reduce network delay for better perceived performance
    networkMode: "always",
    retry: (failureCount, error) => {
      // Retry up to 3 times, but not for auth errors
      if (error.message.includes("401") || error.message.includes("403")) {
        return false;
      }
      return failureCount < 2; // Reduced retry count for faster error handling
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 3000), // Faster retry with cap at 3s
    // Enable background updates when WebSocket is connected
    refetchOnReconnect: !isConnected, // Only refetch on reconnect if WebSocket isn't connected
  });

  return {
    ...query,
    requestRefresh, // Expose WebSocket refresh function
    isConnected, // Expose connection status
  };
};
