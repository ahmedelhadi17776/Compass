import logging
from datetime import datetime
from typing import Dict, Any


class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)

    def log_action(self,
                   user_id: int,
                   action: str,
                   resource: str,
                   details: Dict[str, Any]):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'details': details,
        }
        self.logger.info(log_entry)
