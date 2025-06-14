export type ReportType = "productivity" | "activity" | "dashboard";

export interface CreateReportPayload {
  title: string;
  type: ReportType;
  time_range: {
    start_date: string;
    end_date: string;
  };
}

export interface CreateReportResponse {
  report_id: string;
}

export interface ReportGenerationUpdate {
  status: "in_progress" | "completed" | "failed";
  progress: number;
  message: string;
  report_id: string;
}

export interface ParsedReportSection {
    title: string;
    content: string;
    type: string;
}

export interface DashboardReportInnerContent {
    overall_score: number;
    key_insights: string[];
    recommendations: string[];
}

export interface ActivityReportInnerContent {
    activity_score: number;
    key_metrics: {
        tasks_completed: string;
        overdue_tasks: number;
        meetings_attended: number;
        total_meeting_time_minutes: number;
    };
    insights: string[];
}

export interface ParsedReportContent {
    summary: string;
    content: DashboardReportInnerContent | ActivityReportInnerContent;
    sections: ParsedReportSection[];
}

export interface TimeRange {
    start_date: string;
    end_date: string;
}

export interface ReportTextContent {
    text: string;
}

export interface Report {
    id: string;
    title: string;
    type: ReportType;
    status: 'completed' | 'in_progress' | 'failed';
    content: ReportTextContent;
    user_id: string;
    created_at: string;
    updated_at: string;
    completed_at: string | null;
    parameters: object;
    time_range: TimeRange;
    custom_prompt: string | null;
    summary: string | null;
    sections: ParsedReportSection[];
    error: string | null;
    parsedContent?: ParsedReportContent;
}
