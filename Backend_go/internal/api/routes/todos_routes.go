package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

// TodosRoutes handles the setup of todo-related routes
type TodosRoutes struct {
	handler   *handlers.TodoHandler
	jwtSecret string
}

// NewTodosRoutes creates a new TodosRoutes instance
func NewTodosRoutes(handler *handlers.TodoHandler, jwtSecret string) *TodosRoutes {
	return &TodosRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterRoutes registers all todo-related routes
func (r *TodosRoutes) RegisterRoutes(router *gin.Engine, cache *middleware.CacheMiddleware) {
	todos := router.Group("/api/todos")
	todos.Use(middleware.NewAuthMiddleware(r.jwtSecret))

	// Read operations with caching
	todos.GET("", cache.CacheResponse(), r.handler.ListTodos)
	todos.GET("/:id", cache.CacheResponse(), r.handler.GetTodo)

	// Write operations with cache invalidation
	todos.POST("", cache.CacheInvalidate("todos:list:*"), r.handler.CreateTodo)
	todos.PUT("/:id", cache.CacheInvalidate("todos:list:*", "todos:id:*"), r.handler.UpdateTodo)
	todos.DELETE("/:id", cache.CacheInvalidate("todos:list:*", "todos:id:*"), r.handler.DeleteTodo)

	// Status and priority updates
	todos.PATCH("/:id/status", cache.CacheInvalidate("todos:list:*", "todos:id:*"), r.handler.UpdateTodoStatus)
	todos.PATCH("/:id/priority", cache.CacheInvalidate("todos:list:*", "todos:id:*"), r.handler.UpdateTodoPriority)

	// Completion status
	todos.PATCH("/:id/complete", cache.CacheInvalidate("todos:list:*", "todos:id:*"), r.handler.CompleteTodo)
	todos.PATCH("/:id/uncomplete", cache.CacheInvalidate("todos:list:*", "todos:id:*"), r.handler.UncompleteTodo)

	// Todo Lists routes
	todoLists := router.Group("/api/todo-lists")
	todoLists.Use(middleware.NewAuthMiddleware(r.jwtSecret))
	todoLists.POST("", cache.CacheInvalidate("todo-lists:*"), r.handler.CreateTodoList)
}
