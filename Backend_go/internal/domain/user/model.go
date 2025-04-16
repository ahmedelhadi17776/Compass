package user

import (
	"time"

	"github.com/google/uuid"
)

// User represents a user in the system
type User struct {
	ID                  uuid.UUID              `json:"id" gorm:"type:uuid;primary_key"`
	Email               string                 `json:"email" gorm:"unique;not null"`
	Username            string                 `json:"username" gorm:"unique;not null"`
	PasswordHash        string                 `json:"-" gorm:"not null"`
	IsActive            bool                   `json:"is_active" gorm:"default:true"`
	IsSuperuser         bool                   `json:"is_superuser" gorm:"default:false"`
	CreatedAt           time.Time              `json:"created_at"`
	UpdatedAt           time.Time              `json:"updated_at"`
	DeletedAt           *time.Time             `json:"deleted_at,omitempty" gorm:"index"`
	MFAEnabled          bool                   `json:"mfa_enabled" gorm:"default:false"`
	MFASecret           string                 `json:"-"`
	FailedLoginAttempts int                    `json:"-" gorm:"default:0"`
	AccountLockedUntil  *time.Time             `json:"-"`
	Preferences         map[string]interface{} `json:"preferences,omitempty" gorm:"type:jsonb"`
}

// CreateUserRequest represents the request body for user registration
type CreateUserRequest struct {
	Email    string `json:"email" binding:"required,email" example:"user@example.com"`
	Username string `json:"username" binding:"required" example:"johndoe"`
	Password string `json:"password" binding:"required" example:"securepassword123"`
}

// LoginRequest represents the request body for user login
type LoginRequest struct {
	Email    string `json:"email" binding:"required,email" example:"user@example.com"`
	Password string `json:"password" binding:"required" example:"securepassword123"`
}

// UpdateUserRequest represents the request body for updating a user
type UpdateUserRequest struct {
	Username    string                 `json:"username,omitempty" example:"johndoe_updated"`
	Email       string                 `json:"email,omitempty" example:"updated@example.com"`
	Password    string                 `json:"password,omitempty" example:"newpassword123"`
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}

// UserResponse represents the response for user operations
type UserResponse struct {
	User User `json:"user"`
}

// LoginResponse represents the response for successful login
type LoginResponse struct {
	Token string `json:"token" example:"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."`
	User  User   `json:"user"`
}

// UserListResponse represents the response for listing users
type UserListResponse struct {
	Users []User `json:"users"`
}

// TableName specifies the table name for the User model
func (User) TableName() string {
	return "users"
}

// BeforeCreate is called before creating a new user record
func (u *User) BeforeCreate() error {
	if u.ID == uuid.Nil {
		u.ID = uuid.New()
	}
	return nil
}

// BeforeUpdate is called before updating a user record
func (u *User) BeforeUpdate() error {
	u.UpdatedAt = time.Now()
	return nil
}
