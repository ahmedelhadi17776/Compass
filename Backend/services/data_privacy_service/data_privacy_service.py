"""Data privacy service module for managing user data privacy and compliance."""
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import json

from Backend.data.repositories.user_repository import UserRepository
from Backend.data.repositories.privacy_settings_repository import PrivacySettingsRepository
from Backend.data.repositories.data_request_repository import DataRequestRepository
from Backend.core.exceptions import DataPrivacyError

class DataPrivacyService:
    """Service for managing data privacy and compliance."""

    def __init__(self, session: AsyncSession, config: Dict):
        """Initialize data privacy service."""
        self._user_repository = UserRepository(session)
        self._privacy_settings_repository = PrivacySettingsRepository(session)
        self._data_request_repository = DataRequestRepository(session)
        self._session = session
        self._config = config
        self._retention_periods = config.get("DATA_RETENTION_PERIODS", {})

    async def get_privacy_settings(self, user_id: int) -> Dict:
        """Get user's privacy settings."""
        try:
            settings = await self._privacy_settings_repository.get_settings(user_id)
            return {
                "data_collection": settings.data_collection,
                "data_sharing": settings.data_sharing,
                "marketing_communications": settings.marketing_communications,
                "analytics_tracking": settings.analytics_tracking,
                "last_updated": settings.updated_at
            }
        except Exception as e:
            raise DataPrivacyError(f"Error retrieving privacy settings: {str(e)}")

    async def update_privacy_settings(
        self,
        user_id: int,
        settings: Dict
    ) -> Dict:
        """Update user's privacy settings."""
        try:
            valid_settings = [
                "data_collection",
                "data_sharing",
                "marketing_communications",
                "analytics_tracking"
            ]
            
            # Validate settings
            invalid_settings = [k for k in settings.keys() if k not in valid_settings]
            if invalid_settings:
                raise DataPrivacyError(f"Invalid settings: {invalid_settings}")

            updated_settings = await self._privacy_settings_repository.update_settings(
                user_id,
                settings
            )

            return {
                "user_id": user_id,
                "settings": {
                    "data_collection": updated_settings.data_collection,
                    "data_sharing": updated_settings.data_sharing,
                    "marketing_communications": updated_settings.marketing_communications,
                    "analytics_tracking": updated_settings.analytics_tracking
                },
                "last_updated": updated_settings.updated_at
            }
        except Exception as e:
            raise DataPrivacyError(f"Error updating privacy settings: {str(e)}")

    async def request_data_export(
        self,
        user_id: int,
        data_types: List[str]
    ) -> Dict:
        """Request export of user's data."""
        try:
            valid_types = ["profile", "preferences", "activity", "analytics"]
            invalid_types = [t for t in data_types if t not in valid_types]
            if invalid_types:
                raise DataPrivacyError(f"Invalid data types: {invalid_types}")

            request = await self._data_request_repository.create_request({
                "user_id": user_id,
                "type": "export",
                "data_types": data_types,
                "status": "pending"
            })

            return {
                "request_id": request.id,
                "status": request.status,
                "created_at": request.created_at,
                "estimated_completion": request.created_at + self._config["EXPORT_PROCESSING_TIME"]
            }
        except Exception as e:
            raise DataPrivacyError(f"Error requesting data export: {str(e)}")

    async def request_data_deletion(
        self,
        user_id: int,
        data_types: List[str],
        reason: Optional[str] = None
    ) -> Dict:
        """Request deletion of user's data."""
        try:
            valid_types = ["profile", "preferences", "activity", "analytics"]
            invalid_types = [t for t in data_types if t not in valid_types]
            if invalid_types:
                raise DataPrivacyError(f"Invalid data types: {invalid_types}")

            request = await self._data_request_repository.create_request({
                "user_id": user_id,
                "type": "deletion",
                "data_types": data_types,
                "reason": reason,
                "status": "pending"
            })

            return {
                "request_id": request.id,
                "status": request.status,
                "created_at": request.created_at,
                "estimated_completion": request.created_at + self._config["DELETION_PROCESSING_TIME"]
            }
        except Exception as e:
            raise DataPrivacyError(f"Error requesting data deletion: {str(e)}")

    async def get_data_request_status(
        self,
        request_id: int,
        user_id: int
    ) -> Dict:
        """Get status of data request."""
        try:
            request = await self._data_request_repository.get_request(request_id)
            
            # Verify user owns this request
            if request.user_id != user_id:
                raise DataPrivacyError("Unauthorized access to data request")

            return {
                "request_id": request.id,
                "type": request.type,
                "status": request.status,
                "created_at": request.created_at,
                "completed_at": request.completed_at,
                "download_url": request.download_url if request.type == "export" else None
            }
        except Exception as e:
            raise DataPrivacyError(f"Error retrieving request status: {str(e)}")

    async def anonymize_data(
        self,
        user_id: int,
        data_type: str
    ) -> Dict:
        """Anonymize user's data while preserving functionality."""
        try:
            valid_types = ["profile", "activity", "analytics"]
            if data_type not in valid_types:
                raise DataPrivacyError(f"Invalid data type for anonymization: {data_type}")

            # Get user data
            user_data = await self._user_repository.get_user_data(user_id, data_type)

            # Anonymize sensitive fields
            anonymized_data = self._anonymize_fields(user_data)

            # Update user data
            await self._user_repository.update_user_data(user_id, data_type, anonymized_data)

            return {
                "status": "success",
                "data_type": data_type,
                "anonymized_at": datetime.utcnow()
            }
        except Exception as e:
            raise DataPrivacyError(f"Error anonymizing data: {str(e)}")

    def _anonymize_fields(self, data: Dict) -> Dict:
        """Anonymize sensitive fields in data."""
        sensitive_fields = {
            "email": self._hash_value,
            "phone": self._hash_value,
            "address": self._hash_value,
            "ip_address": self._hash_value,
            "device_id": self._hash_value
        }

        anonymized = {}
        for key, value in data.items():
            if key in sensitive_fields:
                anonymized[key] = sensitive_fields[key](value)
            elif isinstance(value, dict):
                anonymized[key] = self._anonymize_fields(value)
            elif isinstance(value, list):
                anonymized[key] = [
                    self._anonymize_fields(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                anonymized[key] = value

        return anonymized

    def _hash_value(self, value: str) -> str:
        """Hash a value for anonymization."""
        if not value:
            return value
        return hashlib.sha256(str(value).encode()).hexdigest()

    async def check_data_retention(self) -> List[Dict]:
        """Check and handle data retention policies."""
        try:
            expired_data = []
            current_time = datetime.utcnow()

            for data_type, retention_period in self._retention_periods.items():
                cutoff_date = current_time - retention_period
                expired = await self._user_repository.get_expired_data(
                    data_type,
                    cutoff_date
                )
                
                for item in expired:
                    # Archive or delete based on configuration
                    if self._config.get("ARCHIVE_EXPIRED_DATA", False):
                        await self._archive_data(item)
                    else:
                        await self._delete_data(item)
                    
                    expired_data.append({
                        "data_type": data_type,
                        "data_id": item.id,
                        "action": "archived" if self._config.get("ARCHIVE_EXPIRED_DATA") else "deleted",
                        "retention_period": str(retention_period)
                    })

            return expired_data
        except Exception as e:
            raise DataPrivacyError(f"Error checking data retention: {str(e)}")

    async def _archive_data(self, data: Dict) -> None:
        """Archive data before deletion."""
        try:
            archive_data = {
                "original_id": data.id,
                "data_type": data.type,
                "content": json.dumps(data.content),
                "archived_at": datetime.utcnow()
            }
            await self._data_request_repository.create_archive(archive_data)
        except Exception as e:
            raise DataPrivacyError(f"Error archiving data: {str(e)}")

    async def _delete_data(self, data: Dict) -> None:
        """Permanently delete data."""
        try:
            await self._user_repository.delete_data(data.id)
        except Exception as e:
            raise DataPrivacyError(f"Error deleting data: {str(e)}")

    async def generate_privacy_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """Generate privacy compliance report."""
        try:
            stats = await self._data_request_repository.get_privacy_stats(
                start_date,
                end_date
            )
            
            return {
                "period": {
                    "start": start_date,
                    "end": end_date
                },
                "data_requests": {
                    "total": stats["total_requests"],
                    "exports": stats["export_requests"],
                    "deletions": stats["deletion_requests"],
                    "completed": stats["completed_requests"],
                    "average_completion_time": stats["avg_completion_time"]
                },
                "privacy_settings": {
                    "users_opted_out": stats["opted_out_users"],
                    "marketing_consents": stats["marketing_consents"]
                },
                "data_retention": {
                    "archived_items": stats["archived_items"],
                    "deleted_items": stats["deleted_items"]
                },
                "generated_at": datetime.utcnow()
            }
        except Exception as e:
            raise DataPrivacyError(f"Error generating privacy report: {str(e)}")
