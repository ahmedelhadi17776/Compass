package habits

import (
	"context"
	"errors"
	"time"

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
	UserID   *uuid.UUID
	Title    *string
	Page     int
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
	MarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID, completionDate *time.Time) error
	UnmarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID) error
	ResetDailyCompletions(ctx context.Context) (int64, error)
	CheckAndResetBrokenStreaks(ctx context.Context) (int64, error)
	GetTopStreaks(ctx context.Context, userID uuid.UUID, limit int) ([]Habit, error)
	GetHabitsDueToday(ctx context.Context, userID uuid.UUID) ([]Habit, error)
	FindCompletedHabits(ctx context.Context, habits *[]Habit) error
	GetActiveStreaks(ctx context.Context) ([]Habit, error)
	LogStreakHistory(ctx context.Context, habitID uuid.UUID, streakLength int, lastCompletedDate time.Time) error
	ResetStreak(ctx context.Context, habitID uuid.UUID) error
	GetStreakHistory(ctx context.Context, habitID uuid.UUID) ([]StreakHistory, error)
}

type repository struct {
	db *connection.Database
}

func NewRepository(db *connection.Database) Repository {
	return &repository{db: db}
}

func (r *repository) Create(ctx context.Context, habit *Habit) error {
	return r.db.WithContext(ctx).Create(habit).Error
}

func (r *repository) FindByID(ctx context.Context, id uuid.UUID) (*Habit, error) {
	var habit Habit
	result := r.db.WithContext(ctx).First(&habit, id)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrHabitNotFound
		}
		return nil, result.Error
	}
	return &habit, nil
}

func (r *repository) FindAll(ctx context.Context, filter HabitFilter) ([]Habit, int64, error) {
	var habits []Habit
	var total int64
	query := r.db.WithContext(ctx).Model(&Habit{})

	if filter.UserID != nil {
		query = query.Where("user_id = ?", filter.UserID)
	}

	if filter.Title != nil {
		query = query.Where("title LIKE ?", "%"+*filter.Title+"%")
	}

	err := query.Count(&total).Error
	if err != nil {
		return nil, 0, err
	}

	err = query.Offset(filter.Page * filter.PageSize).
		Limit(filter.PageSize).
		Find(&habits).Error
	if err != nil {
		return nil, 0, err
	}

	return habits, total, nil
}

func (r *repository) Update(ctx context.Context, habit *Habit) error {
	result := r.db.WithContext(ctx).Save(habit)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrHabitNotFound
	}
	return nil
}

func (r *repository) Delete(ctx context.Context, id uuid.UUID) error {
	result := r.db.WithContext(ctx).Delete(&Habit{}, id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrHabitNotFound
	}
	return nil
}

func (r *repository) FindByTitle(ctx context.Context, title string, userID uuid.UUID) (*Habit, error) {
	var habit Habit
	result := r.db.WithContext(ctx).
		Where("title = ? AND user_id = ?", title, userID).
		First(&habit)
	if result.Error != nil {
		if errors.Is(result.Error, gorm.ErrRecordNotFound) {
			return nil, ErrHabitNotFound
		}
		return nil, result.Error
	}
	return &habit, nil
}

func (r *repository) MarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID, completionDate *time.Time) error {
	now := time.Now()
	if completionDate == nil {
		completionDate = &now
	}

	result := r.db.WithContext(ctx).Model(&Habit{}).
		Where("id = ? AND user_id = ?", id, userID).
		Updates(map[string]interface{}{
			"is_completed":        true,
			"last_completed_date": completionDate,
			"current_streak":      gorm.Expr("current_streak + 1"),
			"longest_streak":      gorm.Expr("GREATEST(longest_streak, current_streak + 1)"),
		})

	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrHabitNotFound
	}
	return nil
}

func (r *repository) UnmarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID) error {
	result := r.db.WithContext(ctx).Model(&Habit{}).
		Where("id = ? AND user_id = ?", id, userID).
		Updates(map[string]interface{}{
			"is_completed":   false,
			"current_streak": gorm.Expr("current_streak - 1"),
		})

	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrHabitNotFound
	}
	return nil
}

func (r *repository) ResetDailyCompletions(ctx context.Context) (int64, error) {
	result := r.db.WithContext(ctx).Model(&Habit{}).
		Where("is_completed = ?", true).
		Update("is_completed", false)

	return result.RowsAffected, result.Error
}

func (r *repository) CheckAndResetBrokenStreaks(ctx context.Context) (int64, error) {
	yesterday := time.Now().AddDate(0, 0, -1)

	result := r.db.WithContext(ctx).Model(&Habit{}).
		Where("current_streak > 0 AND (last_completed_date IS NULL OR last_completed_date < ?)", yesterday).
		Updates(map[string]interface{}{
			"current_streak": 0,
		})

	return result.RowsAffected, result.Error
}

func (r *repository) GetTopStreaks(ctx context.Context, userID uuid.UUID, limit int) ([]Habit, error) {
	var habits []Habit
	err := r.db.WithContext(ctx).
		Where("user_id = ?", userID).
		Order("current_streak desc").
		Limit(limit).
		Find(&habits).Error

	return habits, err
}

func (r *repository) GetHabitsDueToday(ctx context.Context, userID uuid.UUID) ([]Habit, error) {
	var habits []Habit
	now := time.Now()
	today := time.Date(now.Year(), now.Month(), now.Day(), 0, 0, 0, 0, time.UTC)

	err := r.db.WithContext(ctx).
		Where("user_id = ? AND is_completed = ? AND start_day <= ? AND (end_day IS NULL OR end_day >= ?)",
			userID, false, today, today).
		Find(&habits).Error

	return habits, err
}

func (r *repository) FindCompletedHabits(ctx context.Context, habits *[]Habit) error {
	return r.db.WithContext(ctx).
		Where("is_completed = ?", true).
		Find(habits).Error
}

func (r *repository) GetActiveStreaks(ctx context.Context) ([]Habit, error) {
	var habits []Habit
	err := r.db.WithContext(ctx).
		Where("current_streak > 0").
		Find(&habits).Error
	return habits, err
}

func (r *repository) LogStreakHistory(ctx context.Context, habitID uuid.UUID, streakLength int, lastCompletedDate time.Time) error {
	history := StreakHistory{
		ID:            uuid.New(),
		HabitID:       habitID,
		StartDate:     lastCompletedDate.AddDate(0, 0, -streakLength+1),
		EndDate:       lastCompletedDate,
		StreakLength:  streakLength,
		CompletedDays: streakLength,
		CreatedAt:     time.Now(),
	}
	return r.db.WithContext(ctx).Create(&history).Error
}

func (r *repository) ResetStreak(ctx context.Context, habitID uuid.UUID) error {
	return r.db.WithContext(ctx).Model(&Habit{}).
		Where("id = ?", habitID).
		Updates(map[string]interface{}{
			"current_streak":    0,
			"streak_start_date": nil,
		}).Error
}

func (r *repository) GetStreakHistory(ctx context.Context, habitID uuid.UUID) ([]StreakHistory, error) {
	var history []StreakHistory
	err := r.db.WithContext(ctx).
		Where("habit_id = ?", habitID).
		Order("end_date DESC").
		Find(&history).Error
	return history, err
}
