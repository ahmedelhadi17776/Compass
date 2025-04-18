package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

type HabitsRoutes struct {
	handler   *handlers.HabitsHandler
	jwtSecret string
}

func NewHabitsRoutes(handler *handlers.HabitsHandler, jwtSecret string) *HabitsRoutes {
	return &HabitsRoutes{
		handler:   handler,
		jwtSecret: jwtSecret,
	}
}

// RegisterHabitsRoutes registers all habit-related routes
func (h *HabitsRoutes) RegisterRoutes(router *gin.Engine) {
	habits := router.Group("/habits")
	habits.Use(middleware.NewAuthMiddleware(h.jwtSecret))

	// CRUD operations
	habits.POST("", h.handler.CreateHabit)
	habits.GET("/:id", h.handler.GetHabit)
	habits.PUT("/:id", h.handler.UpdateHabit)
	habits.DELETE("/:id", h.handler.DeleteHabit)

	// List and filter
	habits.GET("", h.handler.ListHabits)
	habits.GET("/due-today", h.handler.GetHabitsDueToday)

	// Habit completion
	habits.POST("/:id/complete", h.handler.MarkHabitCompleted)
	habits.POST("/:id/uncomplete", h.handler.UnmarkHabitCompleted)

	// Stats and history
	habits.GET("/:id/stats", h.handler.GetHabitStats)
	habits.GET("/:id/streak-history", h.handler.GetStreakHistory)
}
