package user

import (
	"context"
	"errors"
	"fmt"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/auth"
	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
)

// Input types
type CreateUserInput struct {
	Email       string                 `json:"email"`
	Username    string                 `json:"username"`
	Password    string                 `json:"password"`
	FirstName   string                 `json:"first_name"`
	LastName    string                 `json:"last_name"`
	PhoneNumber string                 `json:"phone_number,omitempty"`
	AvatarURL   string                 `json:"avatar_url,omitempty"`
	Bio         string                 `json:"bio,omitempty"`
	Timezone    string                 `json:"timezone,omitempty"`
	Locale      string                 `json:"locale,omitempty"`
	Preferences map[string]interface{} `json:"preferences,omitempty"`
}

type UpdateUserInput struct {
	Email       *string                `json:"email,omitempty"`
	Username    *string                `json:"username,omitempty"`
	Password    *string                `json:"password,omitempty"`
	FirstName   *string                `json:"first_name,omitempty"`
	LastName    *string                `json:"last_name,omitempty"`
	PhoneNumber *string                `json:"phone_number,omitempty"`
	AvatarURL   *string                `json:"avatar_url,omitempty"`
	Bio         *string                `json:"bio,omitempty"`
	Timezone    *string                `json:"timezone,omitempty"`
	Locale      *string                `json:"locale,omitempty"`
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
	GetUserRolesAndPermissions(ctx context.Context, userID uuid.UUID) ([]string, []string, error)
}

type service struct {
	repo        Repository
	authService auth.Service
}

func NewService(repo Repository, authService auth.Service) Service {
	return &service{repo: repo, authService: authService}
}

// validateCreateUserInput validates the input for creating a user
func validateCreateUserInput(input CreateUserInput) error {
	if input.Email == "" {
		return errors.New("email is required")
	}
	if input.Username == "" {
		return errors.New("username is required")
	}
	if input.Password == "" {
		return errors.New("password is required")
	}
	if input.FirstName == "" {
		return errors.New("first name is required")
	}
	if input.LastName == "" {
		return errors.New("last name is required")
	}
	return nil
}

// CreateUser creates a new user with the given input
func (s *service) CreateUser(ctx context.Context, input CreateUserInput) (*User, error) {
	if err := validateCreateUserInput(input); err != nil {
		return nil, err
	}

	// Check if email already exists
	existingUser, err := s.repo.FindByEmail(ctx, input.Email)
	if err != nil && !errors.Is(err, ErrUserNotFound) {
		return nil, fmt.Errorf("checking email existence: %w", err)
	}
	if existingUser != nil {
		return nil, ErrEmailExists
	}

	// Check if username already exists
	existingUser, err = s.repo.FindByUsername(ctx, input.Username)
	if err != nil && !errors.Is(err, ErrUserNotFound) {
		return nil, fmt.Errorf("checking username existence: %w", err)
	}
	if existingUser != nil {
		return nil, ErrUsernameExists
	}

	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("hashing password: %w", err)
	}

	// Create user
	user := &User{
		ID:           uuid.New(),
		Email:        input.Email,
		Username:     input.Username,
		PasswordHash: string(hashedPassword),
		FirstName:    input.FirstName,
		LastName:     input.LastName,
		PhoneNumber:  input.PhoneNumber,
		AvatarURL:    input.AvatarURL,
		Bio:          input.Bio,
		Timezone:     input.Timezone,
		Locale:       input.Locale,
		Status:       UserStatusActive,
		IsActive:     true,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
		Preferences:  input.Preferences,
	}

	if err := s.repo.Create(ctx, user); err != nil {
		return nil, fmt.Errorf("creating user: %w", err)
	}

	// Get default user role
	defaultRole, err := s.authService.GetRoleByName(ctx, "user")
	if err != nil {
		return nil, fmt.Errorf("getting default role: %w", err)
	}

	// Assign default role to user
	if err := s.authService.AssignRoleToUser(ctx, user.ID, defaultRole.ID); err != nil {
		return nil, fmt.Errorf("assigning default role: %w", err)
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

	if input.FirstName != nil {
		user.FirstName = *input.FirstName
	}

	if input.LastName != nil {
		user.LastName = *input.LastName
	}

	if input.PhoneNumber != nil {
		user.PhoneNumber = *input.PhoneNumber
	}

	if input.AvatarURL != nil {
		user.AvatarURL = *input.AvatarURL
	}

	if input.Bio != nil {
		user.Bio = *input.Bio
	}

	if input.Timezone != nil {
		user.Timezone = *input.Timezone
	}

	if input.Locale != nil {
		user.Locale = *input.Locale
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

// GetUserRolesAndPermissions retrieves the roles and permissions for a given user
func (s *service) GetUserRolesAndPermissions(ctx context.Context, userID uuid.UUID) ([]string, []string, error) {
	// Get user roles from auth service
	userRoles, err := s.authService.GetUserRoles(ctx, userID)
	if err != nil {
		return nil, nil, fmt.Errorf("getting user roles: %w", err)
	}

	// Extract role names and collect all permissions
	roleNames := make([]string, 0, len(userRoles))
	allPermissions := make(map[string]struct{}) // Use map to deduplicate permissions

	for _, role := range userRoles {
		roleNames = append(roleNames, role.Name)
		for _, perm := range role.Permissions {
			allPermissions[perm.Name] = struct{}{}
		}
	}

	// Convert permissions map to slice
	permissions := make([]string, 0, len(allPermissions))
	for perm := range allPermissions {
		permissions = append(permissions, perm)
	}

	return roleNames, permissions, nil
}
