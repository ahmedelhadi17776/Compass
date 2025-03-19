import json
import os
from typing import Dict, Type, Any
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.base_repository import BaseRepository

# TODO enhance template with more features
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "Backend", "core", "configs", "domain_config.json")

with open(config_path) as f:
    DOMAIN_CONFIG = json.load(f)

REPO_MAPPING = {
    "TaskRepository": TaskRepository,
    "TodoRepository": TodoRepository,
    "BaseRepository": BaseRepository
}

class AIRegistry:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.repo_mapping = REPO_MAPPING
            self.config = DOMAIN_CONFIG
            self.domain_handlers = {}
            self.initialized = True

    def register_domain(self, domain: str, handler: Any) -> None:
        """Register a new domain handler"""
        self.domain_handlers[domain] = handler

    def get_repository(self, domain: str) -> Type:
        """Get repository class for a domain"""
        config = self.config.get(domain, self.config['default'])
        repo_name = config['repository']
        return self.repo_mapping[repo_name]

    def get_prompt_template(self, domain: str) -> str:
        """Get prompt template for a domain"""
        config = self.config.get(domain, self.config['default'])
        return config['prompt_template']

    def get_domain_config(self, domain: str) -> Dict[str, Any]:
        """Get full configuration for a domain"""
        return self.config.get(domain, self.config['default'])

    def get_handler(self, domain: str) -> Any:
        """Get domain-specific handler if registered"""
        return self.domain_handlers.get(domain)

# Global registry instance
ai_registry = AIRegistry()
