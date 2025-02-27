from crewai import Agent
from Backend.agents.task_agents.task_management_agent import TaskManagementAgent
from Backend.agents.task_agents.task_analysis_agent import TaskAnalysisAgent
import sys
import os
from pathlib import Path

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Backend directory
sys.path.insert(0, str(project_root.parent))  # COMPASS directory

# Set a mock OpenAI API key for testing
os.environ["OPENAI_API_KEY"] = "sk-mock-key-for-testing-purposes-only"

# Now import the modules


def test_task_analysis_agent_initialization():
    """Test that TaskAnalysisAgent can be initialized."""
    agent = TaskAnalysisAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("TaskAnalysisAgent initialized successfully")


def test_task_management_agent_initialization():
    """Test that TaskManagementAgent can be initialized."""
    agent = TaskManagementAgent()
    assert agent is not None
    assert isinstance(agent, Agent)
    assert hasattr(agent, "ai_service")
    print("TaskManagementAgent initialized successfully")


if __name__ == "__main__":
    # Run the tests
    test_task_analysis_agent_initialization()
    test_task_management_agent_initialization()
    print("All agent initialization tests passed!")
