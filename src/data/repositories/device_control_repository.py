"""Device control repository module."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models.device_control import DeviceControl
from core.exceptions import DeviceControlNotFoundError

class DeviceControlRepository:
    """Device control repository class."""

    def __init__(self, session: AsyncSession):
        """Initialize device control repository."""
        self._session = session

    async def create_device_control(self, control_data: dict) -> DeviceControl:
        """Create a new device control entry."""
        control = DeviceControl(
            user_id=control_data["user_id"],
            device_type=control_data["device_type"],
            device_id=control_data["device_id"],
            action=control_data["action"],
            parameters=control_data.get("parameters"),
            status=control_data.get("status", "pending"),
            timestamp=datetime.utcnow()
        )
        self._session.add(control)
        await self._session.commit()
        await self._session.refresh(control)
        return control

    async def get_device_control(self, control_id: int) -> DeviceControl:
        """Get a specific device control entry."""
        control = await self._session.execute(
            select(DeviceControl).where(DeviceControl.id == control_id)
        )
        control = control.scalar_one_or_none()
        if not control:
            raise DeviceControlNotFoundError(f"Device control with id {control_id} not found")
        return control

    async def get_user_device_controls(
        self,
        user_id: int,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[DeviceControl]:
        """Get device controls for a specific user."""
        query = select(DeviceControl).where(DeviceControl.user_id == user_id)
        
        if device_type:
            query = query.where(DeviceControl.device_type == device_type)
        if status:
            query = query.where(DeviceControl.status == status)
            
        query = query.order_by(desc(DeviceControl.timestamp)).limit(limit)
        controls = await self._session.execute(query)
        return controls.scalars().all()

    async def update_device_control_status(
        self, control_id: int, status: str, result: Optional[dict] = None
    ) -> DeviceControl:
        """Update the status of a device control entry."""
        control = await self.get_device_control(control_id)
        control.status = status
        if result:
            control.result = result
        control.updated_at = datetime.utcnow()
        await self._session.commit()
        await self._session.refresh(control)
        return control

    async def get_pending_device_controls(self, limit: int = 50) -> List[DeviceControl]:
        """Get pending device control entries."""
        query = select(DeviceControl).where(
            DeviceControl.status == "pending"
        ).order_by(DeviceControl.timestamp).limit(limit)
        controls = await self._session.execute(query)
        return controls.scalars().all()

    async def get_device_controls_by_type(
        self, device_type: str, status: Optional[str] = None, limit: int = 50
    ) -> List[DeviceControl]:
        """Get device controls by device type."""
        query = select(DeviceControl).where(DeviceControl.device_type == device_type)
        
        if status:
            query = query.where(DeviceControl.status == status)
            
        query = query.order_by(desc(DeviceControl.timestamp)).limit(limit)
        controls = await self._session.execute(query)
        return controls.scalars().all()

    async def create_keyboard_control(
        self, user_id: int, action: str, parameters: Optional[dict] = None
    ) -> DeviceControl:
        """Create a keyboard control entry."""
        return await self.create_device_control({
            "user_id": user_id,
            "device_type": "keyboard",
            "device_id": "system_keyboard",
            "action": action,
            "parameters": parameters
        })

    async def create_mouse_control(
        self, user_id: int, action: str, parameters: Optional[dict] = None
    ) -> DeviceControl:
        """Create a mouse control entry."""
        return await self.create_device_control({
            "user_id": user_id,
            "device_type": "mouse",
            "device_id": "system_mouse",
            "action": action,
            "parameters": parameters
        })
