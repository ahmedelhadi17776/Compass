package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// ProjectRoutes handles the setup of project-related routes
type ProjectRoutes struct {
	handler   *handlers.ProjectHandler
	jwtSecret string
}

// NewProjectRoutes creates a new ProjectRoutes instance
func NewProjectRoutes(handler *handlers.ProjectHandler, jwtSecret string) *ProjectRoutes {
	return &ProjectRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all project-related routes
func (pr *ProjectRoutes) RegisterRoutes(router *gin.Engine) {
	// Create a project group with authentication middleware
	projectGroup := router.Group("/api/projects")
	projectGroup.Use(middleware.NewAuthMiddleware(pr.jwtSecret))

	// @Summary Create a new project
	// @Description Create a new project for the authenticated user
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param project body dto.CreateProjectRequest true "Project creation information"
	// @Success 201 {object} dto.ProjectResponse "Project created successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects [post]
	projectGroup.POST("", pr.handler.CreateProject)

	// @Summary Get all projects
	// @Description Get all projects for the authenticated user with pagination
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param page query int false "Page number (default: 0)"
	// @Param pageSize query int false "Page size (default: 10)"
	// @Success 200 {object} dto.ProjectListResponse "List of projects"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects [get]
	projectGroup.GET("", pr.handler.ListProjects)

	// @Summary Get a project by ID
	// @Description Get a specific project by its ID
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Success 200 {object} dto.ProjectResponse "Project details"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id} [get]
	projectGroup.GET("/:id", pr.handler.GetProject)

	// @Summary Get detailed project information
	// @Description Get detailed project information including members and task counts
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Success 200 {object} dto.ProjectDetailsResponse "Project details with members"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id}/details [get]
	projectGroup.GET("/:id/details", pr.handler.GetProjectDetails)

	// @Summary Update a project
	// @Description Update an existing project
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Param project body dto.UpdateProjectRequest true "Project update information"
	// @Success 200 {object} dto.ProjectResponse "Project updated successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id} [put]
	projectGroup.PUT("/:id", pr.handler.UpdateProject)

	// @Summary Delete a project
	// @Description Delete an existing project
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Success 204 "Project deleted successfully"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id} [delete]
	projectGroup.DELETE("/:id", pr.handler.DeleteProject)

	// @Summary Add a member to a project
	// @Description Add a new member to an existing project
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Param member body dto.AddMemberRequest true "Member information"
	// @Success 201 "Member added successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id}/members [post]
	projectGroup.POST("/:id/members", pr.handler.AddProjectMember)

	// @Summary Remove a member from a project
	// @Description Remove a member from an existing project
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Param userId path string true "User ID"
	// @Success 204 "Member removed successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project or member not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id}/members/{userId} [delete]
	projectGroup.DELETE("/:id/members/:userId", pr.handler.RemoveProjectMember)

	// @Summary Update project status
	// @Description Update the status of an existing project
	// @Tags projects
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Project ID"
	// @Param status body string true "New project status"
	// @Success 200 {object} dto.ProjectResponse "Project status updated successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Project not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/projects/{id}/status [put]
	projectGroup.PUT("/:id/status", pr.handler.UpdateProjectStatus)
}
