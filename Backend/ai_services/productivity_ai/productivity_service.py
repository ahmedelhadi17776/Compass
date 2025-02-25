from typing import Dict, List, Optional
from datetime import datetime, timedelta
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.ai_services.nlp_service.nlp_service import NLPService
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result

logger = get_logger(__name__)

class ProductivityService(AIServiceBase):
    def __init__(self):
        super().__init__("productivity")
        self.nlp_service = NLPService()
        self.model_version = "1.0.0"

    @cache_response(ttl=3600)
    async def analyze_task_patterns(
        self,
        tasks: List[Dict],
        time_period: str = "daily",
        include_predictions: bool = True
    ) -> Dict:
        """Analyze task completion patterns and productivity metrics."""
        try:
            cache_key = f"task_patterns:{hash(str(tasks))}:{time_period}"
            if cached_result := await get_cached_ai_result(cache_key):
                return cached_result

            metrics = await self._calculate_task_metrics(tasks, time_period)
            insights = await self._generate_task_insights(metrics)
            
            result = {
                "metrics": metrics,
                "insights": insights,
                "recommendations": await self._generate_recommendations(
                    metrics["completion_rate"],
                    metrics["avg_complexity"]
                )
            }

            if include_predictions:
                result["predictions"] = await self._predict_future_metrics(metrics)

            await cache_ai_result(cache_key, result)
            return result
        except Exception as e:
            logger.error(f"Error analyzing task patterns: {str(e)}")
            raise

    async def _calculate_task_metrics(self, tasks: List[Dict], time_period: str) -> Dict:
        """Calculate comprehensive task metrics."""
        try:
            total_tasks = len(tasks)
            completed_tasks = sum(1 for task in tasks if task.get("status") == "completed")
            
            # Calculate complexity scores using NLP
            complexity_scores = []
            for task in tasks:
                if description := task.get("description"):
                    complexity = await self.nlp_service.analyze_text_complexity(description)
                    complexity_scores.append(complexity["readability_score"])

            # Time-based calculations
            time_window = self._get_time_window(time_period)
            now = datetime.utcnow()
            recent_tasks = [
                task for task in tasks
                if datetime.fromisoformat(task.get("created_at", now.isoformat())) > now - time_window
            ]

            return {
                "completion_rate": completed_tasks / total_tasks if total_tasks > 0 else 0,
                "avg_complexity": sum(complexity_scores) / len(complexity_scores) if complexity_scores else 0,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "recent_completion_rate": self._calculate_recent_completion_rate(recent_tasks),
                "task_distribution": self._analyze_task_distribution(tasks),
                "time_metrics": self._calculate_time_metrics(tasks)
            }
        except Exception as e:
            logger.error(f"Error calculating task metrics: {str(e)}")
            raise

    async def _generate_task_insights(self, metrics: Dict) -> Dict:
        """Generate detailed insights from metrics."""
        try:
            return {
                "productivity_score": self._calculate_productivity_score(metrics),
                "efficiency_rating": self._determine_efficiency_rating(metrics),
                "trend_analysis": await self._analyze_trends(metrics),
                "bottleneck_identification": await self._identify_bottlenecks(metrics),
                "optimization_opportunities": await self._find_optimization_opportunities(metrics)
            }
        except Exception as e:
            logger.error(f"Error generating task insights: {str(e)}")
            raise

    def _get_time_window(self, time_period: str) -> timedelta:
        """Get time window for analysis."""
        return {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
            "quarterly": timedelta(days=90)
        }.get(time_period, timedelta(days=30))

    async def _predict_future_metrics(self, current_metrics: Dict) -> Dict:
        """Predict future productivity metrics."""
        try:
            return await self._make_request(
                "predict_metrics",
                data={"current_metrics": current_metrics}
            )
        except Exception as e:
            logger.error(f"Error predicting metrics: {str(e)}")
            return {}

    @cache_response(ttl=3600)
    async def analyze_workflow_efficiency(self, workflow_data: Dict) -> Dict:
        """Analyze workflow execution efficiency and bottlenecks."""
        try:
            steps = workflow_data.get("steps", [])
            total_time = workflow_data.get("actual_duration", 0)
            expected_time = workflow_data.get("estimated_duration", 0)

            efficiency_ratio = total_time / expected_time if expected_time > 0 else 0
            step_times = [step.get("duration", 0) for step in steps]
            avg_step_time = sum(step_times) / len(step_times) if step_times else 0

            # Analyze step descriptions for complexity
            step_complexities = []
            for step in steps:
                description = step.get("description", "")
                if description:
                    sentiment = await self.nlp_service.analyze_sentiment(description)
                    step_complexities.append(sentiment["confidence"])

            avg_step_complexity = sum(step_complexities) / len(step_complexities) if step_complexities else 0

            return {
                "efficiency_metrics": {
                    "efficiency_ratio": efficiency_ratio,
                    "average_step_time": avg_step_time,
                    "total_steps": len(steps),
                    "average_step_complexity": avg_step_complexity
                },
                "optimization_suggestions": self._analyze_workflow_bottlenecks(steps)
            }
        except Exception as e:
            logger.error(f"Error analyzing workflow efficiency: {str(e)}")
            raise

    def _generate_recommendations(self, completion_rate: float, complexity: float) -> List[str]:
        """Generate productivity recommendations based on metrics."""
        recommendations = []
        if completion_rate < 0.5:
            recommendations.append("Consider breaking down tasks into smaller, more manageable units")
        if complexity > 0.7:
            recommendations.append("Task descriptions indicate high complexity. Consider simplifying or delegating")
        if completion_rate < 0.3 and complexity > 0.5:
            recommendations.append("High task complexity may be impacting completion rates. Review task allocation")
        return recommendations

    def _analyze_workflow_bottlenecks(self, steps: List[Dict]) -> List[str]:
        """Identify workflow bottlenecks and suggest optimizations."""
        suggestions = []
        step_times = [(step.get("duration", 0), step.get("name", "Unknown")) for step in steps]
        avg_time = sum(time for time, _ in step_times) / len(step_times) if step_times else 0

        for duration, step_name in step_times:
            if duration > avg_time * 1.5:
                suggestions.append(f"Step '{step_name}' takes significantly longer than average. Consider optimization")

        return suggestions