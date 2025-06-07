from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends, HTTPException, status
from typing import Optional
import logging
import json
from datetime import datetime

from api.websocket.dashboard_ws import dashboard_ws_manager
from utils.jwt import extract_user_id_from_token, decode_token
from core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for dashboard real-time updates.
    Requires a valid JWT token as a query parameter.
    """
    user_id = None
    try:
        logger.info(
            f"Attempting WebSocket connection with token: {token[:20]}...")

        # Validate token and extract user_id
        payload = decode_token(token)
        if not payload:
            logger.error("Invalid token format or signature")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        if "user_id" not in payload:
            logger.error("Token missing user_id claim")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = payload["user_id"]
        logger.info(f"Token validated for user_id: {user_id}")

        # Accept the connection
        await dashboard_ws_manager.connect(websocket, user_id)
        logger.info(f"WebSocket connection accepted for user_id: {user_id}")

        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to dashboard updates"
        })

        # Keep the connection alive and handle client messages
        while True:
            # Wait for messages from the client
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                message_type = message.get("type")

                # Handle different message types
                if message_type == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.utcnow().isoformat()})
                elif message_type == "refresh":
                    # Client is requesting a refresh of dashboard data
                    logger.info(
                        f"Client requested dashboard refresh: {user_id}")
                    # Invalidate cache to force refresh on next API call
                    from data_layer.cache.dashboard_cache import dashboard_cache
                    await dashboard_cache.invalidate_cache(user_id)
                    await websocket.send_json({
                        "type": "refresh_initiated",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except json.JSONDecodeError:
                logger.warning(f"Received invalid JSON from client: {user_id}")
            except Exception as e:
                logger.error(f"Error handling client message: {str(e)}")

    except WebSocketDisconnect:
        if user_id:
            logger.info(f"WebSocket disconnected for user_id: {user_id}")
            await dashboard_ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        if user_id:
            await dashboard_ws_manager.disconnect(websocket, user_id)
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass


@router.websocket("/ws/dashboard/admin")
async def admin_dashboard_websocket(websocket: WebSocket, token: str = Query(...)):
    """
    Admin WebSocket endpoint for monitoring dashboard connections.
    Requires a valid JWT token with admin privileges.
    """
    try:
        # Validate token and check admin privileges
        payload = decode_token(token)
        if not payload or "user_id" not in payload or not payload.get("is_admin", False):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        user_id = payload["user_id"]

        # Accept the connection
        await websocket.accept()

        # Send initial stats
        await websocket.send_json({
            "type": "stats",
            "timestamp": datetime.utcnow().isoformat(),
            "data": dashboard_ws_manager.get_stats()
        })

        # Keep the connection alive and periodically send stats
        while True:
            # Wait for messages or timeout
            try:
                data = await websocket.receive_text()
                # If admin requests stats update
                await websocket.send_json({
                    "type": "stats",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": dashboard_ws_manager.get_stats()
                })
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"Admin WebSocket error: {str(e)}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
