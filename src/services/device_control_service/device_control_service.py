"""Device control service module."""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ...data.repositories.device_control_repository import DeviceControlRepository
from ...data.database.models.device_control import DeviceControl
from core.exceptions import DeviceControlNotFoundError

class DeviceControlService:
    """Device control service class."""

    def __init__(self, session: AsyncSession):
        """Initialize device control service."""
        self._repository = DeviceControlRepository(session)

    async def create_device_control(
        self,
        user_id: int,
        device_type: str,
        device_id: str,
        action: str,
        parameters: Optional[Dict] = None
    ) -> DeviceControl:
        """Create a new device control entry."""
        # Validate device type
        valid_device_types = ["keyboard", "mouse", "display", "audio", "camera"]
        if device_type not in valid_device_types:
            raise ValueError(f"Invalid device type. Must be one of: {valid_device_types}")

        # Validate action based on device type
        valid_actions = self._get_valid_actions(device_type)
        if action not in valid_actions:
            raise ValueError(f"Invalid action for {device_type}. Must be one of: {valid_actions}")

        return await self._repository.create_device_control({
            "user_id": user_id,
            "device_type": device_type,
            "device_id": device_id,
            "action": action,
            "parameters": parameters,
            "status": "pending"
        })

    def _get_valid_actions(self, device_type: str) -> List[str]:
        """Get valid actions for a device type."""
        actions_map = {
            "keyboard": ["keypress", "keyrelease", "type", "shortcut"],
            "mouse": ["move", "click", "doubleclick", "rightclick", "scroll"],
            "display": ["brightness", "resolution", "orientation"],
            "audio": ["volume", "mute", "unmute"],
            "camera": ["capture", "start_recording", "stop_recording"]
        }
        return actions_map.get(device_type, [])

    async def get_device_control_status(
        self, control_id: int
    ) -> DeviceControl:
        """Get the status of a device control operation."""
        return await self._repository.get_device_control(control_id)

    async def update_control_status(
        self,
        control_id: int,
        status: str,
        result: Optional[Dict] = None
    ) -> DeviceControl:
        """Update the status of a device control operation."""
        valid_statuses = ["pending", "in_progress", "completed", "failed", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {valid_statuses}")

        return await self._repository.update_device_control_status(
            control_id,
            status,
            result
        )

    async def get_user_device_history(
        self,
        user_id: int,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[DeviceControl]:
        """Get device control history for a user."""
        return await self._repository.get_user_device_controls(
            user_id,
            device_type,
            status,
            limit
        )

    async def get_pending_controls(
        self, limit: int = 50
    ) -> List[DeviceControl]:
        """Get pending device control operations."""
        return await self._repository.get_pending_device_controls(limit)

    # Keyboard-specific controls
    async def create_keyboard_control(
        self,
        user_id: int,
        action: str,
        keys: List[str]
    ) -> DeviceControl:
        """Create a keyboard control operation."""
        return await self.create_device_control(
            user_id=user_id,
            device_type="keyboard",
            device_id="system_keyboard",
            action=action,
            parameters={"keys": keys}
        )

    # Mouse-specific controls
    async def create_mouse_control(
        self,
        user_id: int,
        action: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: Optional[str] = None
    ) -> DeviceControl:
        """Create a mouse control operation."""
        parameters = {}
        if x is not None and y is not None:
            parameters["position"] = {"x": x, "y": y}
        if button:
            parameters["button"] = button

        return await self.create_device_control(
            user_id=user_id,
            device_type="mouse",
            device_id="system_mouse",
            action=action,
            parameters=parameters
        )

    # Display-specific controls
    async def create_display_control(
        self,
        user_id: int,
        action: str,
        value: any
    ) -> DeviceControl:
        """Create a display control operation."""
        return await self.create_device_control(
            user_id=user_id,
            device_type="display",
            device_id="system_display",
            action=action,
            parameters={"value": value}
        )

    async def execute_device_control(
        self,
        control: DeviceControl
    ) -> bool:
        """Execute a device control operation."""
        try:
            # Update status to in_progress
            await self.update_control_status(control.id, "in_progress")

            # Execute the control based on device type and action
            success = await self._execute_control_action(control)

            # Update final status
            status = "completed" if success else "failed"
            await self.update_control_status(
                control.id,
                status,
                {"success": success}
            )

            return success
        except Exception as e:
            # Log the error and update status
            await self.update_control_status(
                control.id,
                "failed",
                {"error": str(e)}
            )
            return False

    async def _execute_control_action(self, control: DeviceControl) -> bool:
        """Execute the specific control action."""
        # This would contain the actual implementation for controlling devices
        # For now, we'll just simulate success
        return True
