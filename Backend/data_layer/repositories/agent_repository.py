from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional, Dict
from Backend.data_layer.database.models.ai_models import (
    AgentAction, AgentFeedback, AIModel, AgentType
)
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction
from datetime import datetime


class AgentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_agent_action(self, **action_data) -> AgentAction:
        """Create a new agent action."""
        action = AgentAction(**action_data)
        self.session.add(action)
        await self.session.commit()
        await self.session.refresh(action)
        return action

    async def get_agent_action(self, action_id: int) -> Optional[AgentAction]:
        """Get an agent action by ID."""
        result = await self.session.execute(
            select(AgentAction).where(AgentAction.id == action_id)
        )
        return result.scalar_one_or_none()

    async def update_agent_action(self, action_id: int, updates: Dict) -> Optional[AgentAction]:
        """Update an agent action."""
        action = await self.get_agent_action(action_id)
        if action:
            for key, value in updates.items():
                setattr(action, key, value)
            await self.session.commit()
            await self.session.refresh(action)
        return action

    async def create_agent_feedback(self, **feedback_data) -> AgentFeedback:
        """Create feedback for an agent action."""
        feedback = AgentFeedback(**feedback_data)
        self.session.add(feedback)
        await self.session.commit()
        await self.session.refresh(feedback)
        return feedback

    async def create_agent_interaction(self, **interaction_data) -> AIAgentInteraction:
        """Create a new AI agent interaction."""
        interaction = AIAgentInteraction(**interaction_data)
        self.session.add(interaction)
        await self.session.commit()
        await self.session.refresh(interaction)
        return interaction

    async def get_agent_interactions(
        self,
        user_id: Optional[int] = None,
        agent_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AIAgentInteraction]:
        """Get agent interactions with optional filtering."""
        query = select(AIAgentInteraction)
        
        if user_id:
            query = query.where(AIAgentInteraction.user_id == user_id)
        if agent_type:
            query = query.where(AIAgentInteraction.agent_type == agent_type)
        if start_date:
            query = query.where(AIAgentInteraction.created_at >= start_date)
        if end_date:
            query = query.where(AIAgentInteraction.created_at <= end_date)
        
        query = query.limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_agent_performance_metrics(
        self,
        agent_type: Optional[str] = None,
        time_period: Optional[int] = None  # in days
    ) -> Dict:
        """Get performance metrics for agents."""
        query = select(AIAgentInteraction)
        if agent_type:
            query = query.where(AIAgentInteraction.agent_type == agent_type)
        if time_period:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period)
            query = query.where(AIAgentInteraction.created_at >= cutoff_date)
        
        result = await self.session.execute(query)
        interactions = list(result.scalars().all())
        
        return {
            "total_interactions": len(interactions),
            "average_success_rate": sum(i.success_rate or 0 for i in interactions) / len(interactions) if interactions else 0,
            "average_feedback_score": sum(i.feedback_score or 0 for i in interactions) / len(interactions) if interactions else 0,
            "total_helpful_interactions": sum(1 for i in interactions if i.was_helpful),
            "average_execution_time": sum(i.execution_time or 0 for i in interactions) / len(interactions) if interactions else 0
        }