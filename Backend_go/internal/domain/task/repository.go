package task

import (
	"context"
	"errors"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

var (
	ErrTaskNotFound = errors.New("task not found")
	ErrInvalidInput = errors.New("invalid input")
)

// TaskRepository defines the interface for task persistence operations
type TaskRepository interface {
	Create(ctx context.Context, task *Task) error
	FindByID(ctx context.Context, id uuid.UUID) (*Task, error)
	FindAll(ctx context.Context, filter TaskFilter) ([]Task, int64, error)
	Update(ctx context.Context, task *Task) error
	Delete(ctx context.Context, id uuid.UUID) error
}

type taskRepository struct {
	db *connection.Database
}

func NewRepository(db *connection.Database) TaskRepository {
	return &taskRepository{db: db}
}

func (r *taskRepository) Create(ctx context.Context, task *Task) error {
	return r.db.WithContext(ctx).Create(task).Error
}

func (r *taskRepository) FindByID(ctx context.Context, id uuid.UUID) (*Task, error) {
	var task Task
	result := r.db.WithContext(ctx).First(&task, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrTaskNotFound
		}
		return nil, result.Error
	}
	return &task, nil
}

func (r *taskRepository) FindAll(ctx context.Context, filter TaskFilter) ([]Task, int64, error) {
	var tasks []Task
	var total int64

	query := r.db.WithContext(ctx)

	// Apply filters
	if filter.OrganizationID != nil {
		query = query.Where("organization_id = ?", filter.OrganizationID)
	}
	if filter.ProjectID != nil {
		query = query.Where("project_id = ?", filter.ProjectID)
	}
	if filter.Status != nil {
		query = query.Where("status = ?", filter.Status)
	}
	if filter.Priority != nil {
		query = query.Where("priority = ?", filter.Priority)
	}
	if filter.AssigneeID != nil {
		query = query.Where("assignee_id = ?", filter.AssigneeID)
	}
	if filter.CreatorID != nil {
		query = query.Where("creator_id = ?", filter.CreatorID)
	}
	if filter.ReviewerID != nil {
		query = query.Where("reviewer_id = ?", filter.ReviewerID)
	}
	if filter.StartDate != nil && filter.EndDate != nil {
		query = query.Where("created_at BETWEEN ? AND ?", filter.StartDate, filter.EndDate)
	}

	// Count total before pagination
	err := query.Model(&Task{}).Count(&total).Error
	if err != nil {
		return nil, 0, err
	}

	// Apply pagination
	query = query.Offset(filter.Page * filter.PageSize).Limit(filter.PageSize)

	// Execute query
	if err := query.Find(&tasks).Error; err != nil {
		return nil, 0, err
	}

	return tasks, total, nil
}

func (r *taskRepository) Update(ctx context.Context, task *Task) error {
	result := r.db.WithContext(ctx).Save(task)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrTaskNotFound
	}
	return nil
}

func (r *taskRepository) Delete(ctx context.Context, id uuid.UUID) error {
	result := r.db.WithContext(ctx).Delete(&Task{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrTaskNotFound
	}
	return nil
}
