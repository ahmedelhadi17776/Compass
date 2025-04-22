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
	s.logger.WithField("workflow_id", id).Info("Updating workflow")

	workflow, err := s.repo.GetByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow")
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Update fields if provided in the request
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

	workflow.UpdatedAt = time.Now().UTC()

	if err := s.repo.Update(ctx, workflow); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow")
		return nil, fmt.Errorf("failed to update workflow: %w", err)
	}

	return &WorkflowResponse{Workflow: workflow}, nil
}

// DeleteWorkflow implements the workflow deletion logic
func (s *service) DeleteWorkflow(ctx context.Context, id uuid.UUID) error {
	s.logger.WithField("workflow_id", id).Info("Deleting workflow")

	// First, cancel any active executions
	if err := s.repo.CancelActiveExecutions(ctx, id); err != nil {
		s.logger.WithError(err).Error("Failed to cancel active executions")
		return fmt.Errorf("failed to cancel active executions: %w", err)
	}

	if err := s.repo.Delete(ctx, id); err != nil {
		s.logger.WithError(err).Error("Failed to delete workflow")
		return fmt.Errorf("failed to delete workflow: %w", err)
	}

	return nil
}

// GetWorkflow retrieves a workflow by ID
func (s *service) GetWorkflow(ctx context.Context, id uuid.UUID) (*WorkflowResponse, error) {
	workflow, err := s.repo.GetByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow")
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	return &WorkflowResponse{Workflow: workflow}, nil
}

// ListWorkflows retrieves workflows based on filter criteria
func (s *service) ListWorkflows(ctx context.Context, filter *WorkflowFilter) (*WorkflowListResponse, error) {
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

// AddWorkflowStep adds a new step to a workflow
func (s *service) AddWorkflowStep(ctx context.Context, workflowID uuid.UUID, req CreateWorkflowStepRequest) (*WorkflowStepResponse, error) {
	s.logger.WithFields(logrus.Fields{
		"workflow_id": workflowID,
		"step_name":   req.Name,
	}).Info("Adding workflow step")

	// Verify workflow exists and is in a valid state
	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	if workflow.Status != WorkflowStatusPending && workflow.Status != WorkflowStatusActive {
		return nil, fmt.Errorf("cannot add steps to workflow in %s status", workflow.Status)
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
		Timeout:     req.Timeout,
		IsRequired:  true,
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

	return &WorkflowStepResponse{Step: step}, nil
}

// UpdateWorkflowStep updates an existing workflow step
func (s *service) UpdateWorkflowStep(ctx context.Context, id uuid.UUID, req UpdateWorkflowStepRequest) (*WorkflowStepResponse, error) {
	s.logger.WithField("step_id", id).Info("Updating workflow step")

	step, err := s.repo.GetStepByID(ctx, id)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow step: %w", err)
	}

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

	return &WorkflowStepResponse{Step: step}, nil
}

// DeleteWorkflowStep deletes a workflow step
func (s *service) DeleteWorkflowStep(ctx context.Context, id uuid.UUID) error {
	s.logger.WithField("step_id", id).Info("Deleting workflow step")

	if err := s.repo.DeleteStep(ctx, id); err != nil {
		s.logger.WithError(err).Error("Failed to delete workflow step")
		return fmt.Errorf("failed to delete workflow step: %w", err)
	}

	return nil
}

// GetWorkflowStep retrieves a workflow step by ID
func (s *service) GetWorkflowStep(ctx context.Context, id uuid.UUID) (*WorkflowStepResponse, error) {
	step, err := s.repo.GetStepByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow step")
		return nil, fmt.Errorf("failed to get workflow step: %w", err)
	}

	return &WorkflowStepResponse{Step: step}, nil
}

// ListWorkflowSteps retrieves workflow steps based on filter criteria
func (s *service) ListWorkflowSteps(ctx context.Context, filter *WorkflowStepFilter) (*WorkflowStepListResponse, error) {
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

// ExecuteWorkflow starts the execution of a workflow
func (s *service) ExecuteWorkflow(ctx context.Context, workflowID uuid.UUID) (*WorkflowExecutionResponse, error) {
	s.logger.WithField("workflow_id", workflowID).Info("Starting workflow execution")

	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Create new execution record
	execution := &WorkflowExecution{
		ID:         uuid.New(),
		WorkflowID: workflowID,
		Status:     WorkflowStatusActive,
		StartedAt:  time.Now().UTC(),
		ExecutionMetadata: map[string]interface{}{
			"started_by": workflow.CreatedBy.String(),
			"version":    workflow.Version,
		},
	}

	if err := s.repo.CreateExecution(ctx, execution); err != nil {
		s.logger.WithError(err).Error("Failed to create workflow execution")
		return nil, fmt.Errorf("failed to create workflow execution: %w", err)
	}

	// Update workflow status
	workflow.Status = WorkflowStatusActive
	workflow.LastExecutedAt = &execution.StartedAt
	if err := s.repo.Update(ctx, workflow); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow status")
		return nil, fmt.Errorf("failed to update workflow status: %w", err)
	}

	return &WorkflowExecutionResponse{Execution: execution}, nil
}

// ExecuteWorkflowStep executes a specific step in a workflow
func (s *service) ExecuteWorkflowStep(ctx context.Context, stepID uuid.UUID, executionID uuid.UUID) (*WorkflowStepExecution, error) {
	s.logger.WithFields(logrus.Fields{
		"step_id":      stepID,
		"execution_id": executionID,
	}).Info("Executing workflow step")

	step, err := s.repo.GetStepByID(ctx, stepID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow step: %w", err)
	}

	stepExecution := &WorkflowStepExecution{
		ID:          uuid.New(),
		ExecutionID: executionID,
		StepID:      stepID,
		Status:      StepStatusActive,
		StartedAt:   time.Now().UTC(),
		ExecutionMetadata: map[string]interface{}{
			"step_type": step.StepType,
			"version":   step.Version,
		},
	}

	if err := s.repo.CreateStepExecution(ctx, stepExecution); err != nil {
		s.logger.WithError(err).Error("Failed to create step execution")
		return nil, fmt.Errorf("failed to create step execution: %w", err)
	}

	// Execute the step using the executor
	if err := s.executor.ExecuteStep(ctx, step, stepExecution); err != nil {
		s.logger.WithError(err).Error("Failed to execute step")
		stepExecution.Status = StepStatusFailed
		errStr := err.Error()
		stepExecution.Error = &errStr
		stepExecution.CompletedAt = timePtr(time.Now().UTC())
		_ = s.repo.UpdateStepExecution(ctx, stepExecution)
		return nil, fmt.Errorf("failed to execute step: %w", err)
	}

	return stepExecution, nil
}

// CancelWorkflowExecution cancels an active workflow execution
func (s *service) CancelWorkflowExecution(ctx context.Context, workflowID uuid.UUID) error {
	s.logger.WithField("workflow_id", workflowID).Info("Cancelling workflow execution")

	if err := s.repo.CancelActiveExecutions(ctx, workflowID); err != nil {
		s.logger.WithError(err).Error("Failed to cancel workflow execution")
		return fmt.Errorf("failed to cancel workflow execution: %w", err)
	}

	// Update workflow status
	if err := s.repo.UpdateStatus(ctx, workflowID, WorkflowStatusCancelled); err != nil {
		s.logger.WithError(err).Error("Failed to update workflow status")
		return fmt.Errorf("failed to update workflow status: %w", err)
	}

	return nil
}

// GetWorkflowExecution retrieves a workflow execution by ID
func (s *service) GetWorkflowExecution(ctx context.Context, id uuid.UUID) (*WorkflowExecutionResponse, error) {
	execution, err := s.repo.GetExecutionByID(ctx, id)
	if err != nil {
		s.logger.WithError(err).Error("Failed to get workflow execution")
		return nil, fmt.Errorf("failed to get workflow execution: %w", err)
	}

	return &WorkflowExecutionResponse{Execution: execution}, nil
}

// ListWorkflowExecutions retrieves workflow executions based on filter criteria
func (s *service) ListWorkflowExecutions(ctx context.Context, filter *WorkflowExecutionFilter) (*WorkflowExecutionListResponse, error) {
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

// AnalyzeWorkflow performs analysis on a workflow
func (s *service) AnalyzeWorkflow(ctx context.Context, workflowID uuid.UUID) (map[string]interface{}, error) {
	s.logger.WithField("workflow_id", workflowID).Info("Analyzing workflow")

	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Get workflow executions for analysis
	executions, _, err := s.repo.ListExecutions(ctx, &WorkflowExecutionFilter{
		WorkflowID: &workflowID,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow executions: %w", err)
	}

	// Perform analysis
	analysis := map[string]interface{}{
		"total_executions":     len(executions),
		"average_success_rate": workflow.SuccessRate,
		"optimization_score":   workflow.OptimizationScore,
		"bottlenecks":          workflow.BottleneckAnalysis,
		"performance_metrics": map[string]interface{}{
			"average_completion_time": workflow.AverageCompletionTime,
			"estimated_vs_actual":     calculateEfficiencyRatio(workflow),
		},
	}

	return analysis, nil
}

// OptimizeWorkflow performs optimization on a workflow
func (s *service) OptimizeWorkflow(ctx context.Context, workflowID uuid.UUID) (map[string]interface{}, error) {
	s.logger.WithField("workflow_id", workflowID).Info("Optimizing workflow")

	workflow, err := s.repo.GetByID(ctx, workflowID)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow: %w", err)
	}

	// Update workflow status
	workflow.Status = WorkflowStatusOptimizing
	if err := s.repo.Update(ctx, workflow); err != nil {
		return nil, fmt.Errorf("failed to update workflow status: %w", err)
	}

	// Perform optimization analysis
	optimization := map[string]interface{}{
		"optimization_score": calculateOptimizationScore(workflow),
		"recommendations":    generateOptimizationRecommendations(workflow),
		"metrics": map[string]interface{}{
			"performance_impact": estimatePerformanceImpact(workflow),
			"resource_savings":   estimateResourceSavings(workflow),
		},
	}

	// Update workflow with optimization results
	workflow.Status = WorkflowStatusActive
	workflow.OptimizationScore = optimization["optimization_score"].(float64)
	if err := s.repo.Update(ctx, workflow); err != nil {
		return nil, fmt.Errorf("failed to update workflow with optimization results: %w", err)
	}

	return optimization, nil
}

// Helper functions

func timePtr(t time.Time) *time.Time {
	return &t
}

func calculateEfficiencyRatio(w *Workflow) float64 {
	if w.EstimatedDuration == nil || w.ActualDuration == nil || *w.EstimatedDuration == 0 {
		return 0
	}
	return float64(*w.ActualDuration) / float64(*w.EstimatedDuration)
}

func calculateOptimizationScore(w *Workflow) float64 {
	// Implementation of optimization score calculation
	// This should take into account various metrics like execution time, success rate, etc.
	return w.SuccessRate*0.4 + (1-calculateEfficiencyRatio(w))*0.6
}

func generateOptimizationRecommendations(w *Workflow) []string {
	var recommendations []string

	// Add recommendations based on workflow analysis
	if w.SuccessRate < 0.8 {
		recommendations = append(recommendations, "Consider adding more error handling and retry mechanisms")
	}
	if calculateEfficiencyRatio(w) > 1.2 {
		recommendations = append(recommendations, "Workflow is taking longer than estimated, consider optimizing step execution")
	}
	if w.AIEnabled && w.AIConfidenceThreshold < 0.7 {
		recommendations = append(recommendations, "Consider increasing AI confidence threshold for better accuracy")
	}

	return recommendations
}

func estimatePerformanceImpact(w *Workflow) float64 {
	// Implementation of performance impact estimation
	return (1 - w.SuccessRate) * calculateEfficiencyRatio(w)
}

func estimateResourceSavings(w *Workflow) float64 {
	// Implementation of resource savings estimation
	if w.EstimatedDuration == nil || w.ActualDuration == nil {
		return 0
	}
	return float64(*w.EstimatedDuration-*w.ActualDuration) / float64(*w.EstimatedDuration)
}
