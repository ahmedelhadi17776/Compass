package events

import (
	"time"

	"github.com/google/uuid"
)

// DashboardEvent represents a domain event for dashboard updates
// This struct is published to Redis for cross-service event-driven updates
type DashboardEvent struct {
	EventType string      `json:"event_type"`
	UserID    uuid.UUID   `json:"user_id"`
	EntityID  uuid.UUID   `json:"entity_id"`
	Timestamp time.Time   `json:"timestamp"`
	Details   interface{} `json:"details,omitempty"`
}
