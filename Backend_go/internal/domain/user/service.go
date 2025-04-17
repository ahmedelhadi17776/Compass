package user

import (
	"context"
	"errors"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// Input types
type CreateUserInput struct {
	Email       string                 `json:"email"`
	Username    string                 `json:"username"`
	Password    string                 `json:"password"`
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}

type UpdateUserInput struct {
	Email       *string                `json:"email,omitempty"`
	Username    *string                `json:"username,omitempty"`
	Password    *string                `json:"password,omitempty"`
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}

// Common errors
var (
	ErrEmailExists        = errors.New("email already exists")
	ErrUsernameExists     = errors.New("username already exists")
	ErrInvalidCredentials = errors.New("invalid credentials")
	ErrAccountLocked      = errors.New("account is locked")
	ErrAccountInactive    = errors.New("account is inactive")
)

// Service interface
type Service interface {
	CreateUser(ctx context.Context, input CreateUserInput) (*User, error)
	GetUser(ctx context.Context, id uuid.UUID) (*User, error)
	GetUserByEmail(ctx context.Context, email string) (*User, error)
	GetUserByUsername(ctx context.Context, username string) (*User, error)
	ListUsers(ctx context.Context, filter UserFilter) ([]User, int64, error)
	UpdateUser(ctx context.Context, id uuid.UUID, input UpdateUserInput) (*User, error)
	DeleteUser(ctx context.Context, id uuid.UUID) error
	AuthenticateUser(ctx context.Context, email, password string) (*User, error)
	UpdatePassword(ctx context.Context, id uuid.UUID, currentPassword, newPassword string) error
	LockAccount(ctx context.Context, id uuid.UUID, duration time.Duration) error
	UnlockAccount(ctx context.Context, id uuid.UUID) error
}

type service struct {
	repo Repository
}

func NewService(repo Repository) Service {
	return &service{repo: repo}
}

func (s *service) CreateUser(ctx context.Context, input CreateUserInput) (*User, error) {
	// Validate input
	if input.Email == "" || input.Username == "" || input.Password == "" {
		return nil, ErrInvalidInput
	}

	// Check if email exists
	existingUser, err := s.repo.FindByEmail(ctx, input.Email)
	if err != nil {
		return nil, err
	}
	if existingUser != nil {
		return nil, ErrEmailExists
	}

	// Check if username exists
	existingUser, err = s.repo.FindByUsername(ctx, input.Username)
	if err != nil {
		return nil, err
	}
	if existingUser != nil {
		return nil, ErrUsernameExists
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	user := &User{
		ID:           uuid.New(),
		Email:        input.Email,
		Username:     input.Username,
		PasswordHash: string(hashedPassword),
		IsActive:     true,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
		Preferences:  input.Preferences,
	}

	err = s.repo.Create(ctx, user)
	if err != nil {
		return nil, err
	}

	return user, nil
}

func (s *service) GetUser(ctx context.Context, id uuid.UUID) (*User, error) {
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, ErrUserNotFound
	}
	return user, nil
}

func (s *service) GetUserByEmail(ctx context.Context, email string) (*User, error) {
	return s.repo.FindByEmail(ctx, email)
}

func (s *service) GetUserByUsername(ctx context.Context, username string) (*User, error) {
	return s.repo.FindByUsername(ctx, username)
}

func (s *service) ListUsers(ctx context.Context, filter UserFilter) ([]User, int64, error) {
	return s.repo.FindAll(ctx, filter)
}

func (s *service) UpdateUser(ctx context.Context, id uuid.UUID, input UpdateUserInput) (*User, error) {
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, ErrUserNotFound
	}

	// Update fields if provided
	if input.Email != nil {
		// Check if new email exists
		if *input.Email != user.Email {
			existingUser, err := s.repo.FindByEmail(ctx, *input.Email)
			if err != nil {
				return nil, err
			}
			if existingUser != nil {
				return nil, ErrEmailExists
			}
		}
		user.Email = *input.Email
	}

	if input.Username != nil {
		user.Username = *input.Username
	}

	if input.Password != nil {
		hashedPassword, err := bcrypt.GenerateFromPassword([]byte(*input.Password), bcrypt.DefaultCost)
		if err != nil {
			return nil, err
		}
		user.PasswordHash = string(hashedPassword)
	}

	if input.Preferences != nil {
		user.Preferences = input.Preferences
	}

	user.UpdatedAt = time.Now()
	err = s.repo.Update(ctx, user)
	if err != nil {
		return nil, err
	}

	return user, nil
}

func (s *service) DeleteUser(ctx context.Context, id uuid.UUID) error {
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if user == nil {
		return ErrUserNotFound
	}

	// Soft delete
	now := time.Now()
	user.DeletedAt = &now
	user.IsActive = false
	return s.repo.Update(ctx, user)
}

func (s *service) AuthenticateUser(ctx context.Context, email, password string) (*User, error) {
	user, err := s.repo.FindByEmail(ctx, email)
	if err != nil {
		return nil, err
	}
	if user == nil {
		return nil, ErrInvalidCredentials
	}

	if !user.IsActive {
		return nil, ErrAccountInactive
	}

	if user.AccountLockedUntil != nil && user.AccountLockedUntil.After(time.Now()) {
		return nil, ErrAccountLocked
	}

	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password))
	if err != nil {
		// Update failed login attempts
		user.FailedLoginAttempts++

		// Lock account if too many failed attempts
		if user.FailedLoginAttempts >= 5 {
			lockUntil := time.Now().Add(30 * time.Minute)
			user.AccountLockedUntil = &lockUntil
		}

		s.repo.Update(ctx, user)
		return nil, ErrInvalidCredentials
	}

	// Reset failed attempts on successful login
	user.FailedLoginAttempts = 0
	user.AccountLockedUntil = nil
	user.UpdatedAt = time.Now()
	s.repo.Update(ctx, user)

	return user, nil
}

func (s *service) UpdatePassword(ctx context.Context, id uuid.UUID, currentPassword, newPassword string) error {
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if user == nil {
		return ErrUserNotFound
	}

	// Verify current password
	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(currentPassword))
	if err != nil {
		return ErrInvalidCredentials
	}

	// Hash new password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return err
	}

	user.PasswordHash = string(hashedPassword)
	user.UpdatedAt = time.Now()

	return s.repo.Update(ctx, user)
}

func (s *service) LockAccount(ctx context.Context, id uuid.UUID, duration time.Duration) error {
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if user == nil {
		return ErrUserNotFound
	}

	lockUntil := time.Now().Add(duration)
	user.AccountLockedUntil = &lockUntil
	user.UpdatedAt = time.Now()

	return s.repo.Update(ctx, user)
}

func (s *service) UnlockAccount(ctx context.Context, id uuid.UUID) error {
	user, err := s.repo.FindByID(ctx, id)
	if err != nil {
		return err
	}
	if user == nil {
		return ErrUserNotFound
	}

	user.AccountLockedUntil = nil
	user.FailedLoginAttempts = 0
	user.UpdatedAt = time.Now()

	return s.repo.Update(ctx, user)
}
