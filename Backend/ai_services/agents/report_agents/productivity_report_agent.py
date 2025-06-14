"""
Agent for generating productivity reports.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from ai_services.agents.report_agents.base_report_agent import BaseReportAgent
from data_layer.models.report import ReportType
from ai_services.report.data_fetcher import DataFetcherService

logger = logging.getLogger(__name__)


class ProductivityReportAgent(BaseReportAgent):
    """
    Agent for generating productivity reports.

    This agent analyzes user productivity data and generates
    reports with insights and recommendations for improvement.
    """

    report_type = ReportType.PRODUCTIVITY
    name = "productivity_report_agent"
    description = "Agent for generating productivity reports with insights and recommendations"

    def __init__(self):
        """Initialize the productivity report agent."""
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
        Gather user productivity data for report generation.

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
            # Fetch multiple data types in parallel
            metric_types = [
                "productivity",
                "focus",
                "tasks",
                "todos",
                "calendar",
                "dashboard"
            ]

            metrics = await self.data_fetcher.fetch_metrics(
                user_id,
                metric_types,
                time_range,
                auth_token
            )

            # Add metrics to context
            context.update(metrics)

            # Calculate comparative metrics if possible
            if "productivity" in metrics and "productivity" in metrics["productivity"]:
                prod_data = metrics["productivity"]["productivity"]

                # Calculate average productivity score
                if "daily_scores" in prod_data:
                    daily_scores = prod_data["daily_scores"]
                    if daily_scores:
                        avg_score = sum(
                            score for _, score in daily_scores.items()) / len(daily_scores)
                        context["avg_productivity_score"] = round(avg_score, 2)

            # Extract focus time metrics
            if "focus" in metrics and "total_focus_time" in metrics["focus"]:
                context["total_focus_time"] = metrics["focus"]["total_focus_time"]
                context["daily_focus_time"] = metrics["focus"].get(
                    "daily_focus_time", {})

                # Calculate average daily focus time
                daily_focus = metrics["focus"].get("daily_focus_time", {})
                if daily_focus:
                    avg_focus = sum(
                        time for _, time in daily_focus.items()) / len(daily_focus)
                    context["avg_daily_focus_time"] = round(
                        avg_focus / 60, 2)  # Convert to hours

            # Extract task completion metrics
            if "tasks" in metrics:
                task_data = metrics["tasks"]
                context["task_completion_rate"] = task_data.get(
                    "completion_rate", 0)
                context["tasks_completed"] = task_data.get(
                    "completed_count", 0)
                context["tasks_total"] = task_data.get("total_count", 0)

            # Extract calendar metrics
            if "calendar" in metrics:
                calendar_data = metrics["calendar"]
                context["meeting_time"] = calendar_data.get(
                    "total_meeting_time", 0)
                context["meeting_count"] = calendar_data.get(
                    "meeting_count", 0)

            logger.info(
                f"Successfully gathered productivity data for user {user_id}")

        except Exception as e:
            logger.error(f"Error gathering productivity data: {str(e)}")
            context["error"] = str(e)

        return context

    async def _prepare_report_prompt(self, context: Dict[str, Any]) -> str:
        """
        Prepare the prompt for productivity report generation.

        Parameters:
            context (Dict[str, Any]): Context data for report generation

        Returns:
            str: Formatted prompt for LLM
        """
        time_range = context.get("time_range", {})
        start_date = time_range.get("start_date", "")
        end_date = time_range.get("end_date", "")

        # Extract key metrics for the prompt
        avg_productivity_score = context.get("avg_productivity_score", "N/A")
        avg_daily_focus_time = context.get("avg_daily_focus_time", "N/A")
        task_completion_rate = context.get("task_completion_rate", "N/A")
        tasks_completed = context.get("tasks_completed", "N/A")
        tasks_total = context.get("tasks_total", "N/A")
        meeting_time = context.get("meeting_time", "N/A")
        meeting_count = context.get("meeting_count", "N/A")

        prompt = f"""
        Generate a detailed productivity report for the user based on their data from {start_date} to {end_date}.
        
        Key metrics:
        - Average Productivity Score: {avg_productivity_score}
        - Average Daily Focus Time: {avg_daily_focus_time} hours
        - Task Completion Rate: {task_completion_rate}%
        - Tasks Completed: {tasks_completed} out of {tasks_total}
        - Meeting Time: {meeting_time} minutes across {meeting_count} meetings
        
        The report should include the following sections:
        1. Productivity Summary - A high-level overview of the user's productivity during this period
        2. Focus Time Analysis - Analysis of focus time patterns, effectiveness, and areas for improvement
        3. Task Completion Analysis - Insights into task completion patterns, efficiency, and bottlenecks
        4. Time Management - Analysis of calendar usage, meeting patterns, and time allocation
        5. Recommendations - Actionable suggestions for improving productivity based on the data
        
        Raw data:
        Productivity Data: {context.get("productivity", {})}
        Focus Data: {context.get("focus", {})}
        Task Data: {context.get("tasks", {})}
        Todo Data: {context.get("todos", {})}
        Calendar Data: {context.get("calendar", {})}
        Dashboard Data: {context.get("dashboard", {})}
        
        Return the report as a JSON with the following structure:
        {{
            "summary": "Brief summary of key findings",
            "content": {{
                "productivity_score": 85,  // Overall productivity score out of 100
                "key_metrics": {{
                    // Key metrics extracted from the data
                }},
                "insights": [
                    // List of key insights
                ],
                "areas_for_improvement": [
                    // List of areas that need improvement
                ]
            }},
            "sections": [
                {{
                    "title": "Productivity Summary",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Focus Time Analysis",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Task Completion Analysis",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Time Management",
                    "content": "Detailed analysis...",
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
