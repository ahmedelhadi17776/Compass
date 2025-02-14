from sqlalchemy import Column, Integer, String, Numeric, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from data_layer.database.models.base import Base
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
    user = relationship("User")
    plan = relationship("SubscriptionPlan", back_populates="subscriptions")
    payments = relationship(
        "Payment", back_populates="subscription", cascade="all, delete-orphan")


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
