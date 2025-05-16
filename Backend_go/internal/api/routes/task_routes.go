package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// TaskRoutes handles the setup of task-related routes
type TaskRoutes struct {
	handler   *handlers.TaskHandler
	jwtSecret string
}

// NewTaskRoutes creates a new TaskRoutes instance
func NewTaskRoutes(handler *handlers.TaskHandler, jwtSecret string) *TaskRoutes {
	return &TaskRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all task-related routes
func (r *TaskRoutes) RegisterRoutes(router *gin.Engine, cache *middleware.CacheMiddleware) {
	tasks := router.Group("/api/tasks")
	tasks.Use(middleware.NewAuthMiddleware(r.jwtSecret))

	// Read operations with caching
	tasks.GET("", cache.CacheResponse(), r.handler.ListTasks)
	tasks.GET("/:id", cache.CacheResponse(), r.handler.GetTask)
	tasks.GET("/user/:user_id", cache.CacheResponse(), r.handler.ListTasks)
	tasks.GET("/project/:project_id", cache.CacheResponse(), r.handler.GetProjectTasks)

	// Write operations with cache invalidation
	tasks.POST("", cache.CacheInvalidate("tasks:list:*"), r.handler.CreateTask)
	tasks.PUT("/:id", cache.CacheInvalidate("tasks:list:*", "tasks:id:*"), r.handler.UpdateTask)
	tasks.DELETE("/:id", cache.CacheInvalidate("tasks:list:*", "tasks:id:*"), r.handler.DeleteTask)
	tasks.PATCH("/:id/status", cache.CacheInvalidate("tasks:list:*", "tasks:id:*"), r.handler.UpdateTaskStatus)
	tasks.PATCH("/:id/assign", cache.CacheInvalidate("tasks:list:*", "tasks:id:*"), r.handler.AssignTask)

	// Task analytics routes
	analytics := tasks.Group("/analytics")

	// User-specific analytics
	analytics.GET("/user", r.handler.GetUserTaskAnalytics)
	analytics.GET("/user/summary", r.handler.GetUserTaskActivitySummary)

	// Task-specific analytics
	tasks.GET("/:id/analytics", r.handler.GetTaskAnalytics)
	tasks.GET("/:id/analytics/summary", r.handler.GetTaskActivitySummary)
	tasks.POST("/:id/analytics/record", r.handler.RecordTaskActivity)
}
