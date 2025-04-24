package todos

import (
	"context"
	"time"

	"github.com/google/uuid"
)

type Service interface {
	CreateTodo(ctx context.Context, input CreateTodoInput) (*Todo, error)
	GetTodo(ctx context.Context, id uuid.UUID) (*Todo, error)
	ListTodos(ctx context.Context, filter TodoFilter) ([]Todo, int64, error)
	UpdateTodo(ctx context.Context, id uuid.UUID, input UpdateTodoInput) (*Todo, error)
	UpdateTodoStatus(ctx context.Context, id uuid.UUID, status TodoStatus) (*Todo, error)
	UpdateTodoPriority(ctx context.Context, id uuid.UUID, priority TodoPriority) (*Todo, error)
	CompleteTodo(ctx context.Context, id uuid.UUID) (*Todo, error)
	UncompleteTodo(ctx context.Context, id uuid.UUID) (*Todo, error)
	DeleteTodo(ctx context.Context, id uuid.UUID) error
	FindByUserID(ctx context.Context, userID uuid.UUID) ([]Todo, error)
	FindByListID(ctx context.Context, listID uuid.UUID) ([]Todo, error)
	FindByUserIDAndListID(ctx context.Context, userID uuid.UUID, listID uuid.UUID) ([]Todo, error)
	CreateTodoList(ctx context.Context, list *TodoList) error
	GetOrCreateDefaultList(ctx context.Context, userID uuid.UUID) (*TodoList, error)
}

type CreateTodoInput struct {
	Title                 string                 `json:"title"`
	Description           string                 `json:"description"`
	Status                TodoStatus             `json:"status"`
	Priority              TodoPriority           `json:"priority"`
	IsCompleted           bool                   `json:"is_completed"`
	DueDate               *time.Time             `json:"due_date"`
	ReminderTime          *time.Time             `json:"reminder_time"`
	IsRecurring           bool                   `json:"is_recurring"`
	RecurrencePattern     map[string]interface{} `json:"recurrence_pattern"`
	Tags                  map[string]interface{} `json:"tags"`
	Checklist             map[string]interface{} `json:"checklist"`
	LinkedTaskID          *uuid.UUID             `json:"linked_task_id"`
	LinkedCalendarEventID *uuid.UUID             `json:"linked_calendar_event_id"`
	UserID                uuid.UUID              `json:"user_id"`
	ListID                uuid.UUID              `json:"list_id"`
}

type UpdateTodoInput struct {
	Title                 *string                `json:"title,omitempty"`
	Description           *string                `json:"description,omitempty"`
	Status                *TodoStatus            `json:"status,omitempty"`
	Priority              *TodoPriority          `json:"priority,omitempty"`
	IsCompleted           *bool                  `json:"is_completed,omitempty"`
	DueDate               *time.Time             `json:"due_date,omitempty"`
	ReminderTime          *time.Time             `json:"reminder_time,omitempty"`
	IsRecurring           *bool                  `json:"is_recurring,omitempty"`
	RecurrencePattern     map[string]interface{} `json:"recurrence_pattern,omitempty"`
	Tags                  map[string]interface{} `json:"tags,omitempty"`
	Checklist             map[string]interface{} `json:"checklist,omitempty"`
	LinkedTaskID          *uuid.UUID             `json:"linked_task_id,omitempty"`
	LinkedCalendarEventID *uuid.UUID             `json:"linked_calendar_event_id,omitempty"`
}

type CreateTodoListInput struct {
	Name        string    `json:"name"`
	Description string    `json:"description"`
	UserID      uuid.UUID `json:"user_id"`
	IsDefault   bool      `json:"is_default"`
}

type UpdateTodoListInput struct {
	Name        *string `json:"name"`
	Description *string `json:"description"`
	IsDefault   *bool   `json:"is_default"`
}

type service struct {
	repo TodoRepository
}

func NewService(repo TodoRepository) Service {
	return &service{repo: repo}
}

func (s *service) CreateTodo(ctx context.Context, input CreateTodoInput) (*Todo, error) {
	if input.Title == "" {
		return nil, ErrInvalidInput
	}

	if input.Status == "" {
		input.Status = StatusPending
	}

	if input.Priority == "" {
		input.Priority = PriorityMedium
	}

	todo := &Todo{
		ID:                    uuid.New(),
		Title:                 input.Title,
		Description:           input.Description,
		Status:                input.Status,
		Priority:              input.Priority,
		DueDate:               input.DueDate,
		ReminderTime:          input.ReminderTime,
		IsRecurring:           input.IsRecurring,
		RecurrencePattern:     input.RecurrencePattern,
		Tags:                  input.Tags,
		Checklist:             input.Checklist,
		LinkedTaskID:          input.LinkedTaskID,
		LinkedCalendarEventID: input.LinkedCalendarEventID,
		UserID:                input.UserID,
		ListID:                input.ListID,
		CreatedAt:             time.Now(),
		UpdatedAt:             time.Now(),
	}

	err := s.repo.Create(ctx, todo)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

func (s *service) GetTodo(ctx context.Context, id uuid.UUID) (*Todo, error) {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if todo == nil {
		return nil, ErrTodoNotFound
	}
	return todo, nil
}

func (s *service) ListTodos(ctx context.Context, filter TodoFilter) ([]Todo, int64, error) {
	return s.repo.FindAll(ctx, filter)
}

func (s *service) UpdateTodo(ctx context.Context, id uuid.UUID, input UpdateTodoInput) (*Todo, error) {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if todo == nil {
		return nil, ErrTodoNotFound
	}

	if input.Title != nil {
		todo.Title = *input.Title
	}

	if input.Description != nil {
		todo.Description = *input.Description
	}

	if input.Status != nil {
		todo.Status = *input.Status
	}

	if input.Priority != nil {
		todo.Priority = *input.Priority
	}

	if input.DueDate != nil {
		todo.DueDate = input.DueDate
	}

	if input.ReminderTime != nil {
		todo.ReminderTime = input.ReminderTime
	}

	if input.IsRecurring != nil {
		todo.IsRecurring = *input.IsRecurring
	}

	if input.RecurrencePattern != nil {
		todo.RecurrencePattern = input.RecurrencePattern
	}

	if input.Tags != nil {
		todo.Tags = input.Tags
	}

	if input.Checklist != nil {
		todo.Checklist = input.Checklist
	}

	if input.LinkedTaskID != nil {
		todo.LinkedTaskID = input.LinkedTaskID
	}

	if input.LinkedCalendarEventID != nil {
		todo.LinkedCalendarEventID = input.LinkedCalendarEventID
	}

	err = s.repo.Update(ctx, todo)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

func (s *service) DeleteTodo(ctx context.Context, id uuid.UUID) error {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if todo == nil {
		return ErrTodoNotFound
	}
	return s.repo.Delete(ctx, id)
}

func (s *service) FindByUserID(ctx context.Context, userID uuid.UUID) ([]Todo, error) {
	return s.repo.FindByUserID(ctx, userID)
}

func (s *service) FindByListID(ctx context.Context, listID uuid.UUID) ([]Todo, error) {
	return s.repo.FindByListID(ctx, listID)
}

func (s *service) FindByUserIDAndListID(ctx context.Context, userID uuid.UUID, listID uuid.UUID) ([]Todo, error) {
	return s.repo.FindByUserIDAndListID(ctx, userID, listID)
}

func (s *service) UpdateTodoStatus(ctx context.Context, id uuid.UUID, status TodoStatus) (*Todo, error) {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if todo == nil {
		return nil, ErrTodoNotFound
	}

	todo.Status = status
	err = s.repo.Update(ctx, todo)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

func (s *service) UpdateTodoPriority(ctx context.Context, id uuid.UUID, priority TodoPriority) (*Todo, error) {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if todo == nil {
		return nil, ErrTodoNotFound
	}

	todo.Priority = priority
	err = s.repo.Update(ctx, todo)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

func (s *service) CompleteTodo(ctx context.Context, id uuid.UUID) (*Todo, error) {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if todo == nil {
		return nil, ErrTodoNotFound
	}

	todo.IsCompleted = true
	now := time.Now()
	todo.CompletionDate = &now

	err = s.repo.Update(ctx, todo)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

func (s *service) UncompleteTodo(ctx context.Context, id uuid.UUID) (*Todo, error) {
	todo, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if todo == nil {
		return nil, ErrTodoNotFound
	}

	todo.IsCompleted = false
	todo.CompletionDate = nil

	err = s.repo.Update(ctx, todo)
	if err != nil {
		return nil, err
	}

	return todo, nil
}

func (s *service) CreateTodoList(ctx context.Context, list *TodoList) error {
	if list.Name == "" {
		return ErrInvalidInput
	}
	if list.UserID == uuid.Nil {
		return ErrInvalidInput
	}

	return s.repo.CreateTodoList(ctx, list)
}

func (s *service) GetOrCreateDefaultList(ctx context.Context, userID uuid.UUID) (*TodoList, error) {
	return s.repo.GetOrCreateDefaultList(ctx, userID)
}
