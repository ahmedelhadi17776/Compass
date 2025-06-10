from fastapi import WebSocket, WebSocketDisconnect, status
from typing import Dict, List, Any, Optional
import logging
import json
import asyncio
from datetime import datetime
import time
import hashlib

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
            "errors": 0,
            "reconnections": 0
        }
        # Track connection health
        self.connection_health: Dict[str, Dict[str, Any]] = {}

        # Message deduplication at WebSocket level
        # {user_id: {message_hash: timestamp}}
        self._recent_messages: Dict[str, Dict[str, float]] = {}
        self._message_dedup_window = 0.3

    async def connect(self, websocket: WebSocket, user_id: str):
        try:
            await websocket.accept()
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
            self.stats["total_connections"] += 1
            self.stats["active_connections"] = self._count_active_connections()

            # Initialize connection health tracking
            self.connection_health[user_id] = {
                "last_ping": datetime.utcnow().isoformat(),
                "last_pong": datetime.utcnow().isoformat(),
                "errors": 0,
                "reconnections": 0
            }

            logger.info(
                f"New WebSocket connection for user {user_id}. Active connections: {self.stats['active_connections']}")

            # Send last message if available (for reconnection support)
            if user_id in self.last_messages:
                try:
                    await websocket.send_json(self.last_messages[user_id])
                    logger.debug(
                        f"Sent last message to reconnected user {user_id}")
                    self.connection_health[user_id]["reconnections"] += 1
                    self.stats["reconnections"] += 1
                except Exception as e:
                    logger.error(
                        f"Failed to send last message on reconnection: {str(e)}", exc_info=True)
                    self.connection_health[user_id]["errors"] += 1
                    self.stats["errors"] += 1
        except Exception as e:
            logger.error(
                f"Error in WebSocket connection: {str(e)}", exc_info=True)
            self.stats["errors"] += 1
            raise

    async def disconnect(self, websocket: WebSocket, user_id: str):
        try:
            if user_id in self.active_connections:
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                        if user_id in self.connection_health:
                            del self.connection_health[user_id]

            self.stats["active_connections"] = self._count_active_connections()
            logger.info(
                f"WebSocket disconnected for user {user_id}. Active connections: {self.stats['active_connections']}")
        except Exception as e:
            logger.error(
                f"Error in WebSocket disconnection: {str(e)}", exc_info=True)
            self.stats["errors"] += 1

    def _count_active_connections(self) -> int:
        return sum(len(connections) for connections in self.active_connections.values())

    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            # Add timestamp if not present
            if "timestamp" not in message:
                message["timestamp"] = datetime.utcnow().isoformat()

            # For rapid user actions, reduce deduplication strictness
            message_type = message.get("type", "")
            if message_type in ["dashboard_update", "fresh_metrics"]:
                # Allow rapid updates for immediate user feedback
                should_dedupe = self._is_duplicate_message(
                    user_id, message, use_relaxed_dedup=True)
            else:
                should_dedupe = self._is_duplicate_message(user_id, message)

            if should_dedupe:
                return  # Skip this duplicate message

            # Store last message for reconnection support (except certain types)
            if message.get("type") not in ["cache_invalidate", "dashboard_update"]:
                self.last_messages[user_id] = message

            disconnected = []
            for i, connection in enumerate(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                    self.stats["messages_sent"] += 1
                    # Update last ping time
                    if user_id in self.connection_health:
                        self.connection_health[user_id]["last_ping"] = datetime.utcnow(
                        ).isoformat()
                except Exception as e:
                    logger.error(
                        f"Error broadcasting to user {user_id}: {str(e)}", exc_info=True)
                    self.stats["errors"] += 1
                    if user_id in self.connection_health:
                        self.connection_health[user_id]["errors"] += 1
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
                if user_id in self.connection_health:
                    del self.connection_health[user_id]

            logger.debug(
                f"Broadcast message to {len(self.active_connections.get(user_id, []))} connections for user {user_id}")

    def _is_duplicate_message(self, user_id: str, message: dict, use_relaxed_dedup: bool = False) -> bool:
        """Check if this message is a duplicate within the deduplication window"""
        current_time = time.time()

        # Create a hash of the message content (excluding timestamp)
        message_copy = message.copy()
        message_copy.pop('timestamp', None)  # Remove timestamp for comparison

        # For user action updates, include action context in hash for better dedup
        message_type = message.get("type", "")
        if message_type in ["dashboard_update", "fresh_metrics"]:
            # Include action details in hash to differentiate between different actions
            action_context = f"{message.get('data', {}).get('action', '')}-{message.get('data', {}).get('entity_type', '')}"
            message_copy["_action_context"] = action_context

        message_str = json.dumps(message_copy, sort_keys=True)
        message_hash = hashlib.md5(message_str.encode()).hexdigest()

        # Use relaxed deduplication for user actions (shorter window)
        dedup_window = 0.1 if use_relaxed_dedup else self._message_dedup_window

        # Clean up old messages
        if user_id in self._recent_messages:
            self._recent_messages[user_id] = {
                msg_hash: timestamp for msg_hash, timestamp in self._recent_messages[user_id].items()
                if current_time - timestamp < dedup_window
            }

        # Check if this message is a duplicate
        if user_id in self._recent_messages and message_hash in self._recent_messages[user_id]:
            last_time = self._recent_messages[user_id][message_hash]
            if current_time - last_time < dedup_window:
                logger.info(
                    f"🚫 Blocked duplicate WebSocket message for user {user_id}: {message.get('type')} (within {current_time - last_time:.3f}s)")
                return True

        # Record this message
        if user_id not in self._recent_messages:
            self._recent_messages[user_id] = {}
        self._recent_messages[user_id][message_hash] = current_time

        return False

    async def broadcast_to_all(self, message: dict):
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, message)

    async def send_ping(self):
        """Send ping to all connections to keep them alive"""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, ping_message)

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "users_connected": len(self.active_connections),
            "connections_by_user": {user_id: len(connections) for user_id, connections in self.active_connections.items()},
            "connection_health": self.connection_health
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
