package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/dto"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/workflow"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/lib/pq"
	"gorm.io/datatypes"
)

// WorkflowHandler handles HTTP requests for workflow operations
type WorkflowHandler struct {
	service workflow.Service
}

// NewWorkflowHandler creates a new WorkflowHandler instance
func NewWorkflowHandler(service workflow.Service) *WorkflowHandler {
	return &WorkflowHandler{service: service}
}

// Helper functions to convert between DTO and domain models
func convertCreateRequestToDomain(req dto.CreateWorkflowRequest) workflow.CreateWorkflowRequest {
	var estimatedDuration *int
	if req.EstimatedDuration != nil {
		intVal := int(*req.EstimatedDuration)
		estimatedDuration = &intVal
	}

	// Convert map to JSON
	var config datatypes.JSON
	if req.Config != nil {
		if jsonData, err := json.Marshal(req.Config); err == nil {
			config = datatypes.JSON(jsonData)
		}
	}

	return workflow.CreateWorkflowRequest{
		Name:              req.Name,
		Description:       req.Description,
		WorkflowType:      workflow.WorkflowType(req.WorkflowType),
		OrganizationID:    req.OrganizationID,
		Config:            config,
		AIEnabled:         req.AIEnabled,
		EstimatedDuration: estimatedDuration,
		Deadline:          req.Deadline,
		Tags:              pq.StringArray(req.Tags),
	}
}

func convertUpdateRequestToDomain(req dto.UpdateWorkflowRequest) workflow.UpdateWorkflowRequest {
	var status *workflow.WorkflowStatus
	if req.Status != nil {
		s := workflow.WorkflowStatus(*req.Status)
		status = &s
	}

	var estimatedDuration *int
	if req.EstimatedDuration != nil {
		intVal := int(*req.EstimatedDuration)
		estimatedDuration = &intVal
	}

	// Convert map to JSON
	var config datatypes.JSON
	if req.Config != nil {
		if jsonData, err := json.Marshal(req.Config); err == nil {
			config = datatypes.JSON(jsonData)
		}
	}

	return workflow.UpdateWorkflowRequest{
		Name:              req.Name,
		Description:       req.Description,
		Status:            status,
		Config:            config,
		AIEnabled:         req.AIEnabled,
		EstimatedDuration: estimatedDuration,
		Deadline:          req.Deadline,
		Tags:              pq.StringArray(req.Tags),
	}
}

// CreateWorkflow godoc
// @Summary Create a new workflow
// @Description Create a new workflow with the provided information
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param workflow body dto.CreateWorkflowRequest true "Workflow creation request"
// @Success 201 {object} dto.WorkflowResponse "Workflow created successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 403 {object} map[string]string "Insufficient permissions"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows [post]
func (h *WorkflowHandler) CreateWorkflow(c *gin.Context) {
	var req dto.CreateWorkflowRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get creator ID from context (set by auth middleware)
	creatorID, exists := middleware.GetUserID(c)
	if !exists {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "user not authenticated"})
		return
	}

	// Convert and validate workflow type
	workflowType := workflow.WorkflowType(req.WorkflowType)
	if !workflowType.IsValid() {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow type"})
		return
	}

	domainReq := convertCreateRequestToDomain(req)
	response, err := h.service.CreateWorkflow(c.Request.Context(), domainReq, creatorID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, gin.H{"data": response})
}

// GetWorkflow godoc
// @Summary Get a workflow by ID
// @Description Get detailed information about a specific workflow
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Success 200 {object} dto.WorkflowResponse "Workflow details retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid workflow ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id} [get]
func (h *WorkflowHandler) GetWorkflow(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	// Get organization ID from header
	orgIDStr := c.GetHeader("X-Organization-ID")
	if orgIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "X-Organization-ID header is required"})
		return
	}

	orgID, err := uuid.Parse(orgIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid organization ID format"})
		return
	}

	response, err := h.service.GetWorkflow(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	// Check if workflow belongs to the organization
	if response.Workflow.OrganizationID != orgID {
		c.JSON(http.StatusForbidden, gin.H{"error": "workflow does not belong to the organization"})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

// ListWorkflows godoc
// @Summary List all workflows
// @Description Get a paginated list of workflows with optional filters
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param page query int false "Page number (default: 1)"
// @Param page_size query int false "Number of items per page (default: 10)"
// @Param organization_id query string false "Filter by organization ID"
// @Param workflow_type query string false "Filter by workflow type"
// @Param status query string false "Filter by status"
// @Param creator_id query string false "Filter by creator ID"
// @Success 200 {object} dto.WorkflowListResponse "List of workflows retrieved successfully"
// @Failure 400 {object} map[string]string "Invalid pagination parameters"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows [get]
func (h *WorkflowHandler) ListWorkflows(c *gin.Context) {
	pageStr := c.DefaultQuery("page", "1")
	pageSizeStr := c.DefaultQuery("page_size", "10")

	page, err := strconv.Atoi(pageStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid page number"})
		return
	}
	pageSize, err := strconv.Atoi(pageSizeStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid page size"})
		return
	}

	// Get organization ID from header
	orgIDStr := c.GetHeader("X-Organization-ID")
	if orgIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "X-Organization-ID header is required"})
		return
	}

	orgID, err := uuid.Parse(orgIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid organization ID format"})
		return
	}

	filter := &workflow.WorkflowFilter{
		Page:           page,
		PageSize:       pageSize,
		OrganizationID: &orgID,
	}

	// Parse optional filters
	if workflowTypeStr := c.Query("workflow_type"); workflowTypeStr != "" {
		workflowType := workflow.WorkflowType(workflowTypeStr)
		if workflowType.IsValid() {
			filter.WorkflowType = &workflowType
		}
	}
	if statusStr := c.Query("status"); statusStr != "" {
		status := workflow.WorkflowStatus(statusStr)
		if status.IsValid() {
			filter.Status = &status
		}
	}
	if creatorIDStr := c.Query("creator_id"); creatorIDStr != "" {
		if creatorID, err := uuid.Parse(creatorIDStr); err == nil {
			filter.CreatedBy = &creatorID
		}
	}

	response, err := h.service.ListWorkflows(c.Request.Context(), filter)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

// UpdateWorkflow godoc
// @Summary Update a workflow
// @Description Update an existing workflow's information
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Param workflow body dto.UpdateWorkflowRequest true "Workflow update information"
// @Success 200 {object} dto.WorkflowResponse "Workflow updated successfully"
// @Failure 400 {object} map[string]string "Invalid request"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id} [put]
func (h *WorkflowHandler) UpdateWorkflow(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	var req dto.UpdateWorkflowRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Get organization ID from header
	orgIDStr := c.GetHeader("X-Organization-ID")
	if orgIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "X-Organization-ID header is required"})
		return
	}

	orgID, err := uuid.Parse(orgIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid organization ID format"})
		return
	}

	// Verify workflow belongs to organization
	existingWorkflow, err := h.service.GetWorkflow(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	if existingWorkflow.Workflow.OrganizationID != orgID {
		c.JSON(http.StatusForbidden, gin.H{"error": "workflow does not belong to the organization"})
		return
	}

	domainReq := convertUpdateRequestToDomain(req)
	response, err := h.service.UpdateWorkflow(c.Request.Context(), id, domainReq)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

// DeleteWorkflow godoc
// @Summary Delete a workflow
// @Description Delete an existing workflow
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Success 204 "Workflow deleted successfully"
// @Failure 400 {object} map[string]string "Invalid workflow ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id} [delete]
func (h *WorkflowHandler) DeleteWorkflow(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	// Get organization ID from header
	orgIDStr := c.GetHeader("X-Organization-ID")
	if orgIDStr == "" {
		c.JSON(http.StatusBadRequest, gin.H{"error": "X-Organization-ID header is required"})
		return
	}

	orgID, err := uuid.Parse(orgIDStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid organization ID format"})
		return
	}

	// Verify workflow belongs to organization
	existingWorkflow, err := h.service.GetWorkflow(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
		return
	}

	if existingWorkflow.Workflow.OrganizationID != orgID {
		c.JSON(http.StatusForbidden, gin.H{"error": "workflow does not belong to the organization"})
		return
	}

	if err := h.service.DeleteWorkflow(c.Request.Context(), id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusNoContent)
}

// ExecuteWorkflow godoc
// @Summary Execute a workflow
// @Description Start the execution of a workflow
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Success 200 {object} dto.WorkflowResponse "Workflow execution started successfully"
// @Failure 400 {object} map[string]string "Invalid workflow ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id}/execute [post]
func (h *WorkflowHandler) ExecuteWorkflow(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	response, err := h.service.ExecuteWorkflow(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": response})
}

// CancelWorkflowExecution godoc
// @Summary Cancel a workflow execution
// @Description Cancel an active workflow execution
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Success 200 "Workflow execution cancelled successfully"
// @Failure 400 {object} map[string]string "Invalid workflow ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id}/cancel [post]
func (h *WorkflowHandler) CancelWorkflowExecution(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	if err := h.service.CancelWorkflowExecution(c.Request.Context(), id); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.Status(http.StatusOK)
}

// AnalyzeWorkflow godoc
// @Summary Analyze a workflow
// @Description Get analysis and metrics for a workflow
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Success 200 {object} map[string]interface{} "Workflow analysis"
// @Failure 400 {object} map[string]string "Invalid workflow ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id}/analyze [get]
func (h *WorkflowHandler) AnalyzeWorkflow(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	analysis, err := h.service.AnalyzeWorkflow(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": analysis})
}

// OptimizeWorkflow godoc
// @Summary Optimize a workflow
// @Description Get optimization recommendations for a workflow
// @Tags workflows
// @Accept json
// @Produce json
// @Security BearerAuth
// @Param id path string true "Workflow ID" format(uuid)
// @Success 200 {object} map[string]interface{} "Workflow optimization results"
// @Failure 400 {object} map[string]string "Invalid workflow ID"
// @Failure 401 {object} map[string]string "Unauthorized"
// @Failure 404 {object} map[string]string "Workflow not found"
// @Failure 500 {object} map[string]string "Internal server error"
// @Router /api/workflows/{id}/optimize [post]
func (h *WorkflowHandler) OptimizeWorkflow(c *gin.Context) {
	id, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "invalid workflow ID"})
		return
	}

	optimization, err := h.service.OptimizeWorkflow(c.Request.Context(), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"data": optimization})
}
