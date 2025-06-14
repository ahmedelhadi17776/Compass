"""
Agent for generating dashboard reports.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from ai_services.agents.report_agents.base_report_agent import BaseReportAgent
from data_layer.models.report import ReportType
from ai_services.report.data_fetcher import DataFetcherService
from core.mcp_state import get_mcp_client

logger = logging.getLogger(__name__)


class DashboardReportAgent(BaseReportAgent):
    """
    Agent for generating dashboard reports.

    This agent creates comprehensive dashboard reports that provide
    an overview of user activity across multiple aspects of the platform,
    similar to a summary report but with a focus on dashboard metrics.
    """

    report_type = ReportType.DASHBOARD
    name = "dashboard_report_agent"
    description = "Agent for generating comprehensive dashboard reports across multiple data types"

    def __init__(self):
        """Initialize the dashboard report agent."""
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
        Gather comprehensive user data for dashboard report generation.

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

            context.update(metrics)
            context['time_range'] = time_range

            logger.info(
                f"Successfully gathered dashboard data for user {user_id}")

        except Exception as e:
            logger.error(f"Error gathering dashboard data: {str(e)}")
            context["error"] = str(e)

        return context

    async def _prepare_report_prompt(self, context: Dict[str, Any]) -> str:
        """
        Prepare the prompt for dashboard report generation.

        Parameters:
            context (Dict[str, Any]): Context data for report generation

        Returns:
            str: Formatted prompt for LLM
        """
        time_range = context.get("time_range", {})
        start_date = time_range.get("start_date", "")
        end_date = time_range.get("end_date", "")

        prompt = f"""
        Generate a comprehensive dashboard report for the user based on their data from {start_date} to {end_date}.
        The report should be a narrative summary of the key metrics and insights available on their dashboard.
        
        The report should include the following sections:
        1. Executive Summary - A high-level overview of the user's activity and achievements.
        2. Productivity Overview - Summary of productivity scores, focus time, and task completion.
        3. Habit Consistency - Analysis of habit formation and streaks.
        4. Time Management - Insights from calendar events and meeting patterns.
        5. Key Recommendations - Actionable suggestions based on the dashboard data.
        
        Use the following data to construct the report:
        {context}
        
        Return the report as a JSON with the following structure:
        {{
            "summary": "Brief executive summary of key findings from the dashboard.",
            "content": {{
                "overall_score": 85,  // An overall user performance score out of 100 based on dashboard data
                "key_insights": [
                    // List of key insights derived from the dashboard metrics
                ],
                "recommendations": [
                    // List of actionable recommendations based on the dashboard data
                ]
            }},
            "sections": [
                {{
                    "title": "Executive Summary",
                    "content": "Detailed summary...",
                    "type": "text"
                }},
                {{
                    "title": "Productivity Overview",
                    "content": "Detailed overview...",
                    "type": "text"
                }},
                {{
                    "title": "Habit Consistency",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Time Management",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Key Recommendations",
                    "content": "Detailed recommendations...",
                    "type": "text"
                }}
            ]
        }}
        """

        return prompt
