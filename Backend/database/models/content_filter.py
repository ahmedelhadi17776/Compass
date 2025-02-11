from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .import Base


class ContentFilterRule(Base):
    """Model representing a content filtering rule."""
    __tablename__ = "content_filter_rules"

    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), unique=True, nullable=False)
    description = Column(String(512))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ContentFilterRule(id={self.id}, keyword={self.keyword})>"
