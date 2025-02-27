from crewai import Task
from Backend.orchestration.compass_task import CompassTask
import sys
import os
from pathlib import Path

# Add the project root to the Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent  # Backend directory
sys.path.insert(0, str(project_root.parent))  # COMPASS directory

# Now import the modules


def test_imports():
    """Test that imports work correctly."""
    assert issubclass(CompassTask, Task)
    print("CompassTask is a subclass of Task")


if __name__ == "__main__":
    # Run the tests
    test_imports()
    print("All tests passed!")
