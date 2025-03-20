import json
import os
from typing import Dict, Type, Any

from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.base_repository import BaseRepository
from Backend.orchestration.handlers.task_handler import TaskHandler
from Backend.orchestration.handlers.todo_handler import TodoHandler


def load_config(file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(os.path.dirname(
        current_dir), "core", "configs", "domain_config.json")
    with open(config_path, "r") as f:
        return json.load(f)


DOMAIN_CONFIG = load_config("domain_config.json")
LLM_CONFIG = load_config("llm_config.json")
CACHE_CONFIG = load_config("cache_config.json")
LOGGING_CONFIG = load_config("logging_config.json")

REPO_MAPPING = {
    "tasks": TaskRepository,
    "todos": TodoRepository,
    "base": BaseRepository
}

HANDLER_MAPPING = {
    "tasks": TaskHandler,
    "todos": TodoHandler
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
            self.handler_mapping = HANDLER_MAPPING
            self.domain_config = DOMAIN_CONFIG
            self.cache_config = CACHE_CONFIG
            self.llm_config = LLM_CONFIG
            self.logging_config = LOGGING_CONFIG
            self.domain_handlers = {}
            self.initialized = True

    def register_domain(self, domain: str, handler: Any) -> None:
        """Register a new domain handler."""
        self.domain_handlers[domain] = handler

    def get_repository(self, domain: str) -> Type:
        """Get repository class for a domain."""
        config = self.domain_config.get(domain, self.domain_config['default'])
        repo_name = config['repository']
        return self.repo_mapping[repo_name]

    def get_prompt_template(self, domain: str, variant: str = "default") -> str:
        """Get prompt template for a domain."""
        config = self.domain_config.get(domain, self.domain_config['default'])
        templates = config.get('prompt_templates', {})
        return templates.get(variant, templates.get("default"))

    def get_handler(self, domain: str, db_session) -> Any:
        """Get domain-specific handler if registered."""
        if domain in self.handler_mapping:
            return self.handler_mapping[domain](db_session)
        return None

    def get_domain_config(self, domain):
        return self.domain_config.get(domain, self.domain_config["default"])

    def get_llm_config(self):
        return self.llm_config

    def get_cache_config(self):
        return self.cache_config
    
    def get_rag_settings(self, domain: str):
        domain_config = self.get_domain_config(domain)
        return domain_config.get("rag_settings", {})

    def get_logging_config(self):
        return self.logging_config


ai_registry = AIRegistry()
