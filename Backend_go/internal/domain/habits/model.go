package habits

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type Habit struct {
	ID        uuid.UUID `gorm:"type:uuid;primary_key;default:uuid_generate_v4()"`
	UserID             uuid.UUID  `gorm:"type:uuid;not null"`
	Title              string     `gorm:"size:255;not null"`
	Description        string     `gorm:"type:text"`
	StartDay           time.Time  `gorm:"not null;default:current_timestamp"`
	EndDay             *time.Time `gorm:"default:null"`
	CurrentStreak      int        `gorm:"default:0;not null"`
	StreakStartDate    *time.Time `gorm:"default:null"`
	LongestStreak      int        `gorm:"default:0;not null"`
	IsCompleted        bool       `gorm:"default:false;not null"`
	LastCompletedDate  *time.Time `gorm:"default:null"`
	CreatedAt          time.Time  `gorm:"not null;default:current_timestamp"`
	UpdatedAt          time.Time  `gorm:"not null;default:current_timestamp;autoUpdateTime"`

	// Relationships
	User User `gorm:"foreignKey:UserID"`
}

// CreateHabitRequest represents the request body for creating a habit
type CreateHabitRequest struct {
	Title       string    `json:"title" binding:"required" example:"New Habit"`
	Description string    `json:"description" example:"A detailed habit description"`
	StartDay    time.Time `json:"start_day" example:"2024-01-01T00:00:00Z"`
	EndDay      *time.Time `json:"end_day" example:"2024-01-01T00:00:00Z"`
	UserID      uuid.UUID `json:"user_id" binding:"required"`
}

// UpdateHabitRequest represents the request body for updating a habit
type UpdateHabitRequest struct {
	Title       string    `json:"title" example:"Updated Habit"`
	Description string    `json:"description" example:"Updated habit description"`
	StartDay    time.Time `json:"start_day" example:"2024-01-01T00:00:00Z"`
	EndDay      *time.Time `json:"end_day" example:"2024-01-01T00:00:00Z"`
}

// HabitResponse represents the response body for a habit
type HabitResponse struct {
	Habit Habit `json:"habit"`
}

// HabitListResponse represents the response body for a list of habits
type HabitListResponse struct {
	Habits []Habit `json:"habits"`
}

// TableName specifies the table name for the Habit model
func (Habit) TableName() string {
	return "habits"
}

// BeforeCreate is called before creating a new habit record
func (h *Habit) BeforeCreate(tx *gorm.DB) error {
	if h.ID == uuid.Nil {
		h.ID = uuid.New()
	}
	h.CreatedAt = time.Now()
	h.UpdatedAt = time.Now()
	return nil
}

// BeforeUpdate is called before updating a habit record
func (h *Habit) BeforeUpdate(tx *gorm.DB) error {
	h.UpdatedAt = time.Now()
	return nil
}



