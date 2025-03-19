import json
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.base_repository import BaseRepository

# TODO enhance template with more features
with open("Backend/core/config/domain_config.json") as f:
    DOMAIN_CONFIG = json.load(f)

REPO_MAPPING = {
    "TaskRepository": TaskRepository,
    "TodoRepository": TodoRepository,
    "BaseRepository": BaseRepository
}

# TODO: Add other services here
class AIOrc:
    def __init__(self):
        self.repo_mapping = REPO_MAPPING
        self.config = DOMAIN_CONFIG
