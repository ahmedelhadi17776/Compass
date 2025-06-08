"use client"

import { PolarAngleAxis, RadialBar, RadialBarChart, Tooltip as RechartsTooltip } from "recharts"
import { Card, CardContent } from "@/components//ui/card"
import { ChartContainer } from "@/components//ui/chart"
import { useDashboardMetrics } from "./useDashboardMetrics"
import { useWebSocket } from "@/contexts/websocket-provider"
import { useMemo } from "react"

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
  // Get WebSocket context if needed
  const { requestRefresh } = useWebSocket();
  
  // Fetch metrics data using our custom hook
  const { data: metricsData, isLoading, error } = useDashboardMetrics();

  // Process the metrics data for the chart
  const chartData = useMemo<MetricData[]>(() => {
    if (!metricsData) return [];

    return [
      {
        activity: "todos",
        value: metricsData.todos.total > 0 
          ? (metricsData.todos.completed / metricsData.todos.total) * 100 
          : 0,
        fill: "#3b82f6",
        completed: `${metricsData.todos.completed}/${metricsData.todos.total}`
      },
      {
        activity: "habits",
        value: metricsData.habits.total > 0 
          ? (metricsData.habits.completed / metricsData.habits.total) * 100 
          : 0,
        fill: "#1d4ed8",
        completed: `${metricsData.habits.completed}/${metricsData.habits.total}`
      },
      {
        activity: "tasks",
        value: metricsData.tasks.total > 0 
          ? (metricsData.tasks.completed / metricsData.tasks.total) * 100 
          : 0,
        fill: "#1e40af",
        completed: `${metricsData.tasks.completed}/${metricsData.tasks.total}`
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

  // Handle error state
  if (error) {
    return (
      <Card className="flex flex-col rounded-3xl">
        <CardContent className="p-6 flex justify-center items-center h-[280px]">
          <p className="text-sm text-muted-foreground">Failed to load metrics</p>
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