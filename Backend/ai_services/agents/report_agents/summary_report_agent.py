"""
Agent for generating summary reports.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from ai_services.agents.report_agents.base_report_agent import BaseReportAgent
from data_layer.models.report import ReportType
from ai_services.report.data_fetcher import DataFetcherService

logger = logging.getLogger(__name__)


class SummaryReportAgent(BaseReportAgent):
    """
    Agent for generating summary reports.

    This agent creates comprehensive summary reports that provide
    an overview of user activity across multiple aspects of the platform.
    """

    report_type = ReportType.SUMMARY
    name = "summary_report_agent"
    description = "Agent for generating comprehensive summary reports across multiple data types"

    def __init__(self):
        """Initialize the summary report agent."""
        super().__init__()
        self.data_fetcher = DataFetcherService()

    async def gather_context(
        self,
        user_id: str,
        parameters: Dict[str, Any],
        time_range: Dict[str, str],
        auth_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Gather comprehensive user data for summary report generation.

        Parameters:
            user_id (str): User ID to gather data for
            parameters (Dict[str, Any]): Additional parameters for gathering context
            time_range (Dict[str, str]): Time range for data (start_date, end_date)
            auth_token (Optional[str]): Authentication token

        Returns:
            Dict[str, Any]: Context data for report generation
        """
        # Get basic context from parent class
        context = await super().gather_context(user_id, parameters, time_range, auth_token)

        try:
            # Fetch data from all available sources
            metric_types = [
                "activity",
                "productivity",
                "focus",
                "tasks",
                "todos",
                "habits",
                "calendar",
                "dashboard"
            ]

            metrics = await self.data_fetcher.fetch_metrics(
                user_id,
                metric_types,
                time_range,
                auth_token
            )

            # Also fetch dashboard data which may contain additional metrics
            dashboard_data = await self.data_fetcher.fetch_dashboard_data(
                user_id,
                auth_token
            )

            if dashboard_data:
                metrics["dashboard"] = dashboard_data

            # Add all metrics to context
            context.update(metrics)

            # Extract key metrics for easier access in prompt generation
            self._extract_key_metrics(context, metrics)

            logger.info(
                f"Successfully gathered summary data for user {user_id}")

        except Exception as e:
            logger.error(f"Error gathering summary data: {str(e)}")
            context["error"] = str(e)

        return context

    def _extract_key_metrics(self, context: Dict[str, Any], metrics: Dict[str, Any]) -> None:
        """Extract key metrics from raw data for easier access in prompt generation."""
        # Extract activity metrics
        if "activity" in metrics and metrics["activity"]:
            activity = metrics["activity"]
            context["active_days"] = activity.get("active_days", 0)
            context["active_hours"] = activity.get("active_hours", 0)

        # Extract productivity metrics
        if "productivity" in metrics and metrics["productivity"]:
            productivity = metrics["productivity"]
            if "productivity" in productivity:
                prod_data = productivity["productivity"]
                if "daily_scores" in prod_data:
                    daily_scores = prod_data["daily_scores"]
                    if daily_scores:
                        avg_score = sum(
                            score for _, score in daily_scores.items()) / len(daily_scores)
                        context["avg_productivity_score"] = round(avg_score, 2)

        # Extract focus metrics
        if "focus" in metrics and metrics["focus"]:
            focus = metrics["focus"]
            context["total_focus_time"] = focus.get("total_focus_time", 0)
            context["focus_sessions"] = focus.get("sessions", 0)

        # Extract task metrics
        if "tasks" in metrics and metrics["tasks"]:
            tasks = metrics["tasks"]
            context["task_completion_rate"] = tasks.get("completion_rate", 0)
            context["tasks_completed"] = tasks.get("completed_count", 0)
            context["tasks_total"] = tasks.get("total_count", 0)

        # Extract habit metrics
        if "habits" in metrics and metrics["habits"]:
            habits = metrics["habits"]
            context["habit_completion_rate"] = habits.get("completion_rate", 0)
            context["habits_completed"] = habits.get("completed_count", 0)
            context["habits_total"] = habits.get("total_count", 0)

        # Extract calendar metrics
        if "calendar" in metrics and metrics["calendar"]:
            calendar = metrics["calendar"]
            context["meeting_time"] = calendar.get("total_meeting_time", 0)
            context["meeting_count"] = calendar.get("meeting_count", 0)

    async def _prepare_report_prompt(self, context: Dict[str, Any]) -> str:
        """
        Prepare the prompt for summary report generation.

        Parameters:
            context (Dict[str, Any]): Context data for report generation

        Returns:
            str: Formatted prompt for LLM
        """
        time_range = context.get("time_range", {})
        start_date = time_range.get("start_date", "")
        end_date = time_range.get("end_date", "")

        # Extract key metrics for the prompt
        active_days = context.get("active_days", "N/A")
        activity_trend = context.get("activity_trend", "N/A")
        avg_productivity_score = context.get("avg_productivity_score", "N/A")
        avg_daily_focus_time = context.get("avg_daily_focus_time", "N/A")
        task_completion_rate = context.get("task_completion_rate", "N/A")
        tasks_completed = context.get("tasks_completed", "N/A")
        habit_completion_rate = context.get("habit_completion_rate", "N/A")
        meeting_time = context.get("meeting_time", "N/A")
        meeting_count = context.get("meeting_count", "N/A")
        project_completion_rate = context.get("project_completion_rate", "N/A")
        workflows_executed = context.get("workflows_executed", "N/A")

        prompt = f"""
        Generate a comprehensive summary report for the user based on their data from {start_date} to {end_date}.
        
        Key metrics across domains:
        - Active Days: {active_days} days
        - Activity Trend: {activity_trend}
        - Average Productivity Score: {avg_productivity_score}
        - Average Daily Focus Time: {avg_daily_focus_time} hours
        - Task Completion Rate: {task_completion_rate}%
        - Tasks Completed: {tasks_completed}
        - Habit Completion Rate: {habit_completion_rate}%
        - Meeting Time: {meeting_time} minutes across {meeting_count} meetings
        - Project Completion Rate: {project_completion_rate}%
        - Workflows Executed: {workflows_executed}
        
        The report should include the following sections:
        1. Executive Summary - A high-level overview of the user's activity and achievements
        2. Activity Analysis - Analysis of user activity patterns and trends
        3. Productivity Overview - Summary of productivity metrics and focus time
        4. Task & Project Management - Overview of task and project completion
        5. Habit Building - Summary of habit formation and consistency
        6. Time Management - Analysis of calendar usage and time allocation
        7. Key Achievements - Highlight of major accomplishments during this period
        8. Areas for Improvement - Identification of areas that need attention
        9. Recommendations - Actionable suggestions across different domains
        
        Raw data:
        Activity Data: {context.get("activity", {})}
        Productivity Data: {context.get("productivity", {})}
        Focus Data: {context.get("focus", {})}
        Task Data: {context.get("tasks", {})}
        Todo Data: {context.get("todos", {})}
        Habit Data: {context.get("habits", {})}
        Calendar Data: {context.get("calendar", {})}
        Project Data: {context.get("projects", {})}
        Workflow Data: {context.get("workflow", {})}
        Dashboard Data: {context.get("dashboard", {})}
        
        Return the report as a JSON with the following structure:
        {{
            "summary": "Brief executive summary of key findings",
            "content": {{
                "overall_score": 85,  // Overall user performance score out of 100
                "key_metrics": {{
                    // Key metrics extracted from the data across domains
                }},
                "achievements": [
                    // List of key achievements
                ],
                "areas_for_improvement": [
                    // List of areas that need improvement
                ],
                "recommendations": [
                    // List of recommendations across domains
                ]
            }},
            "sections": [
                {{
                    "title": "Executive Summary",
                    "content": "Detailed summary...",
                    "type": "text"
                }},
                {{
                    "title": "Activity Analysis",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Productivity Overview",
                    "content": "Detailed overview...",
                    "type": "text"
                }},
                {{
                    "title": "Task & Project Management",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Habit Building",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Time Management",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Key Achievements",
                    "content": "Detailed achievements...",
                    "type": "text"
                }},
                {{
                    "title": "Areas for Improvement",
                    "content": "Detailed areas...",
                    "type": "text"
                }},
                {{
                    "title": "Recommendations",
                    "content": "Detailed recommendations...",
                    "type": "text"
                }}
            ]
        }}
        """

        return prompt
