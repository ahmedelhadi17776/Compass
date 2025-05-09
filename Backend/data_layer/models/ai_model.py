from typing import List, Optional, Dict, Any, ClassVar
from pydantic import Field, field_validator
from data_layer.models.base_model import MongoBaseModel
from datetime import datetime
from enum import Enum


class ModelType(str, Enum):
    """Types of AI models."""
    TEXT_GENERATION = "text-generation"
    EMBEDDING = "embedding"
    CLASSIFICATION = "classification"
    SUMMARIZATION = "summarization"
    RAG = "rag"
    VISION = "vision"
    AUDIO = "audio"
    MULTIMODAL = "multimodal"


class ModelProvider(str, Enum):
    """AI model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"
    AZURE = "azure"
    AWS = "aws"
    COHERE = "cohere"


class AIModel(MongoBaseModel):
    """AI model metadata and configuration."""

    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    type: ModelType = Field(..., description="Type of model")
    provider: ModelProvider = Field(..., description="Model provider")
    status: str = Field(
        "active", description="Model status (active, inactive, deprecated)")
    capabilities: Dict[str, Any] = Field(
        default_factory=dict, description="Model capabilities")
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Model configuration")
    metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Model performance metrics")

    # Set collection name
    collection_name: ClassVar[str] = "ai_models"


class ModelUsage(MongoBaseModel):
    """Model usage statistics for tracking and billing."""

    model_id: str = Field(..., description="ID of the AI model used")
    model_name: str = Field(..., description="Name of the model")
    user_id: Optional[str] = Field(None, description="User who used the model")
    session_id: Optional[str] = Field(None, description="Session ID")
    request_type: str = Field(...,
                              description="Type of request (generation, classification, etc.)")
    tokens_in: int = Field(0, description="Number of input tokens")
    tokens_out: int = Field(0, description="Number of output tokens")
    latency_ms: int = Field(0, description="Request latency in milliseconds")
    success: bool = Field(
        True, description="Whether the request was successful")
    error: Optional[str] = Field(
        None, description="Error message if request failed")

    # Set collection name
    collection_name: ClassVar[str] = "model_usage"
