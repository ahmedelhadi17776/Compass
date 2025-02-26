from typing import Dict, List, Optional
from datetime import datetime
from Backend.ai_services.emotion_ai.emotion_service import EmotionService
from Backend.ai_services.nlp_service.nlp_service import NLPService
from Backend.ai_services.productivity_ai.productivity_service import ProductivityService
from Backend.ai_services.summarization_engine.summarization_service import SummarizationService
from Backend.ai_services.task_ai.task_classification_service import TaskClassificationService
from Backend.ai_services.workflow_ai.workflow_optimization_service import WorkflowOptimizationService
from Backend.ai_services.rag.rag_service import RAGService
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.errors import TaskNotFoundError
from Backend.services.integration_service import IntegrationService
from Backend.data_layer.repositories.agent_repository import AgentRepository
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)

class AIService:
    def __init__(self):
        self.emotion_service = EmotionService()
        self.nlp_service = NLPService()
        self.productivity_service = ProductivityService()
        self.summarization_service = SummarizationService()
        self.task_classifier = TaskClassificationService()
        self.workflow_optimizer = WorkflowOptimizationService()
        self.rag_service = RAGService()

    async def analyze_text(self, text: str, analysis_type: str) -> Dict:
        """Analyze text using different AI services."""
        try:
            results = {}
            if analysis_type in ["all", "sentiment"]:
                results["sentiment"] = await self.nlp_service.analyze_sentiment(text)
            if analysis_type in ["all", "emotion"]:
                results["emotion"] = await self.emotion_service.analyze_emotion(text)
            if analysis_type in ["all", "summary"]:
                results["summary"] = await self.summarization_service.generate_summary(text)
            if analysis_type in ["all", "keywords"]:
                results["keywords"] = await self.nlp_service.extract_keywords(text)
            return results
        except Exception as e:
            logger.error(f"Text analysis failed: {str(e)}")
            raise

    async def analyze_productivity(self, tasks: List[Dict], time_period: str = "daily") -> Dict:
        """Analyze task productivity patterns."""
        try:
            return await self.productivity_service.analyze_task_patterns(tasks, time_period)
        except Exception as e:
            logger.error(f"Productivity analysis failed: {str(e)}")
            raise

    async def classify_task(self, task_data: Dict, db_session=None, user_id: int = None) -> Dict:
        """Classify task using AI."""
        try:
            return await self.task_classifier.classify_task(
                task_data=task_data,
                db_session=db_session,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Task classification failed: {str(e)}")
            raise

    async def optimize_workflow(self, workflow_id: int, include_historical: bool = True) -> Dict:
        """Generate workflow optimization recommendations."""
        try:
            return await self.workflow_optimizer.optimize_workflow(
                workflow_id=workflow_id,
                include_historical=include_historical
            )
        except Exception as e:
            logger.error(f"Workflow optimization failed: {str(e)}")
            raise



    async def query_knowledge_base(self, query: str, limit: int = 5, filters: Dict = None) -> Dict:
        """Query the RAG knowledge base."""
        try:
            return await self.rag_service.query_knowledge_base(
                query=query,
                limit=limit,
                filters=filters
            )
        except Exception as e:
            logger.error(f"Knowledge base query failed: {str(e)}")
            raise

    async def get_emotional_context(self, text: str) -> Dict:
        """Get comprehensive emotional analysis including sentiment and key phrases."""
        try:
            return await self.emotion_service.get_emotional_context(text)
        except Exception as e:
            logger.error(f"Emotional context analysis failed: {str(e)}")
            raise

    async def summarize_workflow(self, workflow_data: Dict, include_metrics: bool = True) -> Dict:
        """Generate workflow summary with comprehensive metrics."""
        try:
            return await self.summarization_service.summarize_workflow(
                workflow_data=workflow_data,
                include_metrics=include_metrics
            )
        except Exception as e:
            logger.error(f"Workflow summarization failed: {str(e)}")
            raise

    async def summarize_task_group(self, tasks: List[Dict]) -> Dict:
        """Generate a summary for a group of related tasks."""
        try:
            return await self.summarization_service.summarize_task_group(tasks)
        except Exception as e:
            logger.error(f"Task group summarization failed: {str(e)}")
            raise

    async def process_task_with_ai(self, task_data: Dict, task_id: int, process_type: str) -> Dict:
        """Process task with AI agents."""
        if not task_data:
            raise TaskNotFoundError(f"Task {task_id} not found")

        integration_service = IntegrationService()
        result = await integration_service.process_with_agents(
            data=task_data,
            process_type=process_type
        )

        return {
            "ai_insights": result.get("analysis", {}),
            "ai_recommendations": result.get("recommendations", []),
            "last_ai_process": datetime.utcnow().isoformat()
        }

    async def find_similar_tasks_rag(self, task_data: Dict, task_id: int) -> Dict:
        """Find similar tasks using RAG."""
        if not task_data:
            raise TaskNotFoundError(f"Task {task_id} not found")

        query = f"{task_data['title']} {task_data['description']}"
        similar_tasks = await self.rag_service.query_knowledge_base(
            query=query,
            limit=5
        )

        return {
            "task_id": task_id,
            "similar_tasks": similar_tasks["sources"],
            "confidence": similar_tasks["confidence"]
        }

    async def index_task_for_rag(self, task_data: Dict, task_id: int) -> bool:
        """Index task in RAG knowledge base."""
        if not task_data:
            return False

        content = f"{task_data['title']}\n{task_data['description']}"
        return await self.rag_service.add_to_knowledge_base(
            content=content,
            metadata={
                "id": str(task_id),
                "title": task_data["title"],
                "status": task_data["status"],
                "priority": task_data["priority"],
                "project_id": task_data["project_id"]
            }
        )

    async def analyze_workflow(
        self,
        workflow_id: int,
        user_id: int,
        analysis_type: str,
        time_range: str,
        metrics: List[str]
    ) -> Dict:
        """Analyze workflow using AI services."""
        try:
            workflow_metrics = await self.workflow_optimizer.analyze_workflow_patterns(
                workflow_id=workflow_id,
                time_range=time_range
            )

            # Enhance metrics with AI insights
            metrics_data = {
                "performance": {
                    "average_completion_time": workflow_metrics.get("average_completion_time"),
                    "success_rate": workflow_metrics.get("success_rate"),
                    "optimization_score": workflow_metrics.get("optimization_score")
                },
                "execution": {
                    "total_executions": workflow_metrics.get("total_executions", 0),
                    "successful_executions": workflow_metrics.get("successful_executions", 0),
                    "failed_executions": workflow_metrics.get("failed_executions", 0)
                },
                "timing": {
                    "estimated_duration": workflow_metrics.get("estimated_duration"),
                    "actual_duration": workflow_metrics.get("actual_duration"),
                    "efficiency_ratio": workflow_metrics.get("efficiency_ratio")
                },
                "ai_metrics": {
                    "ai_enabled": workflow_metrics.get("ai_enabled", False),
                    "confidence_threshold": workflow_metrics.get("confidence_threshold"),
                    "learning_progress": workflow_metrics.get("learning_progress")
                }
            }

            return metrics_data
        except Exception as e:
            logger.error(f"Workflow analysis failed: {str(e)}")
            raise

    async def close(self):
        """Close all AI service connections."""
        await self.emotion_service.close()
        await self.nlp_service.close()
        await self.productivity_service.close()
        await self.summarization_service.close()
        await self.task_classifier.close()
        await self.workflow_optimizer.close()
    async def submit_feedback(
        self,
        interaction_id: int,
        feedback_score: float,
        feedback_text: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict:
        """Submit and process feedback for an AI interaction."""
        try:
            if not db:
                raise ValueError("Database session is required")

            # Initialize agent repository
            agent_repo = AgentRepository(db)

            # Get the existing interaction
            interaction = await agent_repo.get_agent_interaction(interaction_id)
            if not interaction:
                raise ValueError(f"Interaction with ID {interaction_id} not found")

            # Update the interaction with feedback
            updated_interaction = await agent_repo.update_agent_interaction(
                interaction_id=interaction_id,
                updates={
                    "feedback_score": feedback_score,
                    "feedback_text": feedback_text,
                    "feedback_timestamp": datetime.utcnow(),
                    "has_feedback": True
                }
            )

            # Process feedback for AI improvement
            await self._process_feedback_for_improvement(
                interaction_type=updated_interaction.interaction_type,
                feedback_score=feedback_score,
                feedback_text=feedback_text
            )

            return {
                "status": "success",
                "message": "Feedback submitted successfully",
                "interaction_id": interaction_id,
                "feedback_processed": True,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to submit feedback: {str(e)}")
            raise

    async def _process_feedback_for_improvement(self, interaction_type: str, feedback_score: float, feedback_text: Optional[str] = None):
        """Process feedback to improve AI services."""
        try:
            # Route feedback to appropriate service for learning
            if interaction_type == "text_analysis":
                await self.nlp_service.process_feedback(feedback_score, feedback_text)
            elif interaction_type == "emotion_analysis":
                await self.emotion_service.process_feedback(feedback_score, feedback_text)
            elif interaction_type == "task_classification":
                await self.task_classifier.process_feedback(feedback_score, feedback_text)
            elif interaction_type == "workflow_optimization":
                await self.workflow_optimizer.process_feedback(feedback_score, feedback_text)

            logger.info(f"Processed feedback for {interaction_type} interaction")

        except Exception as e:
            logger.error(f"Failed to process feedback for improvement: {str(e)}")
            # Don't raise the exception to avoid affecting the main feedback submission
            pass