from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.sql import func


class SubscriptionPlan(Base):
    """Subscription plans available to users."""
    __tablename__ = 'subscription_plans'
    __table_args__ = (
        Index('ix_subscription_plans_name', 'name', unique=True),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    price = Column(Float, nullable=False)
    features = Column(JSON)  # List of features included in the plan
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")


class Subscription(Base):
    """User subscriptions."""
    __tablename__ = 'subscriptions'
    __table_args__ = (
        Index('ix_subscriptions_user', 'user_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey(
        "subscription_plans.id"), nullable=False)
    status = Column(String(50), nullable=False, default='active')
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship("Payment", back_populates="subscription")


class Payment(Base):
    """Payment history for subscriptions."""
    __tablename__ = 'payments'
    __table_args__ = (
        Index('ix_payments_subscription', 'subscription_id'),
        {'extend_existing': True}
    )

    id = Column(Integer, primary_key=True)
    subscription_id = Column(Integer, ForeignKey(
        "subscriptions.id"), nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))
    payment_date = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False, default='completed')
    transaction_id = Column(String(100), unique=True)

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")
