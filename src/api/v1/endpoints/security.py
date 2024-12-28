"""Security API endpoints."""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from src.core.security import SecurityContext
from src.services.security.monitoring_service import SecurityMonitoringService
from src.services.security.alerts_service import SecurityAlertsService
from src.services.notification_service.notification_service import NotificationService
from src.services.authentication.dependencies import get_security_context
from src.data.database.session import get_db
from src.core.security.events import SecurityEventType
from src.services.security.metrics_service import SecurityMetricsService
from src.core.security.exceptions import SecurityError, AccessDeniedError

router = APIRouter()


@router.get("/monitoring/trends")
async def get_security_trends(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> Dict[str, Any]:
    """Get security monitoring trends."""
    monitoring_service = SecurityMonitoringService(
        db=db,
        notification_service=NotificationService(),
        background_tasks=None  # Not needed for trend analysis
    )

    return await monitoring_service.analyze_security_trends(days=days)


@router.post("/alerts/test")
async def test_security_alert(
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> Dict[str, str]:
    """Test security alert system."""
    alerts_service = SecurityAlertsService(
        db=db,
        notification_service=NotificationService()
    )

    await alerts_service.process_security_event(
        event_type="test_alert",
        details={
            "description": "Test security alert",
            "test": True
        },
        severity="info"
    )

    return {"status": "Alert sent successfully"}


@router.get("/monitoring/active-threats")
async def get_active_threats(
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> Dict[str, Any]:
    """Get currently active security threats."""
    monitoring_service = SecurityMonitoringService(
        db=db,
        notification_service=NotificationService(),
        background_tasks=None
    )

    # Get recent suspicious activities
    since = datetime.utcnow() - timedelta(hours=1)
    events = await monitoring_service.repository.get_security_events(
        start_date=since,
        event_types=[SecurityEventType.SUSPICIOUS_ACTIVITY]
    )

    return {
        "active_threats": len(events),
        "threats": [
            {
                "type": event["event_type"],
                "severity": event["severity"],
                "description": event["description"],
                "timestamp": event["timestamp"],
                "details": event["metadata"]
            }
            for event in events
        ]
    }


@router.get("/monitoring/metrics")
async def get_security_metrics(
    timeframe: str = "24h",
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> Dict[str, Any]:
    """Get security metrics for specified timeframe."""
    metrics_service = SecurityMetricsService(db)
    return await metrics_service.get_metrics(timeframe)


@router.get("/audit/events")
async def get_audit_events(
    start_date: datetime,
    end_date: datetime = None,
    event_type: str = None,
    user_id: int = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> Dict[str, Any]:
    """Get audit events with filtering."""
    monitoring_service = SecurityMonitoringService(
        db=db,
        notification_service=NotificationService(),
        background_tasks=None
    )

    events = await monitoring_service.repository.get_audit_logs(
        start_date=start_date,
        end_date=end_date or datetime.utcnow(),
        event_type=event_type,
        user_id=user_id,
        limit=limit
    )

    return {
        "total": len(events),
        "events": [event.to_dict() for event in events]
    }


@router.post("/alerts/configure")
async def configure_alerts(
    config: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    security_context: SecurityContext = Depends(get_security_context)
) -> Dict[str, str]:
    """Configure security alert settings."""
    alerts_service = SecurityAlertsService(
        db=db,
        notification_service=NotificationService()
    )
    # Update alert configuration
    await alerts_service.update_alert_config(config)

    return {"status": "Alert configuration updated"}
