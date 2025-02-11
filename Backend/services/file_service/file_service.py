"""File service module."""
import os
import shutil
import hashlib
from datetime import datetime
from typing import Optional, Dict, BinaryIO
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile

from Backend.data.repositories.task_repository import TaskAttachmentsRepository # to do: change to task_repository
from Backend.core.exceptions import FileServiceError

class FileService:
    """File service class."""

    def __init__(self, session: AsyncSession, config: Dict):
        """Initialize file service."""
        self._attachments_repository = TaskAttachmentsRepository(session)
        self._base_upload_path = config["UPLOAD_PATH"]
        self._max_file_size = config["MAX_FILE_SIZE"]  # in bytes
        self._allowed_extensions = config["ALLOWED_EXTENSIONS"]

    def _create_file_path(self, user_id: int, file_name: str) -> str:
        """Create unique file path."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(f"{user_id}_{timestamp}_{file_name}".encode()).hexdigest()[:8]
        return os.path.join(
            self._base_upload_path,
            str(user_id),
            f"{timestamp}_{file_hash}_{file_name}"
        )

    def _validate_file(self, file: UploadFile, max_size: Optional[int] = None) -> None:
        """Validate file size and extension."""
        if max_size is None:
            max_size = self._max_file_size

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        size = file.file.tell()
        file.file.seek(0)  # Reset position
        
        if size > max_size:
            raise FileServiceError(f"File size exceeds maximum allowed size of {max_size} bytes")

        # Check extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self._allowed_extensions:
            raise FileServiceError(f"File extension {ext} not allowed")

    async def upload_task_attachment(
        self,
        task_id: int,
        user_id: int,
        file: UploadFile
    ) -> Dict:
        """Upload file as task attachment."""
        try:
            # Validate file
            self._validate_file(file)

            # Create directory if not exists
            user_upload_dir = os.path.join(self._base_upload_path, str(user_id))
            os.makedirs(user_upload_dir, exist_ok=True)

            # Generate unique file path
            file_path = self._create_file_path(user_id, file.filename)

            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Create attachment record
            attachment = await self._attachments_repository.create_attachment({
                "task_id": task_id,
                "file_name": file.filename,
                "file_path": file_path,
                "file_type": file.content_type,
                "file_size": os.path.getsize(file_path),
                "uploaded_by": user_id
            })

            return {
                "id": attachment.id,
                "file_name": attachment.file_name,
                "file_type": attachment.file_type,
                "file_size": attachment.file_size,
                "uploaded_at": attachment.created_at
            }

        except Exception as e:
            # Clean up file if it was created
            if "file_path" in locals() and os.path.exists(file_path):
                os.remove(file_path)
            raise FileServiceError(f"Error uploading file: {str(e)}")

    async def download_task_attachment(self, attachment_id: int) -> BinaryIO:
        """Download task attachment."""
        attachment = await self._attachments_repository.get_attachment(attachment_id)
        if not os.path.exists(attachment.file_path):
            raise FileServiceError("File not found")

        return open(attachment.file_path, "rb")

    async def delete_task_attachment(self, attachment_id: int) -> None:
        """Delete task attachment."""
        attachment = await self._attachments_repository.get_attachment(attachment_id)
        
        # Delete file
        if os.path.exists(attachment.file_path):
            os.remove(attachment.file_path)

        # Delete record
        await self._attachments_repository.delete_attachment(attachment_id)

    async def get_task_attachments(self, task_id: int) -> list:
        """Get all attachments for a task."""
        return await self._attachments_repository.get_task_attachments(task_id)

    def _get_file_metadata(self, file_path: str) -> Dict:
        """Get file metadata."""
        return {
            "size": os.path.getsize(file_path),
            "created": datetime.fromtimestamp(os.path.getctime(file_path)),
            "modified": datetime.fromtimestamp(os.path.getmtime(file_path)),
            "extension": os.path.splitext(file_path)[1].lower()
        }

    async def cleanup_orphaned_files(self) -> None:
        """Clean up files without corresponding database records."""
        for root, _, files in os.walk(self._base_upload_path):
            for file in files:
                file_path = os.path.join(root, file)
                attachment = await self._attachments_repository.get_attachment_by_path(file_path)
                if not attachment:
                    os.remove(file_path)

    async def rotate_old_files(self, days: int) -> None:
        """Archive files older than specified days."""
        archive_dir = os.path.join(self._base_upload_path, "archive")
        os.makedirs(archive_dir, exist_ok=True)

        cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        for root, _, files in os.walk(self._base_upload_path):
            if "archive" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                if os.path.getctime(file_path) < cutoff_date:
                    archive_path = os.path.join(
                        archive_dir,
                        f"{datetime.utcnow().strftime('%Y%m%d')}_{file}"
                    )
                    shutil.move(file_path, archive_path)
