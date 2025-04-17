package project

import (
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"
)

type ProjectStatus string

const (
	ProjectStatusActive    ProjectStatus = "Active"
	ProjectStatusCompleted ProjectStatus = "Completed"
	ProjectStatusArchived  ProjectStatus = "Archived"
	ProjectStatusOnHold    ProjectStatus = "On Hold"
)

type Project struct {
	ID             uuid.UUID     `json:"id" gorm:"type:uuid;primary_key;default:uuid_generate_v4()"`
	Name           string        `json:"name" gorm:"not null"`
	Description    string        `json:"description" gorm:"type:text"`
	Status         ProjectStatus `json:"status" gorm:"not null;default:'Active'"`
	CreatedAt      time.Time     `json:"created_at" gorm:"not null;default:current_timestamp"`
	UpdatedAt      time.Time     `json:"updated_at" gorm:"not null;default:current_timestamp"`
	CreatorID      uuid.UUID     `json:"creator_id" gorm:"type:uuid;not null"`
	OrganizationID uuid.UUID     `json:"organization_id" gorm:"type:uuid;not null"`
}

// CreateProjectRequest represents the request body for creating a project
type CreateProjectRequest struct {
	Name           string        `json:"name" binding:"required" example:"New Project"`
	Description    string        `json:"description" example:"A detailed project description"`
	Status         ProjectStatus `json:"status" example:"Active"`
	OrganizationID uuid.UUID     `json:"organization_id" binding:"required"`
}

// UpdateProjectRequest represents the request body for updating a project
type UpdateProjectRequest struct {
	Name        string        `json:"name,omitempty" example:"Updated Project Name"`
	Description string        `json:"description,omitempty" example:"Updated project description"`
	Status      ProjectStatus `json:"status,omitempty" example:"Completed"`
}

// ProjectResponse represents the response for project operations
type ProjectResponse struct {
	Project Project `json:"project"`
}

// ProjectListResponse represents the response for listing projects
type ProjectListResponse struct {
	Projects []Project `json:"projects"`
}

// TableName specifies the table name for the Project model
func (Project) TableName() string {
	return "projects"
}

// BeforeCreate is called before creating a new project record
func (p *Project) BeforeCreate(tx *gorm.DB) error {
	if p.ID == uuid.Nil {
		p.ID = uuid.New()
	}
	p.CreatedAt = time.Now()
	p.UpdatedAt = time.Now()
	return nil
}

// BeforeUpdate is called before updating a project record
func (p *Project) BeforeUpdate(tx *gorm.DB) error {
	p.UpdatedAt = time.Now()
	return nil
}

func (s ProjectStatus) IsValid() bool {
	switch s {
	case ProjectStatusActive, ProjectStatusCompleted,
		ProjectStatusArchived, ProjectStatusOnHold:
		return true
	}
	return false
}
