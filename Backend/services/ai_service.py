from typing import Dict, List, Optional, Any, Union, cast
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
from Backend.ai_services.llm.llm_service import LLMService
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.orchestration.crew_orchestrator import CrewOrchestrator
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.database.models.task import Task
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
import json

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
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()
        self.crew_orchestrator = CrewOrchestrator()

    async def analyze_text(self, text: str, analysis_type: str) -> Dict[str, Any]:
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

    async def analyze_productivity(self, tasks: List[Dict[str, Any]], time_period: str = "daily") -> Dict[str, Any]:
        """Analyze task productivity patterns."""
        try:
            return await self.productivity_service.analyze_task_patterns(tasks, time_period)
        except Exception as e:
            logger.error(f"Productivity analysis failed: {str(e)}")
            raise

    async def classify_task(self, task_data: Dict[str, Any], db_session: Optional[AsyncSession] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
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

    async def optimize_workflow(self, workflow_id: int, include_historical: bool = True) -> Dict[str, Any]:
        """Generate workflow optimization recommendations."""
        try:
            return await self.workflow_optimizer.optimize_workflow(
                workflow_id=workflow_id,
                include_historical=include_historical
            )
        except Exception as e:
            logger.error(f"Workflow optimization failed: {str(e)}")
            raise

    async def query_knowledge_base(self, query: str, limit: int = 5, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

    async def get_emotional_context(self, text: str) -> Dict[str, Any]:
        """Get comprehensive emotional analysis including sentiment and key phrases."""
        try:
            return await self.emotion_service.get_emotional_context(text)
        except Exception as e:
            logger.error(f"Emotional context analysis failed: {str(e)}")
            raise

    async def summarize_workflow(self, workflow_data: Dict[str, Any], include_metrics: bool = True) -> Dict[str, Any]:
        """Generate workflow summary with comprehensive metrics."""
        try:
            return await self.summarization_service.summarize_workflow(
                workflow_data=workflow_data,
                include_metrics=include_metrics
            )
        except Exception as e:
            logger.error(f"Workflow summarization failed: {str(e)}")
            raise

    async def summarize_task_group(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary for a group of related tasks."""
        try:
            return await self.summarization_service.summarize_task_group(tasks)
        except Exception as e:
            logger.error(f"Task group summarization failed: {str(e)}")
            raise

    async def process_task_with_ai(self, task_id: int, db_session: AsyncSession) -> Dict[str, Any]:
        """Process a task with AI agents and update the database.

        Args:
            task_id: ID of the task to process
            db_session: Database session

        Returns:
            Dict with processing results
        """
        try:
            # Initialize repositories
            task_repo = TaskRepository(db_session)
            agent_repo = AgentRepository(db_session)

            # Get task from database
            task = await task_repo.get_task_with_details(task_id)
            if not task:
                return {"error": f"Task with ID {task_id} not found"}

            # Process task with crew orchestrator
            results = await self.crew_orchestrator.process_db_task(task_id)

            # Record AI interaction
            interaction = AIAgentInteraction(
                task_id=task_id,
                agent_type="crew_orchestrator",
                interaction_type="task_processing",
                input_data=json.dumps({"task_id": task_id}),
                output_data=json.dumps(results),
                timestamp=datetime.utcnow()
            )

            # Add method to create AI interaction if it doesn't exist
            if hasattr(agent_repo, "create_ai_interaction"):
                await agent_repo.create_ai_interaction(interaction)
            else:
                logger.warning(
                    "AgentRepository does not have create_ai_interaction method")

            # Update task with AI suggestions if available
            if "output" in results and not results.get("error"):
                # Get current AI suggestions
                ai_suggestions = {}
                if hasattr(task, "ai_suggestions") and task.ai_suggestions is not None:
                    if isinstance(task.ai_suggestions, dict):
                        ai_suggestions = task.ai_suggestions
                    else:
                        logger.warning(
                            f"Task ai_suggestions is not a dictionary: {type(task.ai_suggestions)}")

                # Add new suggestions
                ai_suggestions["crew_processing"] = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": results.get("output")
                }

                await task_repo.update_task(task_id, {"ai_suggestions": ai_suggestions})

            return results
        except Exception as e:
            logger.error(f"Error processing task with AI: {str(e)}")
            return {"error": f"Error processing task with AI: {str(e)}"}

    async def store_task_context(self, task_id: int, context_data: Dict[str, Any], db_session: AsyncSession) -> bool:
        """Store task context in the vector database for future reference.

        Args:
            task_id: ID of the task
            context_data: Context data to store
            db_session: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Get task from database
            task_repo = TaskRepository(db_session)
            task = await task_repo.get_task(task_id)
            if not task:
                logger.error(f"Task with ID {task_id} not found")
                return False

            # Prepare metadata
            metadata = {
                "task_id": task_id,
                "title": task.title,
                "type": "task_context",
                "created_at": datetime.utcnow().isoformat(),
                "source": "ai_service"
            }

            # Convert context data to string
            content = json.dumps(context_data)

            # Store in vector database
            result = await self.rag_service.add_to_knowledge_base(
                content=content,
                metadata=metadata
            )

            return result
        except Exception as e:
            logger.error(f"Error storing task context: {str(e)}")
            return False

    async def retrieve_similar_tasks(self, task_description: str, limit: int = 5, db_session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        """Find similar tasks based on semantic similarity.

        Args:
            task_description: Description of the task to find similar tasks for
            limit: Maximum number of similar tasks to return
            db_session: Optional database session

        Returns:
            List of similar tasks
        """
        try:
            # Query vector database
            results = await self.rag_service.query_knowledge_base(
                query=task_description,
                limit=limit,
                filters={"type": "task_context"}
            )

            # Extract task IDs from results
            task_ids = []
            if results.get("sources"):
                for source in results["sources"]:
                    if isinstance(source, dict) and source.get("task_id"):
                        task_ids.append(source["task_id"])

            # If we have a database session, get task details
            if db_session and task_ids:
                task_repo = TaskRepository(db_session)
                tasks = []
                for task_id in task_ids:
                    task = await task_repo.get_task(task_id)
                    if task:
                        tasks.append({
                            "id": task.id,
                            "title": task.title,
                            "description": task.description,
                            "status": str(task.status),
                            "priority": str(task.priority),
                            "similarity_score": results.get("confidence", 0)
                        })
                return tasks

            return [{"task_id": source.get("task_id")} for source in results.get("sources", [])]
        except Exception as e:
            logger.error(f"Error retrieving similar tasks: {str(e)}")
            return []

    async def analyze_workflow(
        self,
        workflow_id: int,
        user_id: int,
        analysis_type: str,
        time_range: str,
        metrics: List[str]
    ) -> Dict[str, Any]:
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
        await self.llm_service.close()
        await self.embedding_service.close()
        await self.crew_orchestrator.close()

    async def submit_feedback(
        self,
        interaction_id: int,
        feedback_score: float,
        feedback_text: Optional[str] = None,
        db: Optional[AsyncSession] = None
    ) -> Dict[str, Any]:
        """Submit and process feedback for an AI interaction."""
        try:
            if not db:
                raise ValueError("Database session is required")

            # Initialize agent repository
            agent_repo = AgentRepository(db)

            # Get the existing interaction
            interaction = await agent_repo.get_agent_interaction(interaction_id)
            if not interaction:
                raise ValueError(
                    f"Interaction with ID {interaction_id} not found")

            # Update the interaction with feedback
            # Add method if it doesn't exist
            if hasattr(agent_repo, "update_agent_interaction"):
                updated_interaction = await agent_repo.update_agent_interaction(
                    interaction_id=interaction_id,
                    updates={
                        "feedback_score": feedback_score,
                        "feedback_text": feedback_text,
                        "feedback_timestamp": datetime.utcnow(),
                        "has_feedback": True
                    }
                )
            else:
                logger.warning(
                    "AgentRepository does not have update_agent_interaction method")
                updated_interaction = interaction

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
                # Add method if it doesn't exist
                if hasattr(self.workflow_optimizer, "process_feedback"):
                    await self.workflow_optimizer.process_feedback(feedback_score, feedback_text)
                else:
                    logger.warning(
                        "WorkflowOptimizationService does not have process_feedback method")

            logger.info(
                f"Processed feedback for {interaction_type} interaction")

        except Exception as e:
            logger.error(
                f"Failed to process feedback for improvement: {str(e)}")
            # Don't raise the exception to avoid affecting the main feedback submission
            pass
