package dto

import (
	"time"

	"github.com/google/uuid"
)

type CreateUserRequest struct {
	Email          string     `json:"email" binding:"required,email"`
	Username       string     `json:"username" binding:"required"`
	Password       string     `json:"password" binding:"required,min=8"`
	FirstName      string     `json:"first_name" binding:"required"`
	LastName       string     `json:"last_name" binding:"required"`
	PhoneNumber    string     `json:"phone_number"`
	Timezone       string     `json:"timezone"`
	Locale         string     `json:"locale"`
	OrganizationID *uuid.UUID `json:"organization_id,omitempty"`
}

type UpdateUserRequest struct {
	Email                   *string                `json:"email,omitempty" binding:"omitempty,email"`
	FirstName               *string                `json:"first_name,omitempty"`
	LastName                *string                `json:"last_name,omitempty"`
	PhoneNumber             *string                `json:"phone_number,omitempty"`
	AvatarURL               *string                `json:"avatar_url,omitempty"`
	Bio                     *string                `json:"bio,omitempty"`
	Timezone                *string                `json:"timezone,omitempty"`
	Locale                  *string                `json:"locale,omitempty"`
	NotificationPreferences map[string]interface{} `json:"notification_preferences,omitempty"`
	WorkspaceSettings       map[string]interface{} `json:"workspace_settings,omitempty"`
	Username                *string                `json:"username,omitempty"`
}

type UserResponse struct {
	ID          uuid.UUID  `json:"id"`
	Email       string     `json:"email"`
	Username    string     `json:"username"`
	IsActive    bool       `json:"is_active"`
	IsSuperuser bool       `json:"is_superuser"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
	DeletedAt   *time.Time `json:"deleted_at,omitempty"`
	FirstName   string     `json:"first_name,omitempty"`
	LastName    string     `json:"last_name,omitempty"`
	PhoneNumber string     `json:"phone_number,omitempty"`
	AvatarURL   string     `json:"avatar_url,omitempty"`
	Bio         string     `json:"bio,omitempty"`
	Timezone    string     `json:"timezone,omitempty"`
	Locale      string     `json:"locale,omitempty"`

	// Security info
	MFAEnabled          bool       `json:"mfa_enabled"`
	LastLogin           *time.Time `json:"last_login,omitempty"`
	FailedLoginAttempts int        `json:"failed_login_attempts"`
	AccountLockedUntil  *time.Time `json:"account_locked_until,omitempty"`
	ForcePasswordChange bool       `json:"force_password_change"`

	// Organization
	OrganizationID *uuid.UUID `json:"organization_id,omitempty"`

	// Preferences
	NotificationPreferences map[string]interface{} `json:"notification_preferences,omitempty"`
	AllowedIPRanges         []string               `json:"allowed_ip_ranges,omitempty"`
	MaxSessions             int                    `json:"max_sessions"`
	WorkspaceSettings       map[string]interface{} `json:"workspace_settings,omitempty"`
}

type UserListResponse struct {
	Users      []UserResponse `json:"users"`
	TotalCount int64          `json:"total_count"`
	Page       int            `json:"page"`
	PageSize   int            `json:"page_size"`
}

type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

type LoginResponse struct {
	Token     string       `json:"token"`
	User      UserResponse `json:"user"`
	ExpiresAt time.Time    `json:"expires_at"`
}

type TokenResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int    `json:"expires_in"`
}
