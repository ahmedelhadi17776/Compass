"""
Agent for generating habits reports.
"""
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta

from ai_services.agents.report_agents.base_report_agent import BaseReportAgent
from data_layer.models.report import ReportType
from ai_services.report.data_fetcher import DataFetcherService

logger = logging.getLogger(__name__)


class HabitsReportAgent(BaseReportAgent):
    """
    Agent for generating habits reports.

    This agent analyzes user habits data and generates
    reports with insights and recommendations for habit building.
    """

    report_type = ReportType.HABITS
    name = "habits_report_agent"
    description = "Agent for generating habits reports with insights and recommendations"

    def __init__(self):
        """Initialize the habits report agent."""
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
        Gather user habits data for report generation.

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
            habits_data = await self.data_fetcher.fetch_user_data(
                user_id,
                "habits",
                {},
                time_range,
                auth_token,
            )

            # Add habits data to context
            context["habits_data"] = habits_data

            # Extract key metrics
            if habits_data:
                # Get habit completion rate
                if "completion_rate" in habits_data:
                    context["habit_completion_rate"] = habits_data["completion_rate"]

                # Get habit streaks
                if "streaks" in habits_data:
                    context["habit_streaks"] = habits_data["streaks"]

                # Get habit categories
                if "categories" in habits_data:
                    context["habit_categories"] = habits_data["categories"]

                # Get habit consistency
                if "consistency" in habits_data:
                    context["habit_consistency"] = habits_data["consistency"]

                # Get top habits
                if "habits" in habits_data:
                    habits = habits_data["habits"]

                    # Sort habits by completion rate
                    if isinstance(habits, list) and len(habits) > 0:
                        sorted_habits = sorted(
                            habits,
                            key=lambda h: h.get("completion_rate", 0),
                            reverse=True
                        )

                        context["top_habits"] = sorted_habits[:5]
                        context["bottom_habits"] = sorted_habits[-5:] if len(
                            sorted_habits) >= 5 else sorted_habits

            logger.info(
                f"Successfully gathered habits data for user {user_id}")

        except Exception as e:
            logger.error(f"Error gathering habits data: {str(e)}")
            context["error"] = str(e)

        return context

    async def _prepare_report_prompt(self, context: Dict[str, Any]) -> str:
        """
        Prepare the prompt for habits report generation.

        Parameters:
            context (Dict[str, Any]): Context data for report generation

        Returns:
            str: Formatted prompt for LLM
        """
        time_range = context.get("time_range", {})
        start_date = time_range.get("start_date", "")
        end_date = time_range.get("end_date", "")

        # Extract key metrics for the prompt
        completion_rate = context.get("habit_completion_rate", "N/A")
        habit_streaks = context.get("habit_streaks", {})
        habit_categories = context.get("habit_categories", {})
        habit_consistency = context.get("habit_consistency", {})
        top_habits = context.get("top_habits", [])
        bottom_habits = context.get("bottom_habits", [])

        # Format top habits for the prompt
        top_habits_str = "\n".join([
            f"- {h.get('name', 'Unknown')}: {h.get('completion_rate', 0)}% completion rate"
            for h in top_habits
        ]) if top_habits else "No habit data available"

        # Format bottom habits for the prompt
        bottom_habits_str = "\n".join([
            f"- {h.get('name', 'Unknown')}: {h.get('completion_rate', 0)}% completion rate"
            for h in bottom_habits
        ]) if bottom_habits else "No habit data available"

        prompt = f"""
        Generate a detailed habits report for the user based on their data from {start_date} to {end_date}.
        
        Key metrics:
        - Overall Habit Completion Rate: {completion_rate}%
        
        Top performing habits:
        {top_habits_str}
        
        Habits needing improvement:
        {bottom_habits_str}
        
        The report should include the following sections:
        1. Habits Summary - A high-level overview of the user's habit performance during this period
        2. Habit Streaks Analysis - Analysis of habit streaks, consistency, and patterns
        3. Category Analysis - Insights into performance across different habit categories
        4. Time of Day Analysis - When the user is most successful at completing habits
        5. Recommendations - Actionable suggestions for improving habit consistency and building new habits
        
        Raw data:
        Habits Data: {context.get("habits_data", {})}
        Habit Streaks: {habit_streaks}
        Habit Categories: {habit_categories}
        Habit Consistency: {habit_consistency}
        
        Return the report as a JSON with the following structure:
        {{
            "summary": "Brief summary of key findings",
            "content": {{
                "overall_score": 85,  // Overall habits score out of 100
                "key_metrics": {{
                    // Key metrics extracted from the data
                }},
                "insights": [
                    // List of key insights
                ],
                "habit_recommendations": [
                    // List of habit-specific recommendations
                ]
            }},
            "sections": [
                {{
                    "title": "Habits Summary",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Habit Streaks Analysis",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Category Analysis",
                    "content": "Detailed analysis...",
                    "type": "text"
                }},
                {{
                    "title": "Time of Day Analysis",
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
