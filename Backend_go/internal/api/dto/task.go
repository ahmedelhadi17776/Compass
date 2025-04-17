package dto

import (
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/google/uuid"
)

// CreateTaskRequest represents the request body for creating a new task
// @Description Request body for creating a new task in the system
type CreateTaskRequest struct {
	Title          string            `json:"title" binding:"required" example:"Implement user authentication"`
	Description    string            `json:"description" example:"Add JWT-based authentication with role-based access control"`
	Status         task.TaskStatus   `json:"status" example:"Upcoming"`
	Priority       task.TaskPriority `json:"priority" example:"High"`
	AssigneeID     *uuid.UUID        `json:"assignee_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440000"`
	ReviewerID     *uuid.UUID        `json:"reviewer_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440001"`
	CategoryID     *uuid.UUID        `json:"category_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440002"`
	ParentTaskID   *uuid.UUID        `json:"parent_task_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440003"`
	ProjectID      uuid.UUID         `json:"project_id" binding:"required" example:"550e8400-e29b-41d4-a716-446655440004"`
	OrganizationID uuid.UUID         `json:"organization_id" binding:"required" example:"550e8400-e29b-41d4-a716-446655440005"`
	EstimatedHours float64           `json:"estimated_hours,omitempty" example:"8.5"`
	StartDate      time.Time         `json:"start_date" binding:"required" example:"2024-03-15T09:00:00Z"`
	Duration       *float64          `json:"duration,omitempty" example:"16.5"`
	DueDate        *time.Time        `json:"due_date,omitempty" example:"2024-03-20T17:00:00Z"`
	Dependencies   []uuid.UUID       `json:"dependencies,omitempty" example:"['550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440007']"`
}

// UpdateTaskRequest represents the request body for updating an existing task
// @Description Request body for updating task information
type UpdateTaskRequest struct {
	Title          *string            `json:"title,omitempty" example:"Updated: Implement user authentication"`
	Description    *string            `json:"description,omitempty" example:"Updated implementation details for JWT authentication"`
	Status         *task.TaskStatus   `json:"status,omitempty" example:"In Progress"`
	Priority       *task.TaskPriority `json:"priority,omitempty" example:"Urgent"`
	AssigneeID     *uuid.UUID         `json:"assignee_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440000"`
	ReviewerID     *uuid.UUID         `json:"reviewer_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440001"`
	CategoryID     *uuid.UUID         `json:"category_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440002"`
	EstimatedHours *float64           `json:"estimated_hours,omitempty" example:"12.5"`
	StartDate      *time.Time         `json:"start_date,omitempty" example:"2024-03-16T09:00:00Z"`
	Duration       *float64           `json:"duration,omitempty" example:"24"`
	DueDate        *time.Time         `json:"due_date,omitempty" example:"2024-03-22T17:00:00Z"`
	Dependencies   []uuid.UUID        `json:"dependencies,omitempty" example:"['550e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440007']"`
}

// TaskResponse represents a task in API responses
// @Description Detailed task information returned in API responses
type TaskResponse struct {
	ID              uuid.UUID              `json:"id" example:"550e8400-e29b-41d4-a716-446655440000"`
	Title           string                 `json:"title" example:"Implement user authentication"`
	Description     string                 `json:"description" example:"Add JWT-based authentication with role-based access control"`
	Status          task.TaskStatus        `json:"status" example:"In Progress"`
	Priority        task.TaskPriority      `json:"priority" example:"High"`
	CreatedAt       time.Time              `json:"created_at" example:"2024-03-15T09:00:00Z"`
	UpdatedAt       time.Time              `json:"updated_at" example:"2024-03-15T10:30:00Z"`
	CreatorID       uuid.UUID              `json:"creator_id" example:"550e8400-e29b-41d4-a716-446655440001"`
	AssigneeID      *uuid.UUID             `json:"assignee_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440002"`
	ReviewerID      *uuid.UUID             `json:"reviewer_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440003"`
	CategoryID      *uuid.UUID             `json:"category_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440004"`
	ParentTaskID    *uuid.UUID             `json:"parent_task_id,omitempty" example:"550e8400-e29b-41d4-a716-446655440005"`
	ProjectID       uuid.UUID              `json:"project_id" example:"550e8400-e29b-41d4-a716-446655440006"`
	OrganizationID  uuid.UUID              `json:"organization_id" example:"550e8400-e29b-41d4-a716-446655440007"`
	EstimatedHours  float64                `json:"estimated_hours,omitempty" example:"8.5"`
	ActualHours     float64                `json:"actual_hours,omitempty" example:"6.5"`
	StartDate       time.Time              `json:"start_date" example:"2024-03-15T09:00:00Z"`
	Duration        *float64               `json:"duration,omitempty" example:"16.5"`
	DueDate         *time.Time             `json:"due_date,omitempty" example:"2024-03-20T17:00:00Z"`
	Dependencies    []uuid.UUID            `json:"dependencies,omitempty" example:"550e8400-e29b-41d4-a716-446655440008"`
	HealthScore     *float64               `json:"health_score,omitempty" example:"0.85"`
	ComplexityScore *float64               `json:"complexity_score,omitempty" example:"1.2"`
	ProgressMetrics map[string]interface{} `json:"progress_metrics,omitempty" swaggertype:"object"`
	Blockers        []string               `json:"blockers,omitempty" example:"Waiting for API access"`
	RiskFactors     map[string]interface{} `json:"risk_factors,omitempty" swaggertype:"object"`
}

// TaskListResponse represents a paginated list of tasks
// @Description Paginated list of tasks with metadata
type TaskListResponse struct {
	Tasks      []TaskResponse `json:"tasks"`
	TotalCount int64          `json:"total_count" example:"100"`
	Page       int            `json:"page" example:"1"`
	PageSize   int            `json:"page_size" example:"20"`
}

// Convert domain Task to TaskResponse
func TaskToResponse(t *task.Task) *TaskResponse {
	return &TaskResponse{
		ID:              t.ID,
		Title:           t.Title,
		Description:     t.Description,
		Status:          t.Status,
		Priority:        t.Priority,
		CreatedAt:       t.CreatedAt,
		UpdatedAt:       t.UpdatedAt,
		CreatorID:       t.CreatorID,
		AssigneeID:      t.AssigneeID,
		ReviewerID:      t.ReviewerID,
		CategoryID:      t.CategoryID,
		ParentTaskID:    t.ParentTaskID,
		ProjectID:       t.ProjectID,
		OrganizationID:  t.OrganizationID,
		EstimatedHours:  t.EstimatedHours,
		ActualHours:     t.ActualHours,
		StartDate:       t.StartDate,
		Duration:        t.Duration,
		DueDate:         t.DueDate,
		Dependencies:    t.Dependencies,
		HealthScore:     t.HealthScore,
		ComplexityScore: t.ComplexityScore,
		ProgressMetrics: t.ProgressMetrics,
		Blockers:        t.Blockers,
		RiskFactors:     t.RiskFactors,
	}
}

func TasksToResponse(tasks []task.Task) []*TaskResponse {
	response := make([]*TaskResponse, len(tasks))
	for i, t := range tasks {
		response[i] = TaskToResponse(&t)
	}
	return response
}
