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

// RegisterRoutes registers all habit-related routes
// @Summary Register habits routes
// @Description Register all habit-related routes with their handlers
// @Tags habits
// @Security BearerAuth
func (h *HabitsRoutes) RegisterRoutes(router *gin.Engine, cache *middleware.CacheMiddleware) {
	habits := router.Group("/api/habits")
	habits.Use(middleware.NewAuthMiddleware(h.jwtSecret))

	// List and filter - specific routes first
	habits.GET("", cache.CacheResponse(), h.handler.ListHabits)
	habits.POST("", cache.CacheInvalidate("habits:*"), h.handler.CreateHabit)
	habits.GET("/heatmap", cache.CacheResponse(), h.handler.GetHabitHeatmap)
	habits.GET("/due-today", cache.CacheResponse(), h.handler.GetHabitsDueToday)
	habits.GET("/user/:user_id", cache.CacheResponse(), h.handler.GetUserHabits)

	// CRUD operations with parameters
	habits.GET("/:id", cache.CacheResponse(), h.handler.GetHabit)
	habits.PUT("/:id", cache.CacheInvalidate("habits:*"), h.handler.UpdateHabit)
	habits.DELETE("/:id", cache.CacheInvalidate("habits:*"), h.handler.DeleteHabit)

	// Habit completion routes
	habits.POST("/:id/complete", cache.CacheInvalidate("habits:*"), h.handler.MarkHabitCompleted)
	habits.POST("/:id/uncomplete", cache.CacheInvalidate("habits:*"), h.handler.UnmarkHabitCompleted)
	habits.GET("/:id/stats", cache.CacheResponse(), h.handler.GetHabitStats)
	habits.GET("/:id/streak-history", cache.CacheResponse(), h.handler.GetStreakHistory)
}
