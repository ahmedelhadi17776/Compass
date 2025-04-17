package dto

import (
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/google/uuid"
)

type CreateTaskRequest struct {
	Title          string            `json:"title" binding:"required"`
	Description    string            `json:"description"`
	Status         task.TaskStatus   `json:"status"`
	Priority       task.TaskPriority `json:"priority"`
	AssigneeID     *uuid.UUID        `json:"assignee_id,omitempty"`
	ReviewerID     *uuid.UUID        `json:"reviewer_id,omitempty"`
	CategoryID     *uuid.UUID        `json:"category_id,omitempty"`
	ParentTaskID   *uuid.UUID        `json:"parent_task_id,omitempty"`
	ProjectID      uuid.UUID         `json:"project_id" binding:"required"`
	OrganizationID uuid.UUID         `json:"organization_id" binding:"required"`
	EstimatedHours float64           `json:"estimated_hours,omitempty"`
	StartDate      time.Time         `json:"start_date" binding:"required"`
	Duration       *float64          `json:"duration,omitempty"`
	DueDate        *time.Time        `json:"due_date,omitempty"`
	Dependencies   []uuid.UUID       `json:"dependencies,omitempty"`
}

type UpdateTaskRequest struct {
	Title          *string            `json:"title,omitempty"`
	Description    *string            `json:"description,omitempty"`
	Status         *task.TaskStatus   `json:"status,omitempty"`
	Priority       *task.TaskPriority `json:"priority,omitempty"`
	AssigneeID     *uuid.UUID         `json:"assignee_id,omitempty"`
	ReviewerID     *uuid.UUID         `json:"reviewer_id,omitempty"`
	CategoryID     *uuid.UUID         `json:"category_id,omitempty"`
	EstimatedHours *float64           `json:"estimated_hours,omitempty"`
	StartDate      *time.Time         `json:"start_date,omitempty"`
	Duration       *float64           `json:"duration,omitempty"`
	DueDate        *time.Time         `json:"due_date,omitempty"`
	Dependencies   []uuid.UUID        `json:"dependencies,omitempty"`
}

type TaskResponse struct {
	ID              uuid.UUID              `json:"id"`
	Title           string                 `json:"title"`
	Description     string                 `json:"description"`
	Status          task.TaskStatus        `json:"status"`
	Priority        task.TaskPriority      `json:"priority"`
	CreatedAt       time.Time              `json:"created_at"`
	UpdatedAt       time.Time              `json:"updated_at"`
	CreatorID       uuid.UUID              `json:"creator_id"`
	AssigneeID      *uuid.UUID             `json:"assignee_id,omitempty"`
	ReviewerID      *uuid.UUID             `json:"reviewer_id,omitempty"`
	CategoryID      *uuid.UUID             `json:"category_id,omitempty"`
	ParentTaskID    *uuid.UUID             `json:"parent_task_id,omitempty"`
	ProjectID       uuid.UUID              `json:"project_id"`
	OrganizationID  uuid.UUID              `json:"organization_id"`
	EstimatedHours  float64                `json:"estimated_hours,omitempty"`
	ActualHours     float64                `json:"actual_hours,omitempty"`
	StartDate       time.Time              `json:"start_date"`
	Duration        *float64               `json:"duration,omitempty"`
	DueDate         *time.Time             `json:"due_date,omitempty"`
	Dependencies    []uuid.UUID            `json:"dependencies,omitempty"`
	HealthScore     *float64               `json:"health_score,omitempty"`
	ComplexityScore *float64               `json:"complexity_score,omitempty"`
	ProgressMetrics map[string]interface{} `json:"progress_metrics,omitempty"`
	Blockers        []string               `json:"blockers,omitempty"`
	RiskFactors     map[string]interface{} `json:"risk_factors,omitempty"`
}

type TaskListResponse struct {
	Tasks      []TaskResponse `json:"tasks"`
	TotalCount int64          `json:"total_count"`
	Page       int            `json:"page"`
	PageSize   int            `json:"page_size"`
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
