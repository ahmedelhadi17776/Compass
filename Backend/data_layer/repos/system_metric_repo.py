from datetime import datetime
from data_layer.models.system_metric_model import SystemMetric
from .base_repo import BaseMongoRepository
from typing import Optional, List


class SystemMetricRepository(BaseMongoRepository[SystemMetric]):
    def __init__(self):
        super().__init__(SystemMetric)

    def find_by_user(self, user_id: str) -> List[SystemMetric]:
        return self.find_many({"user_id": user_id})

    def find_by_type_and_range(self, user_id: str, metric_type: str, start: datetime, end: datetime) -> List[SystemMetric]:
        return self.find_many({
            "user_id": user_id,
            "metric_type": metric_type,
            "timestamp": {"$gte": start, "$lte": end}
        })

    def create_metric(self, metric: SystemMetric) -> str:
        return self.insert(metric)
