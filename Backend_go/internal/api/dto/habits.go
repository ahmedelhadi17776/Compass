package dto

import (
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/habits"
	"github.com/google/uuid"
)

// CreateHabitRequest represents the request body for creating a new habit
// @Description Request body for creating a new habit in the system
type CreateHabitRequest struct {
	Title       string     `json:"title" binding:"required" example:"New Habit"`
	Description string     `json:"description" example:"A detailed habit description"`
	StartDay    time.Time  `json:"start_day" example:"2024-01-01T00:00:00Z"`
	EndDay      *time.Time `json:"end_day" example:"2024-01-01T00:00:00Z"`
	UserID      uuid.UUID  `json:"user_id" binding:"required"`
}

// UpdateHabitRequest represents the request body for updating an existing habit
// @Description Request body for updating habit information
type UpdateHabitRequest struct {
	Title       *string    `json:"title,omitempty" example:"Updated Habit"`
	Description *string    `json:"description,omitempty" example:"Updated habit description"`
	StartDay    *time.Time `json:"start_day,omitempty" example:"2024-01-01T00:00:00Z"`
	EndDay      *time.Time `json:"end_day,omitempty" example:"2024-01-01T00:00:00Z"`
}

// HabitResponse represents a habit in API responses
// @Description Detailed habit information returned in API responses
type HabitResponse struct {
	ID                uuid.UUID  `json:"id" example:"550e8400-e29b-41d4-a716-446655440000"`
	Title             string     `json:"title" example:"New Habit"`
	Description       string     `json:"description" example:"A detailed habit description"`
	StartDay          time.Time  `json:"start_day" example:"2024-01-01T00:00:00Z"`
	EndDay            *time.Time `json:"end_day" example:"2024-01-01T00:00:00Z"`
	CurrentStreak     int        `json:"current_streak" example:"5"`
	LongestStreak     int        `json:"longest_streak" example:"10"`
	IsCompleted       bool       `json:"is_completed" example:"false"`
	LastCompletedDate *time.Time `json:"last_completed_date" example:"2024-01-01T00:00:00Z"`
	CreatedAt         time.Time  `json:"created_at" example:"2024-01-01T00:00:00Z"`
	UpdatedAt         time.Time  `json:"updated_at" example:"2024-01-01T00:00:00Z"`
}

// HabitListResponse represents a list of habits in API responses
// @Description List of habits returned in API responses
type HabitListResponse struct {
	Habits     []HabitResponse `json:"habits"`
	TotalCount int64           `json:"total_count" example:"100"`
	Page       int             `json:"page" example:"1"`
	PageSize   int             `json:"page_size" example:"20"`
}

// StreakHistoryResponse represents a streak history in API responses
// @Description Streak history information returned in API responses
type StreakHistoryResponse struct {
	StartDate     time.Time `json:"start_date" example:"2024-01-01T00:00:00Z"`
	EndDate       time.Time `json:"end_date" example:"2024-01-01T00:00:00Z"`
	StreakLength  int       `json:"streak_length" example:"5"`
	CompletedDays int       `json:"completed_days" example:"3"`
}

// HabitStatsResponse represents habit statistics in API responses
// @Description Habit statistics information returned in API responses
type HabitStatsResponse struct {
	TotalHabits     int64 `json:"total_habits" example:"100"`
	ActiveHabits    int64 `json:"active_habits" example:"50"`
	CompletedHabits int64 `json:"completed_habits" example:"30"`
}

// Convert domain Habit to HabitResponse
func HabitToResponse(h *habits.Habit) *HabitResponse {
	return &HabitResponse{
		ID:                h.ID,
		Title:             h.Title,
		Description:       h.Description,
		StartDay:          h.StartDay,
		EndDay:            h.EndDay,
		CurrentStreak:     h.CurrentStreak,
		LongestStreak:     h.LongestStreak,
		IsCompleted:       h.IsCompleted,
		LastCompletedDate: h.LastCompletedDate,
		CreatedAt:         h.CreatedAt,
		UpdatedAt:         h.UpdatedAt,
	}
}

// Convert domain StreakHistory to StreakHistoryResponse
func StreakHistoryToResponse(sh *habits.StreakHistory) *StreakHistoryResponse {
	return &StreakHistoryResponse{
		StartDate:     sh.StartDate,
		EndDate:       sh.EndDate,
		StreakLength:  sh.StreakLength,
		CompletedDays: sh.CompletedDays,
	}
}

// Convert domain Habits to HabitResponses
func HabitsToResponse(habits []habits.Habit) []*HabitResponse {
	response := make([]*HabitResponse, len(habits))
	for i, h := range habits {
		response[i] = HabitToResponse(&h)
	}
	return response
}
