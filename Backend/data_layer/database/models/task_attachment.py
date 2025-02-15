from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class TaskAttachment(Base):
    __tablename__ = "task_attachments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey(
        "tasks.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[
                            uploaded_by], back_populates="uploaded_attachments")

    __table_args__ = (
        Index("ix_task_attachments_task_id", "task_id"),
        Index("ix_task_attachments_uploaded_by", "uploaded_by"),
        Index("ix_task_attachments_created_at", "created_at"),
        Index("ix_task_attachments_file_type", "file_type"),
    )
