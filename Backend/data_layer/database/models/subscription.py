from sqlalchemy import Column, Integer, String, Numeric, JSON, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship
from Backend.data_layer.database.models.base import Base
import datetime


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    price = Column(Numeric(10, 2))
    features = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="plan")

    __table_args__ = (
        Index("ix_subscription_plans_name", "name", unique=True),
        Index("ix_subscription_plans_created_at", "created_at"),
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"))
    status = Column(String(50))
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship(
        "Payment", back_populates="subscription", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_subscriptions_user_id", "user_id"),
        Index("ix_subscriptions_plan_id", "plan_id"),
        Index("ix_subscriptions_status", "status"),
        Index("ix_subscriptions_expires_at", "expires_at"),
    )


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey(
        "subscriptions.id", ondelete="CASCADE"))
    amount = Column(Numeric(10, 2))
    payment_method = Column(String(50))
    payment_date = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50))
    transaction_id = Column(String(100))

    # Relationships
    subscription = relationship("Subscription", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_subscription_id", "subscription_id"),
        Index("ix_payments_payment_date", "payment_date"),
        Index("ix_payments_status", "status"),
        Index("ix_payments_transaction_id", "transaction_id", unique=True),
    )
