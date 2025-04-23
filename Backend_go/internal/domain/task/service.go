package task

import (
	"context"
	"errors"
	"time"

	"github.com/google/uuid"
)

var (
	ErrInvalidTransition = errors.New("invalid status transition")
	ErrDependencyFailed  = errors.New("dependencies not completed")
)

type Service interface {
	CreateTask(ctx context.Context, input CreateTaskInput) (*Task, error)
	GetTask(ctx context.Context, id uuid.UUID) (*Task, error)
	ListTasks(ctx context.Context, filter TaskFilter) ([]Task, int64, error)
	UpdateTask(ctx context.Context, id uuid.UUID, input UpdateTaskInput) (*Task, error)
	UpdateTaskStatus(ctx context.Context, id uuid.UUID, status TaskStatus) (*Task, error)
	DeleteTask(ctx context.Context, id uuid.UUID) error
	GetTaskMetrics(ctx context.Context, id uuid.UUID) (*TaskMetrics, error)
	GetProjectTasks(ctx context.Context, projectID uuid.UUID, filter TaskFilter) ([]Task, int64, error)
	AssignTask(ctx context.Context, id uuid.UUID, assigneeID uuid.UUID) (*Task, error)
}

type TaskMetrics struct {
	HealthScore     float64                `json:"health_score"`
	ComplexityScore float64                `json:"complexity_score"`
	ProgressMetrics map[string]interface{} `json:"progress_metrics"`
	Blockers        []string               `json:"blockers"`
	RiskFactors     map[string]interface{} `json:"risk_factors"`
}

type CreateTaskInput struct {
	Title          string       `json:"title"`
	Description    string       `json:"description"`
	Status         TaskStatus   `json:"status"`
	Priority       TaskPriority `json:"priority"`
	CreatorID      uuid.UUID    `json:"creator_id"`
	AssigneeID     *uuid.UUID   `json:"assignee_id,omitempty"`
	ReviewerID     *uuid.UUID   `json:"reviewer_id,omitempty"`
	CategoryID     *uuid.UUID   `json:"category_id,omitempty"`
	ParentTaskID   *uuid.UUID   `json:"parent_task_id,omitempty"`
	ProjectID      uuid.UUID    `json:"project_id"`
	OrganizationID uuid.UUID    `json:"organization_id"`
	EstimatedHours float64      `json:"estimated_hours,omitempty"`
	StartDate      time.Time    `json:"start_date"`
	Duration       *float64     `json:"duration,omitempty"`
	DueDate        *time.Time   `json:"due_date,omitempty"`
	Dependencies   []uuid.UUID  `json:"dependencies,omitempty"`
}

type UpdateTaskInput struct {
	Title          *string       `json:"title,omitempty"`
	Description    *string       `json:"description,omitempty"`
	Status         *TaskStatus   `json:"status,omitempty"`
	Priority       *TaskPriority `json:"priority,omitempty"`
	AssigneeID     *uuid.UUID    `json:"assignee_id,omitempty"`
	ReviewerID     *uuid.UUID    `json:"reviewer_id,omitempty"`
	CategoryID     *uuid.UUID    `json:"category_id,omitempty"`
	EstimatedHours *float64      `json:"estimated_hours,omitempty"`
	StartDate      *time.Time    `json:"start_date,omitempty"`
	Duration       *float64      `json:"duration,omitempty"`
	DueDate        *time.Time    `json:"due_date,omitempty"`
	Dependencies   []uuid.UUID   `json:"dependencies,omitempty"`
}

// Repository interface

type service struct {
	repo TaskRepository
}

func NewService(repo TaskRepository) Service {
	return &service{repo: repo}
}

func (s *service) CreateTask(ctx context.Context, input CreateTaskInput) (*Task, error) {
	// Validate input
	if input.Title == "" {
		return nil, ErrInvalidInput
	}

	// Set default values
	if input.Status == "" {
		input.Status = TaskStatusUpcoming
	}
	if input.Priority == "" {
		input.Priority = TaskPriorityMedium
	}

	task := &Task{
		ID:             uuid.New(),
		Title:          input.Title,
		Description:    input.Description,
		Status:         input.Status,
		Priority:       input.Priority,
		CreatorID:      input.CreatorID,
		AssigneeID:     input.AssigneeID,
		ReviewerID:     input.ReviewerID,
		CategoryID:     input.CategoryID,
		ParentTaskID:   input.ParentTaskID,
		ProjectID:      input.ProjectID,
		OrganizationID: input.OrganizationID,
		EstimatedHours: input.EstimatedHours,
		StartDate:      input.StartDate,
		Duration:       input.Duration,
		DueDate:        input.DueDate,
		Dependencies:   input.Dependencies,
		CreatedAt:      time.Now(),
		UpdatedAt:      time.Now(),
	}

	err := s.repo.Create(ctx, task)
	if err != nil {
		return nil, err
	}

	return task, nil
}

func (s *service) GetTask(ctx context.Context, id uuid.UUID) (*Task, error) {
	task, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if task == nil {
		return nil, ErrTaskNotFound
	}
	return task, nil
}

func (s *service) ListTasks(ctx context.Context, filter TaskFilter) ([]Task, int64, error) {
	return s.repo.FindAll(ctx, filter)
}

func (s *service) UpdateTask(ctx context.Context, id uuid.UUID, input UpdateTaskInput) (*Task, error) {
	task, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if task == nil {
		return nil, ErrTaskNotFound
	}

	// Update fields if provided
	if input.Title != nil {
		task.Title = *input.Title
	}
	if input.Description != nil {
		task.Description = *input.Description
	}
	if input.Status != nil {
		if !input.Status.IsValid() {
			return nil, ErrInvalidInput
		}
		if !isValidStatusTransition(task.Status, *input.Status) {
			return nil, ErrInvalidTransition
		}
		task.Status = *input.Status
	}
	if input.Priority != nil {
		if !input.Priority.IsValid() {
			return nil, ErrInvalidInput
		}
		task.Priority = *input.Priority
	}
	if input.AssigneeID != nil {
		task.AssigneeID = input.AssigneeID
	}
	if input.ReviewerID != nil {
		task.ReviewerID = input.ReviewerID
	}
	if input.CategoryID != nil {
		task.CategoryID = input.CategoryID
	}
	if input.EstimatedHours != nil {
		task.EstimatedHours = *input.EstimatedHours
	}
	if input.StartDate != nil {
		task.StartDate = *input.StartDate
	}
	if input.Duration != nil {
		task.Duration = input.Duration
	}
	if input.DueDate != nil {
		task.DueDate = input.DueDate
	}
	if input.Dependencies != nil {
		task.Dependencies = input.Dependencies
	}

	task.UpdatedAt = time.Now()
	err = s.repo.Update(ctx, task)
	if err != nil {
		return nil, err
	}

	return task, nil
}

func (s *service) UpdateTaskStatus(ctx context.Context, id uuid.UUID, status TaskStatus) (*Task, error) {
	task, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if task == nil {
		return nil, ErrTaskNotFound
	}

	if !status.IsValid() {
		return nil, ErrInvalidInput
	}

	if !isValidStatusTransition(task.Status, status) {
		return nil, ErrInvalidTransition
	}

	// Check dependencies if moving to completed
	if status == TaskStatusCompleted {
		completed, err := s.checkDependenciesCompleted(ctx, task.Dependencies)
		if err != nil {
			return nil, err
		}
		if !completed {
			return nil, ErrDependencyFailed
		}
	}

	task.Status = status
	task.UpdatedAt = time.Now()

	err = s.repo.Update(ctx, task)
	if err != nil {
		return nil, err
	}

	return task, nil
}

func (s *service) DeleteTask(ctx context.Context, id uuid.UUID) error {
	task, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if task == nil {
		return ErrTaskNotFound
	}

	return s.repo.Delete(ctx, id)
}

func (s *service) GetTaskMetrics(ctx context.Context, id uuid.UUID) (*TaskMetrics, error) {
	task, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if task == nil {
		return nil, ErrTaskNotFound
	}

	metrics := &TaskMetrics{
		HealthScore:     calculateHealthScore(task),
		ComplexityScore: calculateComplexityScore(task),
		ProgressMetrics: task.ProgressMetrics,
		Blockers:        task.Blockers,
		RiskFactors:     task.RiskFactors,
	}

	return metrics, nil
}

func (s *service) checkDependenciesCompleted(ctx context.Context, dependencies []uuid.UUID) (bool, error) {
	for _, depID := range dependencies {
		dep, err := s.repo.FindByID(ctx, depID)
		if err != nil {
			return false, err
		}
		if dep == nil || dep.Status != TaskStatusCompleted {
			return false, nil
		}
	}
	return true, nil
}

func isValidStatusTransition(current, new TaskStatus) bool {
	transitions := map[TaskStatus][]TaskStatus{
		TaskStatusUpcoming: {
			TaskStatusInProgress,
			TaskStatusCancelled,
			TaskStatusDeferred,
			TaskStatusCompleted,
		},
		TaskStatusInProgress: {
			TaskStatusCompleted,
			TaskStatusBlocked,
			TaskStatusUnderReview,
			TaskStatusUpcoming,
		},
		TaskStatusCompleted: {
			TaskStatusUpcoming,
			TaskStatusInProgress,
		},
		TaskStatusCancelled: {
			TaskStatusUpcoming,
		},
		TaskStatusBlocked: {
			TaskStatusInProgress,
			TaskStatusUpcoming,
			TaskStatusCancelled,
		},
		TaskStatusUnderReview: {
			TaskStatusCompleted,
			TaskStatusInProgress,
		},
		TaskStatusDeferred: {
			TaskStatusUpcoming,
			TaskStatusCancelled,
		},
	}

	allowed, exists := transitions[current]
	if !exists {
		return false
	}

	for _, status := range allowed {
		if status == new {
			return true
		}
	}
	return false
}

func calculateHealthScore(task *Task) float64 {
	score := 1.0

	// Status impact
	if task.Status == TaskStatusBlocked {
		score *= 0.5
	} else if task.Status == TaskStatusDeferred {
		score *= 0.7
	}

	// Due date impact
	if task.DueDate != nil && task.DueDate.Before(time.Now()) {
		score *= 0.8
	}

	// Blockers impact
	if len(task.Blockers) > 0 {
		score *= 0.9
	}

	return score
}

func calculateComplexityScore(task *Task) float64 {
	score := 1.0

	// Base complexity from estimated hours
	if task.EstimatedHours > 0 {
		score *= (1 + task.EstimatedHours/40) // 40 hours as baseline
	}

	// Dependencies impact
	if len(task.Dependencies) > 0 {
		score *= (1 + float64(len(task.Dependencies))*0.1)
	}

	// Blockers impact
	if len(task.Blockers) > 0 {
		score *= (1 + float64(len(task.Blockers))*0.2)
	}

	return score
}

func (s *service) GetProjectTasks(ctx context.Context, projectID uuid.UUID, filter TaskFilter) ([]Task, int64, error) {
	filter.ProjectID = &projectID
	return s.repo.FindAll(ctx, filter)
}

func (s *service) AssignTask(ctx context.Context, id uuid.UUID, assigneeID uuid.UUID) (*Task, error) {
	task, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if task == nil {
		return nil, ErrTaskNotFound
	}

	task.AssigneeID = &assigneeID
	task.UpdatedAt = time.Now()

	err = s.repo.Update(ctx, task)
	if err != nil {
		return nil, err
	}

	return task, nil
}
