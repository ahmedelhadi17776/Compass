package habits

import (
	"context"
	"errors"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

var (
	ErrHabitNotFound = errors.New("habit not found")
	ErrInvalidInput  = errors.New("invalid input")
)

// HabitFilter defines the filtering options for habits
type HabitFilter struct {
	UserID *uuid.UUID
	Title  *string
	Page   int
	PageSize int
}

// Repository defines the interface for habit persistence operations
type Repository interface {
	Create(ctx context.Context, habit *Habit) error
	FindByID(ctx context.Context, id uuid.UUID) (*Habit, error)
	FindAll(ctx context.Context, filter HabitFilter) ([]Habit, int64, error)
	Update(ctx context.Context, habit *Habit) error
	Delete(ctx context.Context, id uuid.UUID) error
	FindByTitle(ctx context.Context, title string, userID uuid.UUID) (*Habit, error)
}

type repository struct {
	db *connection.Database
}

func NewRepository(db *connection.Database) Repository {
	return &repository{db: db}
}



