from Backend.orchestration.compass_task import CompassTask
from Backend.orchestration.crew_orchestrator import CrewOrchestrator
from langchain.tools import Tool
from crewai import Agent, Task, Crew
import asyncio
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))


# Now import the modules


@pytest.mark.asyncio
async def test_crew_orchestrator_initialization():
    """Test that the CrewOrchestrator can be initialized."""
    orchestrator = CrewOrchestrator()
    assert orchestrator is not None
    assert orchestrator.task_analyzer is not None
    assert orchestrator.task_manager is not None
    assert orchestrator.workflow_optimizer is not None
    assert orchestrator.productivity_agent is not None
    assert orchestrator.collaboration_agent is not None
    assert orchestrator.resource_agent is not None


@pytest.mark.asyncio
async def test_compass_task_creation():
    """Test that CompassTask can be created and inherits from Task."""
    # Create a simple agent for testing
    agent = Agent(
        role="Test Agent",
        goal="Test the CompassTask",
        backstory="I am a test agent",
        verbose=True
    )

    # Create a CompassTask
    task = CompassTask(
        description="Test task",
        agent=agent,
        expected_output="Test output",
        task_data={"test_key": "test_value"},
        task_type="test"
    )

    # Verify it's a Task instance
    assert isinstance(task, Task)
    assert task.description == "Test task"
    assert task.expected_output == "Test output"
    assert task.get_task_data() == {"test_key": "test_value"}
    assert task.get_task_type() == "test"


@pytest.mark.asyncio
async def test_crew_with_compass_tasks():
    """Test that a Crew can be created with CompassTasks."""
    # Create a simple agent for testing
    agent = Agent(
        role="Test Agent",
        goal="Test the CompassTask",
        backstory="I am a test agent",
        verbose=True
    )

    # Create a CompassTask
    task = CompassTask(
        description="Test task",
        agent=agent,
        expected_output="Test output",
        task_data={"test_key": "test_value"},
        task_type="test"
    )

    # Create a Crew with the task
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True
    )

    assert crew is not None


if __name__ == "__main__":
    # Run the tests
    asyncio.run(test_crew_orchestrator_initialization())
    asyncio.run(test_compass_task_creation())
    asyncio.run(test_crew_with_compass_tasks())
    print("All tests passed!")
