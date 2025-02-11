"""Test system logs repository."""
import pytest
from datetime import datetime, timedelta

from Backend.data.repositories.system_logs_repository import SystemLogsRepository
from Backend.data.database.models.system_logs import SystemLog
from core.exceptions import LogNotFoundError

@pytest.mark.asyncio
async def test_create_log(test_db):
    """Test creating a system log."""
    repository = SystemLogsRepository(test_db)
    log_data = {
        "user_id": 1,
        "event_type": "info",
        "description": "Test log entry",
        "severity": "info",
        "metadata": {"test": "data"}
    }

    log = await repository.create_log(log_data)
    assert log.user_id == log_data["user_id"]
    assert log.event_type == log_data["event_type"]
    assert log.description == log_data["description"]
    assert log.severity == log_data["severity"]
    assert log.metadata == log_data["metadata"]

@pytest.mark.asyncio
async def test_get_log(test_db):
    """Test getting a system log."""
    repository = SystemLogsRepository(test_db)
    log_data = {
        "user_id": 1,
        "event_type": "error",
        "description": "Test error",
        "severity": "error"
    }
    log = SystemLog(**log_data)
    test_db.add(log)
    await test_db.commit()
    await test_db.refresh(log)

    retrieved_log = await repository.get_log(log.id)
    assert retrieved_log.event_type == log_data["event_type"]
    assert retrieved_log.description == log_data["description"]
    assert retrieved_log.severity == log_data["severity"]

@pytest.mark.asyncio
async def test_get_log_not_found(test_db):
    """Test getting non-existent log."""
    repository = SystemLogsRepository(test_db)
    with pytest.raises(LogNotFoundError):
        await repository.get_log(999)

@pytest.mark.asyncio
async def test_get_user_logs(test_db):
    """Test getting user logs."""
    repository = SystemLogsRepository(test_db)
    user_id = 1
    logs_data = [
        {"user_id": user_id, "event_type": "info", "description": "Log 1"},
        {"user_id": user_id, "event_type": "error", "description": "Log 2"},
        {"user_id": 2, "event_type": "info", "description": "Other user log"}
    ]
    
    for log_data in logs_data:
        test_db.add(SystemLog(**log_data))
    await test_db.commit()

    user_logs = await repository.get_user_logs(user_id)
    assert len(user_logs) == 2
    assert all(log.user_id == user_id for log in user_logs)

@pytest.mark.asyncio
async def test_get_system_logs(test_db):
    """Test getting system logs with filters."""
    repository = SystemLogsRepository(test_db)
    logs_data = [
        {"event_type": "error", "severity": "high", "description": "Error 1"},
        {"event_type": "error", "severity": "low", "description": "Error 2"},
        {"event_type": "info", "severity": "low", "description": "Info 1"}
    ]
    
    for log_data in logs_data:
        test_db.add(SystemLog(**log_data))
    await test_db.commit()

    error_logs = await repository.get_system_logs(event_type="error")
    assert len(error_logs) == 2
    assert all(log.event_type == "error" for log in error_logs)

@pytest.mark.asyncio
async def test_delete_old_logs(test_db):
    """Test deleting old logs."""
    repository = SystemLogsRepository(test_db)
    now = datetime.utcnow()
    logs_data = [
        {"description": "Old log", "timestamp": now - timedelta(days=31)},
        {"description": "Recent log", "timestamp": now - timedelta(days=15)}
    ]
    
    for log_data in logs_data:
        test_db.add(SystemLog(**log_data))
    await test_db.commit()

    await repository.delete_old_logs(days=30)
    remaining_logs = await repository.get_system_logs()
    assert len(remaining_logs) == 1
    assert remaining_logs[0].description == "Recent log"

@pytest.mark.asyncio
async def test_create_error_log(test_db):
    """Test creating an error log."""
    repository = SystemLogsRepository(test_db)
    error_message = "Test error message"
    user_id = 1
    metadata = {"error_code": 500}

    log = await repository.create_error_log(error_message, user_id, metadata)
    assert log.event_type == "error"
    assert log.severity == "error"
    assert log.description == error_message
    assert log.user_id == user_id
    assert log.metadata == metadata

@pytest.mark.asyncio
async def test_create_security_log(test_db):
    """Test creating a security log."""
    repository = SystemLogsRepository(test_db)
    event_description = "Unauthorized access attempt"
    user_id = 1
    metadata = {"ip": "192.168.1.1"}

    log = await repository.create_security_log(event_description, user_id, metadata)
    assert log.event_type == "security"
    assert log.severity == "warning"
    assert log.description == event_description
    assert log.user_id == user_id
    assert log.metadata == metadata
