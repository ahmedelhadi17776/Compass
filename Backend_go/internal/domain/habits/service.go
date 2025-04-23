package habits

import (
	"context"
	"errors"
	"fmt"
	"log"
	"sort"
	"time"

	"github.com/google/uuid"
)

var (
	ErrInvalidTransition = errors.New("invalid status transition")
	ErrDependencyFailed  = errors.New("dependencies not completed")
)

type Service interface {
	CreateHabit(ctx context.Context, input CreateHabitInput) (*Habit, error)
	GetHabit(ctx context.Context, id uuid.UUID) (*Habit, error)
	ListHabits(ctx context.Context, filter HabitFilter) ([]Habit, int64, error)
	UpdateHabit(ctx context.Context, id uuid.UUID, input UpdateHabitInput) (*Habit, error)
	DeleteHabit(ctx context.Context, id uuid.UUID) error
	MarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID, completionDate *time.Time) error
	UnmarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID) error
	ResetDailyCompletions(ctx context.Context) (int64, error)
	CheckAndResetBrokenStreaks(ctx context.Context) (int64, error)
	GetTopStreaks(ctx context.Context, userID uuid.UUID, limit int) ([]Habit, error)
	GetStreakHistory(ctx context.Context, id uuid.UUID) ([]StreakHistory, error)
	GetHabitsDueToday(ctx context.Context, userID uuid.UUID) ([]Habit, error)
}

type service struct {
	repo Repository
}

func NewService(repo Repository) Service {
	return &service{repo: repo}
}

func (s *service) CreateHabit(ctx context.Context, input CreateHabitInput) (*Habit, error) {
	habit := &Habit{
		ID:          uuid.New(),
		UserID:      input.UserID,
		Title:       input.Title,
		Description: input.Description,
		StartDay:    input.StartDay,
		EndDay:      input.EndDay,
	}

	err := s.repo.Create(ctx, habit)
	if err != nil {
		return nil, err
	}

	return habit, nil
}

func (s *service) GetHabit(ctx context.Context, id uuid.UUID) (*Habit, error) {
	habit, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if habit == nil {
		return nil, ErrHabitNotFound
	}
	return habit, nil
}

func (s *service) ListHabits(ctx context.Context, filter HabitFilter) ([]Habit, int64, error) {
	return s.repo.FindAll(ctx, filter)
}

func (s *service) UpdateHabit(ctx context.Context, id uuid.UUID, input UpdateHabitInput) (*Habit, error) {
	habit, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}

	if habit == nil {
		return nil, ErrHabitNotFound
	}

	if input.Title != nil {
		habit.Title = *input.Title
	}
	if input.Description != nil {
		habit.Description = *input.Description
	}
	if input.StartDay != nil {
		habit.StartDay = *input.StartDay
	}
	if input.EndDay != nil {
		habit.EndDay = input.EndDay
	}

	err = s.repo.Update(ctx, habit)
	if err != nil {
		return nil, err
	}

	return habit, nil
}

func (s *service) DeleteHabit(ctx context.Context, id uuid.UUID) error {
	habit, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if habit == nil {
		return ErrHabitNotFound
	}
	return s.repo.Delete(ctx, id)
}

func (s *service) MarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID, completionDate *time.Time) error {
	habit, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if habit == nil {
		return ErrHabitNotFound
	}

	if err := s.repo.MarkCompleted(ctx, id, userID, completionDate); err != nil {
		return err
	}

	// Update streak quality after marking completed
	if err := s.repo.UpdateStreakQuality(ctx, id); err != nil {
		log.Printf("failed to update streak quality for habit %s: %v", id, err)
	}

	return nil
}

func (s *service) UnmarkCompleted(ctx context.Context, id uuid.UUID, userID uuid.UUID) error {
	habit, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if habit == nil {
		return ErrHabitNotFound
	}

	if err := s.repo.UnmarkCompleted(ctx, id, userID); err != nil {
		return err
	}

	// Update streak quality after unmarking completed
	if err := s.repo.UpdateStreakQuality(ctx, id); err != nil {
		log.Printf("failed to update streak quality for habit %s: %v", id, err)
	}

	return nil
}

func (s *service) ResetDailyCompletions(ctx context.Context) (int64, error) {
	affected, err := s.repo.ResetDailyCompletions(ctx)
	if err != nil {
		return 0, fmt.Errorf("failed to reset daily completions: %w", err)
	}
	return affected, nil
}

func (s *service) CheckAndResetBrokenStreaks(ctx context.Context) (int64, error) {
	now := time.Now().UTC()
	yesterday := now.AddDate(0, 0, -1)

	// Get habits with active streaks
	activeStreaks, err := s.repo.GetActiveStreaks(ctx)
	if err != nil {
		return 0, fmt.Errorf("failed to fetch active streaks: %w", err)
	}

	var totalReset int64
	for _, habit := range activeStreaks {
		// Check if streak is broken
		if habit.LastCompletedDate == nil || habit.LastCompletedDate.Before(yesterday) {
			// Before resetting, store the streak history
			if err := s.repo.LogStreakHistory(ctx, habit.ID, habit.CurrentStreak, *habit.LastCompletedDate); err != nil {
				log.Printf("failed to log streak history for habit %s: %v", habit.ID, err)
			}

			// Update streak quality after logging history
			if err := s.repo.UpdateStreakQuality(ctx, habit.ID); err != nil {
				log.Printf("failed to update streak quality for habit %s: %v", habit.ID, err)
			}

			// Reset the streak
			if err := s.repo.ResetStreak(ctx, habit.ID); err != nil {
				log.Printf("failed to reset streak for habit %s: %v", habit.ID, err)
				continue
			}

			totalReset++
		}
	}

	return totalReset, nil
}

func (s *service) GetTopStreaks(ctx context.Context, userID uuid.UUID, limit int) ([]Habit, error) {
	// Get habits with additional streak metadata
	habits, err := s.repo.GetTopStreaks(ctx, userID, limit)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch top streaks: %w", err)
	}

	// Enrich habits with additional streak information
	for i := range habits {
		// Get streak history
		history, err := s.repo.GetStreakHistory(ctx, habits[i].ID)
		if err != nil {
			log.Printf("failed to fetch streak history for habit %s: %v", habits[i].ID, err)
			continue
		}

		// Calculate streak quality (consistency)
		streakQuality := calculateStreakQuality(&habits[i], history)
		habits[i].StreakQuality = streakQuality
	}

	// Sort by streak quality if available
	sort.Slice(habits, func(i, j int) bool {
		if habits[i].CurrentStreak == habits[j].CurrentStreak {
			return habits[i].StreakQuality > habits[j].StreakQuality
		}
		return habits[i].CurrentStreak > habits[j].CurrentStreak
	})

	return habits, nil
}

// Helper function to calculate streak quality
func calculateStreakQuality(habit *Habit, history []StreakHistory) float64 {
	if len(history) == 0 {
		return 0
	}

	// Sort history by start date to ensure correct calculation
	sort.Slice(history, func(i, j int) bool {
		return history[i].StartDate.Before(history[j].StartDate)
	})

	// Find earliest and latest dates
	earliest := history[0].StartDate
	latest := history[0].EndDate
	totalCompleted := 0

	for _, h := range history {
		if h.StartDate.Before(earliest) {
			earliest = h.StartDate
		}
		if h.EndDate.After(latest) {
			latest = h.EndDate
		}
		totalCompleted += h.CompletedDays
	}

	// Calculate total days in entire period
	totalDays := int(latest.Sub(earliest).Hours()/24) + 1
	if totalDays == 0 {
		return 0
	}

	quality := float64(totalCompleted) / float64(totalDays)

	// Ensure quality doesn't exceed 1.0
	if quality > 1.0 {
		quality = 1.0
	}

	return quality
}

func (s *service) GetStreakHistory(ctx context.Context, id uuid.UUID) ([]StreakHistory, error) {
	habit, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if habit == nil {
		return nil, ErrHabitNotFound
	}

	return s.repo.GetStreakHistory(ctx, id)
}

func (s *service) GetHabitsDueToday(ctx context.Context, userID uuid.UUID) ([]Habit, error) {
	return s.repo.GetHabitsDueToday(ctx, userID)
}
