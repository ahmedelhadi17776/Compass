package organization

import (
	"time"

	"github.com/google/uuid"
)

// OrganizationStatus represents the status of an organization
type OrganizationStatus string

const (
	// OrganizationStatusActive represents an active organization
	OrganizationStatusActive OrganizationStatus = "Active"
	// OrganizationStatusInactive represents an inactive organization
	OrganizationStatusInactive OrganizationStatus = "Inactive"
	// OrganizationStatusArchived represents an archived organization
	OrganizationStatusArchived OrganizationStatus = "Archived"
)

// IsValid checks if the organization status is valid
func (s OrganizationStatus) IsValid() bool {
	switch s {
	case OrganizationStatusActive, OrganizationStatusInactive, OrganizationStatusArchived:
		return true
	default:
		return false
	}
}

// Organization represents an organization entity in the system
type Organization struct {
	ID          uuid.UUID          `json:"id" gorm:"type:uuid;primary_key"`
	Name        string             `json:"name" gorm:"type:varchar(255);not null;unique;index"`
	Description string             `json:"description" gorm:"type:text"`
	Status      OrganizationStatus `json:"status" gorm:"type:varchar(20);not null;default:'Active'"`
	CreatedAt   time.Time          `json:"created_at" gorm:"not null;default:CURRENT_TIMESTAMP"`
	UpdatedAt   time.Time          `json:"updated_at" gorm:"not null;default:CURRENT_TIMESTAMP;ON UPDATE CURRENT_TIMESTAMP"`
	DeletedAt   *time.Time         `json:"deleted_at,omitempty" gorm:"index"`
}

// TableName specifies the table name for the Organization model
func (Organization) TableName() string {
	return "organizations"
}

// Validate checks if the organization data is valid
func (o *Organization) Validate() error {
	if o.Name == "" {
		return ErrInvalidInput
	}
	if !o.Status.IsValid() {
		return ErrInvalidStatus
	}
	return nil
}

// BeforeCreate is a GORM hook that runs before creating a new organization
func (o *Organization) BeforeCreate() error {
	if o.ID == uuid.Nil {
		o.ID = uuid.New()
	}
	if o.Status == "" {
		o.Status = OrganizationStatusActive
	}
	now := time.Now()
	o.CreatedAt = now
	o.UpdatedAt = now
	return o.Validate()
}

// BeforeUpdate is a GORM hook that runs before updating an organization
func (o *Organization) BeforeUpdate() error {
	o.UpdatedAt = time.Now()
	return o.Validate()
}

// Common errors
var (
	ErrOrganizationNotFound = NewError("organization not found")
	ErrInvalidInput         = NewError("invalid input")
	ErrInvalidStatus        = NewError("invalid organization status")
	ErrDuplicateName        = NewError("organization name already exists")
)

// Error represents a domain error
type Error struct {
	message string
}

// NewError creates a new Error instance
func NewError(message string) *Error {
	return &Error{message: message}
}

// Error returns the error message
func (e *Error) Error() string {
	return e.message
}
