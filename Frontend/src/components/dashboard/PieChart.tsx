"use client"

import { PolarAngleAxis, RadialBar, RadialBarChart, Tooltip as RechartsTooltip } from "recharts"
import { Card, CardContent } from "@/components//ui/card"
import { ChartContainer } from "@/components//ui/chart"
import { useWebSocket } from "@/contexts/websocket-provider"
import { useState, useEffect, useMemo } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { QUERY_KEYS, DashboardMetrics } from "@/contexts/websocket-provider"

interface MetricData {
  activity: string
  value: number
  fill: string
  completed: string
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-zinc-800 px-3 py-2 rounded-lg border border-zinc-700">
        <p className="text-xs font-medium text-zinc-200 capitalize">{data.activity}</p>
        <p className="text-xs text-zinc-400">{data.completed} completed</p>
      </div>
    );
  }
  return null;
};

export default function PieChart() {
  // Get WebSocket context
  const { requestRefresh } = useWebSocket();
  const queryClient = useQueryClient();
  
  // State to store metrics data
  const [metricsData, setMetricsData] = useState<DashboardMetrics | undefined>(undefined);
  const [isLoading, setIsLoading] = useState(true);

  // Get metrics data directly from React Query cache
  useEffect(() => {
    // Initial data fetch
    const cachedData = queryClient.getQueryData<DashboardMetrics>(QUERY_KEYS.DASHBOARD_METRICS);
    if (cachedData) {
      setMetricsData(cachedData);
      setIsLoading(false);
    } else {
      // Request data if not available
      requestRefresh();
    }

    // Subscribe to cache changes
    const unsubscribe = queryClient.getQueryCache().subscribe(() => {
      const updatedData = queryClient.getQueryData<DashboardMetrics>(QUERY_KEYS.DASHBOARD_METRICS);
      if (updatedData) {
        console.log("PieChart received updated metrics:", updatedData);
        setMetricsData(updatedData);
        setIsLoading(false);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [queryClient, requestRefresh]);

  // Process the metrics data for the chart
  const chartData = useMemo<MetricData[]>(() => {
    if (!metricsData) {
      return [];
    }

    const todos = metricsData.todos || { total: 0, completed: 0 };
    const habits = metricsData.habits || { total: 0, completed: 0 };
    const tasks = metricsData.tasks || { total: 0, completed: 0 };

    return [
      {
        activity: "todos",
        value: todos.total > 0 
          ? (todos.completed / todos.total) * 100 
          : 0,
        fill: "#3b82f6",
        completed: `${todos.completed || 0}/${todos.total || 0}`
      },
      {
        activity: "habits",
        value: habits.total > 0 
          ? (habits.completed / habits.total) * 100 
          : 0,
        fill: "#1d4ed8",
        completed: `${habits.completed || 0}/${habits.total || 0}`
      },
      {
        activity: "tasks",
        value: tasks.total > 0 
          ? (tasks.completed / tasks.total) * 100 
          : 0,
        fill: "#1e40af",
        completed: `${tasks.completed || 0}/${tasks.total || 0}`
      },
    ];
  }, [metricsData]);

  // Handle loading state
  if (isLoading) {
    return (
      <Card className="flex flex-col rounded-3xl">
        <CardContent className="p-6 flex justify-center items-center h-[280px]">
          <p className="text-sm text-muted-foreground">Loading metrics...</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="flex flex-col rounded-3xl">
      <CardContent className="p-0">
        <div className="flex flex-col">
          <div className="flex flex-col items-center space-y-1.5 p-6 pb-2">
            <span className="text-xl font-semibold leading-none tracking-tight">Completion Status</span>
            <span className="text-sm text-muted-foreground">Progress overview</span>
          </div>
          <div className="flex items-center justify-between px-6 pb-6">
            <div className="flex flex-col space-y-4">
              <div className="flex flex-col">
                <div className="text-sm text-zinc-400 mb-1">Tasks</div>
                <div className="flex items-baseline gap-1.5 text-xl font-bold tabular-nums leading-none">
                  {chartData[2]?.completed || "0/0"}
                  <span className="text-sm font-normal text-zinc-500">
                    completed
                  </span>
                </div>
              </div>
              <div className="flex flex-col">
                <div className="text-sm text-zinc-400 mb-1">Habits</div>
                <div className="flex items-baseline gap-1.5 text-xl font-bold tabular-nums leading-none">
                  {chartData[1]?.completed || "0/0"}
                  <span className="text-sm font-normal text-zinc-500">
                    completed
                  </span>
                </div>
              </div>
              <div className="flex flex-col">
                <div className="text-sm text-zinc-400 mb-1">Todos</div>
                <div className="flex items-baseline gap-1.5 text-xl font-bold tabular-nums leading-none">
                  {chartData[0]?.completed || "0/0"}
                  <span className="text-sm font-normal text-zinc-500">
                    completed
                  </span>
                </div>
              </div>
            </div>
            <ChartContainer
              config={{
                tasks: {
                  label: "Tasks",
                  color: "#1e40af",
                },
                habits: {
                  label: "Habits",
                  color: "#1d4ed8",
                },
                todos: {
                  label: "Todos",
                  color: "#3b82f6",
                },
              }}
              className="aspect-square w-[180px] h-[180px] -mr-4"
            >
              <RadialBarChart
                margin={{
                  left: -12,
                  right: -12,
                  top: -12,
                  bottom: -12,
                }}
                data={chartData}
                innerRadius="40%"
                barSize={20}
                startAngle={90}
                endAngle={450}
              >
                <PolarAngleAxis
                  type="number"
                  domain={[0, 100]}
                  dataKey="value"
                  tick={false}
                />
                <RadialBar 
                  dataKey="value" 
                  background 
                  cornerRadius={6}
                  animationDuration={1500}
                />
                <RechartsTooltip content={<CustomTooltip />} cursor={false} />
              </RadialBarChart>
            </ChartContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}