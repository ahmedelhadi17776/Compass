from Backend.ai_services.rag.rag_service import RAGService
from Backend.events.event_dispatcher import EventDispatcher
from Backend.events.event_registry import TASK_UPDATED, TODO_UPDATED

dispatcher = EventDispatcher()
rag_service = RAGService()

async def on_task_updated(payload):
    task_id = payload.get("task_id")
    logger.info(f"Task updated: {task_id}")
    
    # Retrieve updated task and store it in the knowledge base
    updated_task = payload.get("task_data")
    await rag_service.add_to_knowledge_base(
        content=updated_task["description"],
        metadata={"task_id": task_id, "type": "task"}
    )

dispatcher.register_listener(TASK_UPDATED, on_task_updated)
