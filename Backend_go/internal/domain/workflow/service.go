package workflow

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/sirupsen/logrus"
	"gorm.io/datatypes"
)

// Service defines the interface for workflow business logic
type Service interface {
	// Workflow operations
	CreateWorkflow(ctx context.Context, req CreateWorkflowRequest, creatorID uuid.UUID) (*WorkflowResponse, error)
	UpdateWorkflow(ctx context.Context, id uuid.UUID, req UpdateWorkflowRequest) (*WorkflowResponse, error)
	DeleteWorkflow(ctx context.Context, id uuid.UUID) error
	GetWorkflow(ctx context.Context, id uuid.UUID) (*WorkflowResponse, error)
	ListWorkflows(ctx context.Context, filter *WorkflowFilter) (*WorkflowListResponse, error)

	// Step operations
	AddWorkflowStep(ctx context.Context, workflowID uuid.UUID, req CreateWorkflowStepRequest) (*WorkflowStepResponse, error)
	UpdateWorkflowStep(ctx context.Context, id uuid.UUID, req UpdateWorkflowStepRequest) (*WorkflowStepResponse, error)
	DeleteWorkflowStep(ctx context.Context, id uuid.UUID) error
	GetWorkflowStep(ctx context.Context, id uuid.UUID) (*WorkflowStepResponse, error)
	ListWorkflowSteps(ctx context.Context, filter *WorkflowStepFilter) (*WorkflowStepListResponse, error)

	// Execution operations
	ExecuteWorkflow(ctx context.Context, workflowID uuid.UUID) (*WorkflowExecutionResponse, error)
	ExecuteWorkflowStep(ctx context.Context, stepID uuid.UUID, executionID uuid.UUID) (*WorkflowStepExecution, error)
	CancelWorkflowExecution(ctx context.Context, workflowID uuid.UUID) error
	GetWorkflowExecution(ctx context.Context, id uuid.UUID) (*WorkflowExecutionResponse, error)
	ListWorkflowExecutions(ctx context.Context, filter *WorkflowExecutionFilter) (*WorkflowExecutionListResponse, error)

	// Analysis and optimization
	AnalyzeWorkflow(ctx context.Context, workflowID uuid.UUID) (map[string]interface{}, error)
	OptimizeWorkflow(ctx context.Context, workflowID uuid.UUID) (map[string]interface{}, error)

	GetRepo() Repository
	GetExecutor() WorkflowExecutor
}

type service struct {
	repo     Repository
	logger   *logrus.Logger
	executor WorkflowExecutor
}

// WorkflowExecutor handles the actual execution of workflow steps
type WorkflowExecutor interface {
	ExecuteStep(ctx context.Context, step *WorkflowStep, execution *WorkflowStepExecution) error
	ValidateTransition(ctx context.Context, fromStep, toStep *WorkflowStep) error
	ProcessNextSteps(ctx context.Context, currentStep *WorkflowStep, execution *WorkflowStepExecution) error
}

// ServiceConfig holds the configuration for the workflow service
type ServiceConfig struct {
	Repository Repository
	Logger     *logrus.Logger
	Executor   WorkflowExecutor
}

// NewService creates a new workflow service
func NewService(cfg ServiceConfig) Service {
	return &service{
		repo:     cfg.Repository,
		logger:   cfg.Logger,
		executor: cfg.Executor,
	}
}

// CreateWorkflow implements the workflow creation logic
func (s *service) CreateWorkflow(ctx context.Context, req CreateWorkflowRequest, creatorID uuid.UUID) (*WorkflowResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"creator_id": creatorID,
		"name":       req.Name,
	}).Info("Creating new workflow")

	metadata := map[string]interface{}{
		"created_at": time.Now().UTC(),
		"creator_id": creatorID.String(),
		"version":    "1.0.0",
	}
	metadataJSON, _ := json.Marshal(metadata)

	workflow := &Workflow{
		ID:               uuid.New(),
		Name:             req.Name,
		Description:      req.Description,
		WorkflowType:     req.WorkflowType,
		CreatedBy:        creatorID,
		OrganizationID:   req.OrganizationID,
		Status:           WorkflowStatusPending,
		Config:           req.Config,
		AIEnabled:        req.AIEnabled,
		Tags:             req.Tags,
		Version:          "1.0.0",
		WorkflowMetadata: datatypes.JSON(metadataJSON),
	}

	if req.EstimatedDuration != nil {
		workflow.EstimatedDuration = req.EstimatedDuration
	}

	if req.Deadline != nil {
		workflow.Deadline = req.Deadline
	}

	if err := s.repo.Create(ctx, workflow); err != nil {
		s.logger.WithError(err).Error("Failed to create workflow")
		return nil, fmt.Errorf("failed to create workflow: %w", err)
	}

	return &WorkflowResponse{Workflow: workflow}, nil
}

// UpdateWorkflow implements the workflow update logic
func (s *service) UpdateWorkflow(ctx context.Context, id uuid.UUID, req UpdateWorkflowRequest) (*WorkflowResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": id,
	}).Info("Updating workflow")

	workflow, err := s.repo.GetByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow for update")
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Update fields if they are provided
	if req.Name != nil {
		workflow.Name = *req.Name
	}
	if req.Description != nil {
		workflow.Description = *req.Description
	}
	if req.Status != nil {
		workflow.Status = *req.Status
	}
	if req.Config != nil {
		workflow.Config = req.Config
	}
	if req.AIEnabled != nil {
		workflow.AIEnabled = *req.AIEnabled
	}
	if req.EstimatedDuration != nil {
		workflow.EstimatedDuration = req.EstimatedDuration
	}
	if req.Deadline != nil {
		workflow.Deadline = req.Deadline
	}
	if req.Tags != nil {
		workflow.Tags = req.Tags
	}

	// Update the metadata to include update time
	var metadata map[string]interface{}
	if workflow.WorkflowMetadata != nil {
		if err := json.Unmarshal(workflow.WorkflowMetadata, &metadata); err == nil {
			metadata["updated_at"] = time.Now().UTC()
			if metadataJSON, err := json.Marshal(metadata); err == nil {
				workflow.WorkflowMetadata = datatypes.JSON(metadataJSON)
			}
		}
	}

	if err := s.repo.Update(ctx, workflow); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow")
		return nil, fmt.Errorf("failed to update workflow: %w", err)
	}

	return &WorkflowResponse{Workflow: workflow}, nil
}

// DeleteWorkflow implements the workflow deletion logic
func (s *service) DeleteWorkflow(ctx context.Context, id uuid.UUID) error {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": id,
	}).Info("Deleting workflow")

	// First check if workflow exists
	_, err := s.repo.GetByID(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get workflow: %w", err)
	}

	// Cancel any active executions
	if err := s.repo.CancelActiveExecutions(ctx, id); err != nil {
		s.logger.WithError(err).Error("Failed to cancel active executions")
		// Continue with deletion even if cancellation fails
	}

	if err := s.repo.Delete(ctx, id); err != nil {
		s.logger.WithError(err).Error("Failed to delete workflow")
		return fmt.Errorf("failed to delete workflow: %w", err)
	}

	return nil
}

// GetWorkflow implements the workflow retrieval logic
func (s *service) GetWorkflow(ctx context.Context, id uuid.UUID) (*WorkflowResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": id,
	}).Info("Getting workflow details")

	workflow, err := s.repo.GetByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow")
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	return &WorkflowResponse{Workflow: workflow}, nil
}

// ListWorkflows implements the workflow listing logic
func (s *service) ListWorkflows(ctx context.Context, filter *WorkflowFilter) (*WorkflowListResponse, error) {
	s.logger.Info("Listing workflows")

	workflows, total, err := s.repo.List(ctx, filter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflows")
		return nil, fmt.Errorf("failed to list workflows: %w", err)
	}

	return &WorkflowListResponse{
		Workflows: workflows,
		Total:     total,
	}, nil
}

// AddWorkflowStep implements the step creation logic
func (s *service) AddWorkflowStep(ctx context.Context, workflowID uuid.UUID, req CreateWorkflowStepRequest) (*WorkflowStepResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": workflowID,
		"step_name":   req.Name,
	}).Info("Adding workflow step")

	// First check if workflow exists
	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	step := &WorkflowStep{
		ID:          uuid.New(),
		WorkflowID:  workflowID,
		Name:        req.Name,
		Description: req.Description,
		StepType:    req.StepType,
		StepOrder:   req.StepOrder,
		Status:      StepStatusPending,
		Config:      req.Config,
		Conditions:  req.Conditions,
		IsRequired:  true, // Default to required
	}

	if req.Timeout != nil {
		step.Timeout = req.Timeout
	}

	if req.IsRequired != nil {
		step.IsRequired = *req.IsRequired
	}

	if req.AssignedTo != nil {
		step.AssignedTo = req.AssignedTo
	}

	if err := s.repo.CreateStep(ctx, step); err != nil {
		s.logger.WithError(err).Error("Failed to create workflow step")
		return nil, fmt.Errorf("failed to create workflow step: %w", err)
	}

	// Update workflow updated_at timestamp
	workflow.UpdatedAt = time.Now()
	if err := s.repo.Update(ctx, workflow); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow timestamp")
		// Continue even if timestamp update fails
	}

	return &WorkflowStepResponse{Step: step}, nil
}

// UpdateWorkflowStep implements the step update logic
func (s *service) UpdateWorkflowStep(ctx context.Context, id uuid.UUID, req UpdateWorkflowStepRequest) (*WorkflowStepResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"step_id": id,
	}).Info("Updating workflow step")

	step, err := s.repo.GetStepByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow step for update")
		return nil, fmt.Errorf("failed to get workflow step: %w", err)
	}

	// Update fields if they are provided
	if req.Name != nil {
		step.Name = *req.Name
	}
	if req.Description != nil {
		step.Description = *req.Description
	}
	if req.StepType != nil {
		step.StepType = *req.StepType
	}
	if req.StepOrder != nil {
		step.StepOrder = *req.StepOrder
	}
	if req.Status != nil {
		step.Status = *req.Status
	}
	if req.Config != nil {
		step.Config = req.Config
	}
	if req.Conditions != nil {
		step.Conditions = req.Conditions
	}
	if req.Timeout != nil {
		step.Timeout = req.Timeout
	}
	if req.IsRequired != nil {
		step.IsRequired = *req.IsRequired
	}
	if req.AssignedTo != nil {
		step.AssignedTo = req.AssignedTo
	}

	if err := s.repo.UpdateStep(ctx, step); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow step")
		return nil, fmt.Errorf("failed to update workflow step: %w", err)
	}

	// Update parent workflow updated_at timestamp
	workflow, err := s.repo.GetByID(ctx, step.WorkflowID)
	if err == nil {
		workflow.UpdatedAt = time.Now()
		_ = s.repo.Update(ctx, workflow) // Ignore error as this is a secondary operation
	}

	return &WorkflowStepResponse{Step: step}, nil
}

// DeleteWorkflowStep implements the step deletion logic
func (s *service) DeleteWorkflowStep(ctx context.Context, id uuid.UUID) error {
	s.logger.WithFields(logrus.Fields{
		"step_id": id,
	}).Info("Deleting workflow step")

	// First check if step exists and get its workflow ID
	step, err := s.repo.GetStepByID(ctx, id)
	if err != nil {
		return fmt.Errorf("failed to get workflow step: %w", err)
	}

	// Check if there are any transitions using this step
	transitions, _, err := s.repo.ListTransitions(ctx, &WorkflowTransitionFilter{
		FromStepID: &id,
	})
	if err != nil {
		s.logger.WithError(err).Error("Failed to list transitions from step")
		// Continue with deletion even if transition check fails
	}

	// If there are transitions, delete them first
	for _, transition := range transitions {
		if err := s.repo.DeleteTransition(ctx, transition.ID); err != nil {
			s.logger.WithError(err).WithField("transition_id", transition.ID).Error("Failed to delete transition")
			// Continue with other transitions
		}
	}

	// Also check transitions where this step is a target
	toTransitions, _, err := s.repo.ListTransitions(ctx, &WorkflowTransitionFilter{
		ToStepID: &id,
	})
	if err != nil {
		s.logger.WithError(err).Error("Failed to list transitions to step")
		// Continue with deletion even if transition check fails
	}

	// Delete transitions where this step is a target
	for _, transition := range toTransitions {
		if err := s.repo.DeleteTransition(ctx, transition.ID); err != nil {
			s.logger.WithError(err).WithField("transition_id", transition.ID).Error("Failed to delete transition")
			// Continue with other transitions
		}
	}

	if err := s.repo.DeleteStep(ctx, id); err != nil {
		s.logger.WithError(err).Error("Failed to delete workflow step")
		return fmt.Errorf("failed to delete workflow step: %w", err)
	}

	// Update parent workflow updated_at timestamp
	workflowID := step.WorkflowID
	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err == nil {
		workflow.UpdatedAt = time.Now()
		_ = s.repo.Update(ctx, workflow) // Ignore error as this is a secondary operation
	}

	return nil
}

// GetWorkflowStep implements the step retrieval logic
func (s *service) GetWorkflowStep(ctx context.Context, id uuid.UUID) (*WorkflowStepResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"step_id": id,
	}).Info("Getting workflow step details")

	step, err := s.repo.GetStepByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow step")
		return nil, fmt.Errorf("failed to get workflow step: %w", err)
	}

	return &WorkflowStepResponse{Step: step}, nil
}

// ListWorkflowSteps implements the step listing logic
func (s *service) ListWorkflowSteps(ctx context.Context, filter *WorkflowStepFilter) (*WorkflowStepListResponse, error) {
	s.logger.Info("Listing workflow steps")

	steps, total, err := s.repo.ListSteps(ctx, filter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflow steps")
		return nil, fmt.Errorf("failed to list workflow steps: %w", err)
	}

	return &WorkflowStepListResponse{
		Steps: steps,
		Total: total,
	}, nil
}

// ExecuteWorkflow implements the workflow execution logic
func (s *service) ExecuteWorkflow(ctx context.Context, workflowID uuid.UUID) (*WorkflowExecutionResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": workflowID,
	}).Info("Executing workflow")

	// Check if workflow exists
	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Update workflow status to active
	if workflow.Status != WorkflowStatusActive {
		err = s.repo.UpdateStatus(ctx, workflowID, WorkflowStatusActive)
		if err != nil {
			s.logger.WithError(err).Error("Failed to update workflow status to active")
			return nil, fmt.Errorf("failed to update workflow status: %w", err)
		}
		workflow.Status = WorkflowStatusActive
	}

	// Create a new execution record
	now := time.Now()
	executionMetadata := map[string]interface{}{
		"started_by": "system",
		"version":    workflow.Version,
	}
	metadataJSON, _ := json.Marshal(executionMetadata)

	execution := &WorkflowExecution{
		ID:                uuid.New(),
		WorkflowID:        workflowID,
		Status:            WorkflowStatusActive,
		ExecutionPriority: 0, // Default priority
		ExecutionMetadata: datatypes.JSON(metadataJSON),
		StartedAt:         now,
		UpdatedAt:         now,
	}

	if err := s.repo.CreateExecution(ctx, execution); err != nil {
		s.logger.WithError(err).Error("Failed to create workflow execution")
		return nil, fmt.Errorf("failed to create workflow execution: %w", err)
	}

	// Find first step (lowest step order)
	stepFilter := &WorkflowStepFilter{
		WorkflowID: &workflowID,
	}
	steps, _, err := s.repo.ListSteps(ctx, stepFilter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflow steps")
		return nil, fmt.Errorf("failed to list workflow steps: %w", err)
	}

	if len(steps) == 0 {
		// No steps to execute, mark workflow as completed
		execution.Status = WorkflowStatusCompleted
		completedTime := time.Now()
		execution.CompletedAt = &completedTime
		if err := s.repo.UpdateExecution(ctx, execution); err != nil {
			s.logger.WithError(err).Error("Failed to update workflow execution")
			// Continue even if update fails
		}

		// Update workflow status
		if err := s.repo.UpdateStatus(ctx, workflowID, WorkflowStatusCompleted); err != nil {
			s.logger.WithError(err).Error("Failed to update workflow status to completed")
			// Continue even if update fails
		}

		return &WorkflowExecutionResponse{Execution: execution}, nil
	}

	// Find first step (assume steps are ordered by step_order)
	firstStep := steps[0]
	for _, step := range steps {
		if step.StepOrder < firstStep.StepOrder {
			firstStep = step
		}
	}

	// Create execution for first step
	stepMetadata := map[string]interface{}{
		"auto_triggered": true,
	}
	stepMetadataJSON, _ := json.Marshal(stepMetadata)

	stepExecution := &WorkflowStepExecution{
		ID:                uuid.New(),
		ExecutionID:       execution.ID,
		StepID:            firstStep.ID,
		Status:            StepStatusPending,
		ExecutionPriority: 0, // Default priority
		ExecutionMetadata: datatypes.JSON(stepMetadataJSON),
		StartedAt:         now,
		UpdatedAt:         now,
	}

	if err := s.repo.CreateStepExecution(ctx, stepExecution); err != nil {
		s.logger.WithError(err).Error("Failed to create step execution")
		return nil, fmt.Errorf("failed to create step execution: %w", err)
	}

	// Start step execution asynchronously if executor is available
	if s.executor != nil {
		go func() {
			ctx := context.Background() // Use a new context for async execution
			if err := s.executor.ExecuteStep(ctx, &firstStep, stepExecution); err != nil {
				s.logger.WithError(err).Error("Failed to execute workflow step")
				// Update step execution with error
				stepExecution.Status = StepStatusFailed
				errorStr := err.Error()
				stepExecution.Error = &errorStr
				_ = s.repo.UpdateStepExecution(ctx, stepExecution)
			}
		}()
	}

	return &WorkflowExecutionResponse{Execution: execution}, nil
}

// ExecuteWorkflowStep implements the step execution logic
func (s *service) ExecuteWorkflowStep(ctx context.Context, stepID uuid.UUID, executionID uuid.UUID) (*WorkflowStepExecution, error) {
	s.logger.WithFields(logrus.Fields{
		"step_id":      stepID,
		"execution_id": executionID,
	}).Info("Executing workflow step")

	// Verify the step exists
	step, err := s.repo.GetStepByID(ctx, stepID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow step: %w", err)
	}

	// Verify the execution exists
	execution, err := s.repo.GetExecutionByID(ctx, executionID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow execution: %w", err)
	}

	// Check if execution is active
	if execution.Status != WorkflowStatusActive && execution.Status != WorkflowStatusPending {
		return nil, fmt.Errorf("cannot execute step: workflow execution is not active")
	}

	// Create a new step execution
	now := time.Now()
	manualMetadata := map[string]interface{}{
		"manually_triggered": true,
	}
	manualMetadataJSON, _ := json.Marshal(manualMetadata)

	stepExecution := &WorkflowStepExecution{
		ID:                uuid.New(),
		ExecutionID:       executionID,
		StepID:            stepID,
		Status:            StepStatusActive,
		ExecutionPriority: 0, // Default priority
		ExecutionMetadata: datatypes.JSON(manualMetadataJSON),
		StartedAt:         now,
		UpdatedAt:         now,
	}

	if err := s.repo.CreateStepExecution(ctx, stepExecution); err != nil {
		s.logger.WithError(err).Error("Failed to create step execution")
		return nil, fmt.Errorf("failed to create step execution: %w", err)
	}

	// Execute step if executor is available
	if s.executor != nil {
		if err := s.executor.ExecuteStep(ctx, step, stepExecution); err != nil {
			s.logger.WithError(err).Error("Failed to execute workflow step")
			// Update step execution with error
			stepExecution.Status = StepStatusFailed
			errorStr := err.Error()
			stepExecution.Error = &errorStr
			if err := s.repo.UpdateStepExecution(ctx, stepExecution); err != nil {
				s.logger.WithError(err).Error("Failed to update step execution status")
			}
			return stepExecution, fmt.Errorf("failed to execute workflow step: %w", err)
		}
	}

	return stepExecution, nil
}

// CancelWorkflowExecution implements the execution cancellation logic
func (s *service) CancelWorkflowExecution(ctx context.Context, workflowID uuid.UUID) error {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": workflowID,
	}).Info("Cancelling workflow execution")

	// Check if workflow exists
	_, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return fmt.Errorf("failed to get workflow: %w", err)
	}

	// Cancel active executions
	if err := s.repo.CancelActiveExecutions(ctx, workflowID); err != nil {
		s.logger.WithError(err).Error("Failed to cancel active executions")
		return fmt.Errorf("failed to cancel active executions: %w", err)
	}

	// Update workflow status
	if err := s.repo.UpdateStatus(ctx, workflowID, WorkflowStatusCancelled); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow status to cancelled")
		return fmt.Errorf("failed to update workflow status: %w", err)
	}

	return nil
}

// GetWorkflowExecution implements the execution retrieval logic
func (s *service) GetWorkflowExecution(ctx context.Context, id uuid.UUID) (*WorkflowExecutionResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"execution_id": id,
	}).Info("Getting workflow execution details")

	execution, err := s.repo.GetExecutionByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow execution")
		return nil, fmt.Errorf("failed to get workflow execution: %w", err)
	}

	return &WorkflowExecutionResponse{Execution: execution}, nil
}

// ListWorkflowExecutions implements the execution listing logic
func (s *service) ListWorkflowExecutions(ctx context.Context, filter *WorkflowExecutionFilter) (*WorkflowExecutionListResponse, error) {
	s.logger.Info("Listing workflow executions")

	executions, total, err := s.repo.ListExecutions(ctx, filter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflow executions")
		return nil, fmt.Errorf("failed to list workflow executions: %w", err)
	}

	return &WorkflowExecutionListResponse{
		Executions: executions,
		Total:      total,
	}, nil
}

// AnalyzeWorkflow implements the workflow analysis logic
func (s *service) AnalyzeWorkflow(ctx context.Context, workflowID uuid.UUID) (map[string]interface{}, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": workflowID,
	}).Info("Analyzing workflow")

	// Check if workflow exists
	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Get workflow steps
	stepFilter := &WorkflowStepFilter{
		WorkflowID: &workflowID,
	}
	steps, _, err := s.repo.ListSteps(ctx, stepFilter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflow steps")
		return nil, fmt.Errorf("failed to list workflow steps: %w", err)
	}

	// Get workflow executions
	executionFilter := &WorkflowExecutionFilter{
		WorkflowID: &workflowID,
	}
	executions, _, err := s.repo.ListExecutions(ctx, executionFilter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflow executions")
		return nil, fmt.Errorf("failed to list workflow executions: %w", err)
	}

	// Perform basic analysis
	analysis := map[string]interface{}{
		"workflow_id":          workflowID,
		"name":                 workflow.Name,
		"total_steps":          len(steps),
		"total_executions":     len(executions),
		"average_success_rate": workflow.SuccessRate,
	}

	// Count executions by status
	statusCounts := make(map[string]int)
	for _, exec := range executions {
		statusCounts[string(exec.Status)]++
	}
	analysis["executions_by_status"] = statusCounts

	// Calculate step performance data
	stepPerformance := make([]map[string]interface{}, 0, len(steps))
	for _, step := range steps {
		stepData := map[string]interface{}{
			"step_id":                step.ID,
			"name":                   step.Name,
			"average_execution_time": step.AverageExecutionTime,
			"success_rate":           step.SuccessRate,
		}
		stepPerformance = append(stepPerformance, stepData)
	}
	analysis["step_performance"] = stepPerformance

	// Add performance metrics
	analysis["average_completion_time"] = workflow.AverageCompletionTime
	analysis["optimization_score"] = workflow.OptimizationScore

	return analysis, nil
}

// OptimizeWorkflow implements the workflow optimization logic
func (s *service) OptimizeWorkflow(ctx context.Context, workflowID uuid.UUID) (map[string]interface{}, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": workflowID,
	}).Info("Optimizing workflow")

	// First analyze the workflow
	analysis, err := s.AnalyzeWorkflow(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to analyze workflow: %w", err)
	}

	// Check if workflow exists
	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Set workflow status to optimizing
	previousStatus := workflow.Status
	if err := s.repo.UpdateStatus(ctx, workflowID, WorkflowStatusOptimizing); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow status to optimizing")
		// Continue with optimization even if status update fails
	}

	// Get workflow steps
	stepFilter := &WorkflowStepFilter{
		WorkflowID: &workflowID,
	}
	steps, _, err := s.repo.ListSteps(ctx, stepFilter)
	if err != nil {
		s.logger.WithError(err).Error("Failed to list workflow steps")
		return nil, fmt.Errorf("failed to list workflow steps: %w", err)
	}

	// Perform simple optimization: identify bottlenecks
	bottlenecks := make([]map[string]interface{}, 0)
	for _, step := range steps {
		if step.AverageExecutionTime > 0 && step.AverageExecutionTime > float64(len(steps))*60 {
			bottleneck := map[string]interface{}{
				"step_id":                step.ID,
				"name":                   step.Name,
				"average_execution_time": step.AverageExecutionTime,
				"recommendation":         "Consider parallelizing or optimizing this step",
			}
			bottlenecks = append(bottlenecks, bottleneck)
		}
	}

	// Prepare optimization result
	optimizationResult := map[string]interface{}{
		"workflow_id": workflowID,
		"analysis":    analysis,
		"bottlenecks": bottlenecks,
		"recommendations": []map[string]interface{}{
			{
				"type":        "general",
				"description": "Consider implementing automatic retries for failed steps",
			},
		},
	}

	// Calculate optimization score (simple example)
	optimizationScore := 0.8 // Base score
	if len(bottlenecks) > 0 {
		optimizationScore -= float64(len(bottlenecks)) * 0.1
	}
	if optimizationScore < 0.1 {
		optimizationScore = 0.1
	}

	// Update workflow with optimization data
	workflow.OptimizationScore = optimizationScore
	bottleneckData, _ := json.Marshal(bottlenecks)
	workflow.BottleneckAnalysis = datatypes.JSON(bottleneckData)

	if err := s.repo.Update(ctx, workflow); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow with optimization data")
		// Continue even if update fails
	}

	// Set workflow status back to previous status
	if err := s.repo.UpdateStatus(ctx, workflowID, previousStatus); err != nil {
		s.logger.WithError(err).Error("Failed to restore workflow status")
		// Continue even if status update fails
	}

	return optimizationResult, nil
}

// Helper methods for handler implementations
func (s *service) GetRepo() Repository {
	return s.repo
}

func (s *service) GetExecutor() WorkflowExecutor {
	return s.executor
}

// ProcessNextSteps exposes the processNextSteps functionality from the executor
func (e *DefaultWorkflowExecutor) ProcessNextSteps(ctx context.Context, currentStep *WorkflowStep, execution *WorkflowStepExecution) error {
	return e.processNextSteps(ctx, currentStep, execution)
}
