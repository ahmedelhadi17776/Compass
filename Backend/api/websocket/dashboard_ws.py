from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Any, Optional
import logging
import json
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        # Store active connections by user_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store last message sent to each user for reconnection
        self.last_messages: Dict[str, Dict[str, Any]] = {}
        # Track connection stats
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "errors": 0
        }

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = self._count_active_connections()
        logger.info(
            f"New WebSocket connection for user {user_id}. Active connections: {self.stats['active_connections']}")

        # Send last message if available (for reconnection support)
        if user_id in self.last_messages:
            try:
                await websocket.send_json(self.last_messages[user_id])
                logger.debug(
                    f"Sent last message to reconnected user {user_id}")
            except Exception as e:
                logger.error(
                    f"Failed to send last message on reconnection: {str(e)}")

    async def disconnect(self, websocket: WebSocket, user_id: str):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

        self.stats["active_connections"] = self._count_active_connections()
        logger.info(
            f"WebSocket disconnected for user {user_id}. Active connections: {self.stats['active_connections']}")

    def _count_active_connections(self) -> int:
        return sum(len(connections) for connections in self.active_connections.values())

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            # Store last message for reconnection support
            self.last_messages[user_id] = message

            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            disconnected = []
            for i, connection in enumerate(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                    self.stats["messages_sent"] += 1
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to user {user_id}: {str(e)}")
                    self.stats["errors"] += 1
                    disconnected.append(i)

            # Remove disconnected connections
            for i in sorted(disconnected, reverse=True):
                try:
                    await self.active_connections[user_id][i].close()
                except:
                    pass
                del self.active_connections[user_id][i]

            # Clean up if no connections left
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

            logger.debug(
                f"Broadcast message to {len(self.active_connections.get(user_id, []))} connections for user {user_id}")

    async def broadcast_to_all(self, message: dict):
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, message)

    async def send_ping(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {"type": "ping",
                        "timestamp": datetime.utcnow().isoformat()}
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, ping_message)

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "users_connected": len(self.active_connections),
            "connections_by_user": {user_id: len(connections) for user_id, connections in self.active_connections.items()}
        }


# Create a global instance
dashboard_ws_manager = ConnectionManager()

# Start background ping task to keep connections alive


async def start_ping_task():
    while True:
        await asyncio.sleep(30)  # Send ping every 30 seconds
        try:
            await dashboard_ws_manager.send_ping()
        except Exception as e:
            logger.error(f"Error sending ping: {str(e)}")

# This will be started in the lifespan event of the FastAPI app
ping_task = None


async def start_background_tasks():
    global ping_task
    ping_task = asyncio.create_task(start_ping_task())


async def stop_background_tasks():
    global ping_task
    if ping_task:
        ping_task.cancel()
        try:
            await ping_task
        except asyncio.CancelledError:
            pass
