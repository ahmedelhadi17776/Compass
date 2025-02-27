from Backend.orchestration.compass_task import CompassTask
from crewai import Agent, Task
import sys
from pathlib import Path

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))


def test_compass_task_creation():
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


def test_compass_task_to_dict():
    """Test the to_dict method of CompassTask."""
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

    # Test to_dict method
    task_dict = task.to_dict()
    assert task_dict["description"] == "Test task"
    assert task_dict["expected_output"] == "Test output"
    assert task_dict["task_type"] == "test"
    assert task_dict["task_data"] == {"test_key": "test_value"}


def test_compass_task_update_data():
    """Test updating task data."""
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

    # Update task data
    task.update_task_data({"new_key": "new_value"})

    # Verify data was updated
    assert task.get_task_data() == {
        "test_key": "test_value", "new_key": "new_value"}


if __name__ == "__main__":
    # Run the tests
    test_compass_task_creation()
    test_compass_task_to_dict()
    test_compass_task_update_data()
    print("All tests passed!")
