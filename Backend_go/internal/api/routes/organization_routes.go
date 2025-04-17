package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// OrganizationRoutes handles the setup of organization-related routes
type OrganizationRoutes struct {
	handler   *handlers.OrganizationHandler
	jwtSecret string
}

// NewOrganizationRoutes creates a new OrganizationRoutes instance
func NewOrganizationRoutes(handler *handlers.OrganizationHandler, jwtSecret string) *OrganizationRoutes {
	return &OrganizationRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all organization-related routes
func (or *OrganizationRoutes) RegisterRoutes(router *gin.Engine) {
	// Create an organization group with authentication middleware
	organizationGroup := router.Group("/api/organizations")
	organizationGroup.Use(middleware.NewAuthMiddleware(or.jwtSecret))

	// @Summary Create a new organization
	// @Description Create a new organization with the provided information
	// @Tags organizations
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param organization body dto.CreateOrganizationRequest true "Organization creation information"
	// @Success 201 {object} dto.OrganizationResponse "Organization created successfully"
	// @Failure 400 {object} map[string]string "Invalid request"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 409 {object} map[string]string "Organization name already exists"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/organizations [post]
	organizationGroup.POST("", or.handler.CreateOrganization)

	// @Summary Get all organizations
	// @Description Get all organizations with pagination
	// @Tags organizations
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param page query int false "Page number (default: 0)"
	// @Param pageSize query int false "Page size (default: 10)"
	// @Success 200 {object} dto.OrganizationListResponse "List of organizations"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/organizations [get]
	organizationGroup.GET("", or.handler.ListOrganizations)

	// @Summary Get an organization by ID
	// @Description Get detailed information about a specific organization
	// @Tags organizations
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Organization ID" format(uuid)
	// @Success 200 {object} dto.OrganizationResponse "Organization details"
	// @Failure 400 {object} map[string]string "Invalid organization ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Organization not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/organizations/{id} [get]
	organizationGroup.GET("/:id", or.handler.GetOrganization)

	// @Summary Get organization statistics
	// @Description Get detailed statistics about a specific organization
	// @Tags organizations
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Organization ID" format(uuid)
	// @Success 200 {object} dto.OrganizationStatsResponse "Organization statistics"
	// @Failure 400 {object} map[string]string "Invalid organization ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Organization not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/organizations/{id}/stats [get]
	organizationGroup.GET("/:id/stats", or.handler.GetOrganizationStats)

	// @Summary Update an organization
	// @Description Update an existing organization's information
	// @Tags organizations
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Organization ID" format(uuid)
	// @Param organization body dto.UpdateOrganizationRequest true "Organization update information"
	// @Success 200 {object} dto.OrganizationResponse "Organization updated successfully"
	// @Failure 400 {object} map[string]string "Invalid request or organization ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Organization not found"
	// @Failure 409 {object} map[string]string "Organization name already exists"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/organizations/{id} [put]
	organizationGroup.PUT("/:id", or.handler.UpdateOrganization)

	// @Summary Delete an organization
	// @Description Delete an existing organization
	// @Tags organizations
	// @Accept json
	// @Produce json
	// @Security BearerAuth
	// @Param id path string true "Organization ID" format(uuid)
	// @Success 204 "Organization deleted successfully"
	// @Failure 400 {object} map[string]string "Invalid organization ID"
	// @Failure 401 {object} map[string]string "Unauthorized"
	// @Failure 404 {object} map[string]string "Organization not found"
	// @Failure 500 {object} map[string]string "Internal server error"
	// @Router /api/organizations/{id} [delete]
	organizationGroup.DELETE("/:id", or.handler.DeleteOrganization)
}
