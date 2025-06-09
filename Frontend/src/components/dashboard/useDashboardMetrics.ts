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
  const { requestRefresh } = useWebSocket();

  const query = useQuery<DashboardMetrics, Error>({
    queryKey: QUERY_KEYS.DASHBOARD_METRICS,
    queryFn: fetchDashboardMetrics,
    staleTime: 30000, // Consider data fresh for 30 seconds
    gcTime: 300000, // Keep in cache for 5 minutes
    refetchOnWindowFocus: false, // Disable refetch on window focus since we have WebSocket
    refetchOnMount: true,
    retry: (failureCount, error) => {
      // Retry up to 3 times, but not for auth errors
      if (error.message.includes("401") || error.message.includes("403")) {
        return false;
      }
      return failureCount < 3;
    },
  });

  return {
    ...query,
    requestRefresh, // Expose WebSocket refresh function
  };
};
