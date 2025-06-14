export interface DashboardReport {
  status: 'completed' | 'in_progress' | 'failed';
  report_id: string;
  progress: number;
  message: string;
  report: {
    id: string;
    summary: string;
    content: {
      overall_score: number;
      key_insights: string[];
      recommendations: string[];
    }
  }
}

export interface ReportData {
  dashboard: DashboardReport;
  // Add other report types here as needed
}

// Mock data
export const mockReportData: ReportData = {
  dashboard: {
    status: "completed",
    report_id: "684c7d166ad52debed43dc65",
    progress: 1.0,
    message: "Report generation completed",
    report: {
      id: "684c7d166ad52debed43dc65",
      summary: "Between June 1 and June 13, 2025, the user demonstrated moderate engagement with their productivity and habit tracking tools, with notable focus time achieved on a few days but limited task completion and habit streaks. Calendar activity was present but minimal, and overall system metrics suggest a stable productivity score. Key areas for improvement include increasing habit completion, enhancing focus consistency, and addressing overdue tasks.",
      content: {
        overall_score: 85,
        key_insights: [
          "The user maintained 6 active habits but did not complete any during the period, resulting in no ongoing streaks.",
          "Focus time totaled 3 hours (10,800 seconds) across 3 sessions, with the longest streak being 1 day, falling short of the daily target of 10 hours.",
          "Task completion was low, with zero tasks completed and 2 overdue todos out of 4 total todos.",
          "Calendar events totaled 14 with only 1 upcoming event, indicating a relatively light schedule.",
          "User activity was high in terms of actions (314) and logins (308), showing consistent engagement with the system.",
          "Mood was recorded as neutral in the single journal entry, suggesting a stable emotional state during this timeframe.",
          "System productivity scores were stable around 87.5, reflecting consistent performance levels."
        ],
        recommendations: [
          "Focus on completing habits consistently to build streaks and improve habit formation.",
          "Increase daily focus time gradually to meet or exceed the 10-hour daily target for better productivity.",
          "Prioritize clearing overdue todos and managing task lists to reduce backlog and improve task completion rates.",
          "Leverage calendar planning to better distribute workload and avoid last-minute scheduling.",
          "Continue regular journaling to monitor mood trends and identify factors influencing productivity."
        ]
      }
    }
  }
} 