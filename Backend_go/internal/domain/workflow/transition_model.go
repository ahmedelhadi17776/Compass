package workflow

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

// WorkflowTransition represents a transition between workflow steps
type WorkflowTransition struct {
	ID         uuid.UUID              `json:"id" gorm:"type:uuid;primary_key;default:uuid_generate_v4()"`
	FromStepID uuid.UUID              `json:"from_step_id" gorm:"type:uuid;not null"`
	ToStepID   uuid.UUID              `json:"to_step_id" gorm:"type:uuid;not null"`
	Conditions map[string]interface{} `json:"conditions" gorm:"type:jsonb"`
	Triggers   map[string]interface{} `json:"triggers" gorm:"type:jsonb"`
	CreatedAt  time.Time              `json:"created_at" gorm:"not null;default:current_timestamp"`
}

// CreateWorkflowTransitionRequest represents the request body for creating a workflow transition
type CreateWorkflowTransitionRequest struct {
	FromStepID uuid.UUID              `json:"from_step_id" binding:"required"`
	ToStepID   uuid.UUID              `json:"to_step_id" binding:"required"`
	Conditions map[string]interface{} `json:"conditions,omitempty"`
	Triggers   map[string]interface{} `json:"triggers,omitempty"`
}

// UpdateWorkflowTransitionRequest represents the request body for updating a workflow transition
type UpdateWorkflowTransitionRequest struct {
	Conditions map[string]interface{} `json:"conditions,omitempty"`
	Triggers   map[string]interface{} `json:"triggers,omitempty"`
}

// WorkflowTransitionResponse represents the response for transition operations
type WorkflowTransitionResponse struct {
	Transition *WorkflowTransition `json:"transition"`
}

// WorkflowTransitionListResponse represents the response for listing transitions
type WorkflowTransitionListResponse struct {
	Transitions []WorkflowTransition `json:"transitions"`
	Total       int64                `json:"total"`
}

// TableName specifies the table name for the WorkflowTransition model
func (WorkflowTransition) TableName() string {
	return "workflow_transitions"
}

// BeforeCreate is called before creating a new workflow transition record
func (t *WorkflowTransition) BeforeCreate(tx *gorm.DB) error {
	if t.ID == uuid.Nil {
		t.ID = uuid.New()
	}
	t.CreatedAt = time.Now()
	return nil
}

// WorkflowTransitionFilter represents the filter options for querying workflow transitions
type WorkflowTransitionFilter struct {
	FromStepID *uuid.UUID
	ToStepID   *uuid.UUID
	Page       int
	PageSize   int
}
