package todos

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// TodoPriority represents the priority level of a todo
type TodoPriority string

const (
	PriorityHigh   TodoPriority = "high"
	PriorityMedium TodoPriority = "medium"
	PriorityLow    TodoPriority = "low"
)

// Scan implements the sql.Scanner interface
func (p *TodoPriority) Scan(value interface{}) error {
	str, ok := value.(string)
	if !ok {
		return errors.New("invalid data for TodoPriority")
	}
	*p = TodoPriority(str)
	return nil
}

// Value implements the driver.Valuer interface
func (p TodoPriority) Value() (driver.Value, error) {
	return string(p), nil
}

// TodoStatus represents the status of a todo
type TodoStatus string

const (
	StatusPending    TodoStatus = "pending"
	StatusInProgress TodoStatus = "in_progress"
	StatusCompleted  TodoStatus = "completed"
	StatusArchived   TodoStatus = "archived"
)

// Scan implements the sql.Scanner interface
func (s *TodoStatus) Scan(value interface{}) error {
	str, ok := value.(string)
	if !ok {
		return errors.New("invalid data for TodoStatus")
	}
	*s = TodoStatus(str)
	return nil
}

// Value implements the driver.Valuer interface
func (s TodoStatus) Value() (driver.Value, error) {
	return string(s), nil
}

// JSON type for storing JSON data
type JSON json.RawMessage

// Scan implements the sql.Scanner interface
func (j *JSON) Scan(value interface{}) error {
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("invalid data for JSON")
	}
	*j = bytes
	return nil
}

// Value implements the driver.Valuer interface
func (j JSON) Value() (driver.Value, error) {
	if len(j) == 0 {
		return nil, nil
	}
	return json.RawMessage(j), nil
}

// Todo represents a todo item in the system
type Todo struct {
	ID                    uuid.UUID    `gorm:"type:uuid;primary_key;default:uuid_generate_v4()"`
	UserID                uuid.UUID    `gorm:"type:uuid;not null;index"`
	Title                 string       `gorm:"size:255;not null"`
	Description           string       `gorm:"type:text"`
	Status                TodoStatus   `gorm:"type:varchar(20);not null;default:'pending';index"`
	Priority              TodoPriority `gorm:"type:varchar(20);not null;default:'medium';index"`
	DueDate               *time.Time   `gorm:"index"`
	ReminderTime          *time.Time
	IsRecurring           bool       `gorm:"default:false;not null"`
	RecurrencePattern     JSON       `gorm:"type:jsonb"`
	Tags                  JSON       `gorm:"type:jsonb"`
	Checklist             JSON       `gorm:"type:jsonb"`
	LinkedTaskID          *uuid.UUID `gorm:"type:uuid"`
	LinkedCalendarEventID *uuid.UUID `gorm:"type:uuid"`
	AIGenerated           bool       `gorm:"default:false;not null"`
	AISuggestions         JSON       `gorm:"type:jsonb"`
	CompletionDate        *time.Time
	CreatedAt             time.Time `gorm:"not null;default:current_timestamp;index"`
	UpdatedAt             time.Time `gorm:"not null;default:current_timestamp;autoUpdateTime"`
}

// CreateTodoInput represents the input for creating a new todo
type CreateTodoInput struct {
	Title                 string       `json:"title"`
	Description           string       `json:"description"`
	StartDay              time.Time    `json:"start_day"`
	EndDay                *time.Time   `json:"end_day"`
	UserID                uuid.UUID    `json:"user_id"`
	Priority              TodoPriority `json:"priority"`
	DueDate               *time.Time   `json:"due_date"`
	ReminderTime          *time.Time   `json:"reminder_time"`
	IsRecurring           bool         `json:"is_recurring"`
	RecurrencePattern     JSON         `json:"recurrence_pattern"`
	Tags                  JSON         `json:"tags"`
	Checklist             JSON         `json:"checklist"`
	LinkedTaskID          *uuid.UUID   `json:"linked_task_id"`
	LinkedCalendarEventID *uuid.UUID   `json:"linked_calendar_event_id"`
}

// UpdateTodoInput represents the input for updating a todo
type UpdateTodoInput struct {
	Title                 *string       `json:"title,omitempty"`
	Description           *string       `json:"description,omitempty"`
	StartDay              *time.Time    `json:"start_day,omitempty"`
	EndDay                *time.Time    `json:"end_day,omitempty"`
	Priority              *TodoPriority `json:"priority,omitempty"`
	DueDate               *time.Time    `json:"due_date,omitempty"`
	ReminderTime          *time.Time    `json:"reminder_time,omitempty"`
	IsRecurring           *bool         `json:"is_recurring,omitempty"`
	RecurrencePattern     *JSON         `json:"recurrence_pattern,omitempty"`
	Tags                  *JSON         `json:"tags,omitempty"`
	Checklist             *JSON         `json:"checklist,omitempty"`
	LinkedTaskID          *uuid.UUID    `json:"linked_task_id,omitempty"`
	LinkedCalendarEventID *uuid.UUID    `json:"linked_calendar_event_id,omitempty"`
}

// TodoResponse represents the response body for a todo
type TodoResponse struct {
	Todo Todo `json:"todo"`
}

// TodoListResponse represents the response body for a list of todos
type TodoListResponse struct {
	Todos []Todo `json:"todos"`
}

func (Todo) TableName() string {
	return "todos"
}

// BeforeCreate is called before creating a new todo record
func (t *Todo) BeforeCreate(tx *gorm.DB) error {
	if t.ID == uuid.Nil {
		t.ID = uuid.New()
	}

	// Set default values if not provided
	if t.Status == "" {
		t.Status = StatusPending
	}
	if t.Priority == "" {
		t.Priority = PriorityMedium
	}

	t.CreatedAt = time.Now()
	t.UpdatedAt = time.Now()
	return nil
}

// BeforeUpdate is called before updating a todo record
func (t *Todo) BeforeUpdate(tx *gorm.DB) error {
	t.UpdatedAt = time.Now()

	// If status is changed to completed and completion date is not set
	if t.Status == StatusCompleted && t.CompletionDate == nil {
		now := time.Now()
		t.CompletionDate = &now
	}

	return nil
}
