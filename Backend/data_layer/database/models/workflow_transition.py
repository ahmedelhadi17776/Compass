from sqlalchemy import Column, Integer, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"

    id = Column(Integer, primary_key=True, index=True)
    from_step_id = Column(Integer, ForeignKey(
        "workflow_steps.id", ondelete="CASCADE"))
    to_step_id = Column(Integer, ForeignKey(
        "workflow_steps.id", ondelete="CASCADE"))
    conditions = Column(JSON)
    triggers = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    from_step = relationship("WorkflowStep", foreign_keys=[
                             from_step_id], back_populates="transitions_from")
    to_step = relationship("WorkflowStep", foreign_keys=[
                           to_step_id], back_populates="transitions_to")
