from typing import Callable, Dict, Any, List
import asyncio


class EventManager:
    """Manages event registration and dispatching."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Dict[str, Any]], Any]]] = {}

    def register_listener(self, event_type: str, listener: Callable[[Dict[str, Any]], Any]) -> None:
        """Registers a listener for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    async def dispatch_event(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Dispatches an event to all registered listeners."""
        listeners = self._listeners.get(event_type, [])
        tasks = [listener(event_data) for listener in listeners]
        await asyncio.gather(*tasks)
