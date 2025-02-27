from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.agents.base.base_agent import BaseAgent
from Backend.agents.resource_agents.resource_allocation_agent import ResourceAllocationAgent
from Backend.agents.collaboration_agents.collaboration_agent import CollaborationAgent
from Backend.agents.productivity_agents.productivity_agent import ProductivityAgent
from Backend.agents.workflow_agents.workflow_optimization_agent import WorkflowOptimizationAgent
from Backend.agents.task_agents.task_management_agent import TaskManagementAgent
from Backend.agents.task_agents.task_analysis_agent import TaskAnalysisAgent
import sys
import os
from pathlib import Path
import asyncio
import pytest
from crewai import Agent

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Backend directory
sys.path.insert(0, str(project_root.parent))  # COMPASS directory

# Set a mock OpenAI API key for testing
os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-testing-purposes-only"

# Import all agent classes after setting up the path


@pytest.mark.asyncio
async def test_task_analysis_agent():
    """Test that TaskAnalysisAgent can be initialized."""
    agent = TaskAnalysisAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("TaskAnalysisAgent initialized successfully")


@pytest.mark.asyncio
async def test_task_management_agent():
    """Test that TaskManagementAgent can be initialized."""
    agent = TaskManagementAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("TaskManagementAgent initialized successfully")


@pytest.mark.asyncio
async def test_workflow_optimization_agent():
    """Test that WorkflowOptimizationAgent can be initialized."""
    agent = WorkflowOptimizationAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("WorkflowOptimizationAgent initialized successfully")


@pytest.mark.asyncio
async def test_productivity_agent():
    """Test that ProductivityAgent can be initialized."""
    agent = ProductivityAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("ProductivityAgent initialized successfully")


@pytest.mark.asyncio
async def test_collaboration_agent():
    """Test that CollaborationAgent can be initialized."""
    agent = CollaborationAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("CollaborationAgent initialized successfully")


@pytest.mark.asyncio
async def test_resource_allocation_agent():
    """Test that ResourceAllocationAgent can be initialized."""
    agent = ResourceAllocationAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("ResourceAllocationAgent initialized successfully")


@pytest.mark.asyncio
async def test_base_agent():
    """Test that BaseAgent can be initialized."""
    # Create a simple AIServiceBase instance for testing
    class TestAIService(AIServiceBase):
        def __init__(self):
            super().__init__("test")

    agent = BaseAgent(
        name="Test Agent",
        role="Test Role",
        goal="Test Goal",
        ai_service=TestAIService(),
        backstory="Test Backstory",
        verbose=True
    )
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    assert agent.name == "Test Agent"
    print("BaseAgent initialized successfully")


async def run_all_tests():
    """Run all agent tests."""
    await test_task_analysis_agent()
    await test_task_management_agent()
    await test_workflow_optimization_agent()
    await test_productivity_agent()
    await test_collaboration_agent()
    await test_resource_allocation_agent()
    await test_base_agent()


if __name__ == "__main__":
    # Run all tests
    asyncio.run(run_all_tests())
    print("All agent tests passed successfully!")
