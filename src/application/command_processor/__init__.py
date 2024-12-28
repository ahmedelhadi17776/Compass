from typing import Dict, Any
from src.services.task_service.task_service import TaskService
from src.services.calendar_service.calendar_service import CalendarService
from src.services.notification_service.notification_service import NotificationService
from src.services.web_search_service.web_search_service import WebSearchService
from src.services.content_filter_service.content_filter_service import ContentFilterService
from src.services.security.security_service import SecurityService
from src.services.security.monitoring_service import SecurityMonitoringService

class CommandProcessor:
    """Processes and executes user commands based on intent."""

    def __init__(
        self,
        task_service: TaskService,
        calendar_service: CalendarService,
        notification_service: NotificationService,
        web_search_service: WebSearchService,
        content_filter_service: ContentFilterService
    ):
        self.task_service = task_service
        self.calendar_service = calendar_service
        self.notification_service = notification_service
        self.web_search_service = web_search_service
        self.content_filter_service = content_filter_service
        self.security_service = SecurityService(db=db)
        self.monitoring_service = SecurityMonitoringService(
            db=db,
            notification_service=NotificationService()
        )

    async def process_command(self, intent: str, entities: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Routes the command to the appropriate service based on intent."""
        if intent == "create_task":
            return await self.task_service.create_task_from_command(entities, user_id)
        elif intent == "schedule_meeting":
            return await self.calendar_service.schedule_meeting(entities, user_id)
        elif intent == "send_notification":
            return await self.notification_service.send_notification(entities, user_id)
        elif intent == "search_web":
            return await self.web_search_service.search(entities, user_id)
        elif intent == "filter_content":
            return await self.content_filter_service.filter_content(entities, user_id)
        else:
            return {"status": "error", "message": "Unknown intent."}
