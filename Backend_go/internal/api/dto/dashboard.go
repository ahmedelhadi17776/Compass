package dto

type DashboardMetricsResponse struct {
	Habits   HabitsDashboardMetrics   `json:"habits"`
	Tasks    TasksDashboardMetrics    `json:"tasks"`
	Todos    TodosDashboardMetrics    `json:"todos"`
	Calendar CalendarDashboardMetrics `json:"calendar"`
	User     UserDashboardMetrics     `json:"user"`
}

type HabitsDashboardMetrics struct {
	Total     int `json:"total"`
	Active    int `json:"active"`
	Completed int `json:"completed"`
	Streak    int `json:"streak"`
}

type TasksDashboardMetrics struct {
	Total     int `json:"total"`
	Completed int `json:"completed"`
	Overdue   int `json:"overdue"`
}

type TodosDashboardMetrics struct {
	Total     int `json:"total"`
	Completed int `json:"completed"`
	Overdue   int `json:"overdue"`
}

type CalendarDashboardMetrics struct {
	Upcoming int `json:"upcoming"`
	Total    int `json:"total"`
}

type UserDashboardMetrics struct {
	ActivitySummary map[string]int `json:"activity_summary"`
}
