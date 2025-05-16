package routes

import (
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
	"github.com/gin-gonic/gin"
)

// NotificationRoutes manages notification endpoint routes
type NotificationRoutes struct {
	handler     *handlers.NotificationHandler
	jwtSecret   string
	rateLimiter auth.RateLimiter
}

// NewNotificationRoutes creates a new notification routes handler
func NewNotificationRoutes(handler *handlers.NotificationHandler, jwtSecret string, rateLimiter auth.RateLimiter) *NotificationRoutes {
	return &NotificationRoutes{
		handler:     handler,
		jwtSecret:   jwtSecret,
		rateLimiter: rateLimiter,
	}
}

// RegisterRoutes registers notification routes with the provided router
func (r *NotificationRoutes) RegisterRoutes(router *gin.Engine, cacheMiddleware *middleware.CacheMiddleware) {
	// Create a route group with authentication middleware
	authMiddleware := middleware.JWTAuthMiddleware(r.jwtSecret)

	// Apply moderate rate limiting to notification endpoints (more requests allowed than auth endpoints)
	notificationRateLimiter := middleware.RateLimitMiddleware(r.rateLimiter.WithLimit(120, time.Minute))

	// Notification routes
	notificationRoutes := router.Group("/api/notifications")
	notificationRoutes.Use(authMiddleware)
	notificationRoutes.Use(notificationRateLimiter)
	{
		// GET endpoints
		notificationRoutes.GET("", cacheMiddleware.CachePageWithTTL("notifications", 30*time.Second), r.handler.GetAll)
		notificationRoutes.GET("/unread", r.handler.GetUnread) // No cache for unread - always fresh
		notificationRoutes.GET("/count", r.handler.CountUnread)
		notificationRoutes.GET("/:id", cacheMiddleware.CachePageWithTTL("notification", 1*time.Minute), r.handler.GetByID)

		// PUT endpoints
		notificationRoutes.PUT("/:id/read", r.handler.MarkAsRead)
		notificationRoutes.PUT("/read-all", r.handler.MarkAllAsRead)

		// DELETE endpoint
		notificationRoutes.DELETE("/:id", r.handler.Delete)

		// POST endpoint (typically for admin or system use)
		notificationRoutes.POST("", r.handler.Create)

		// WebSocket endpoint (no cache, real-time)
		notificationRoutes.GET("/ws", r.handler.WebSocketHandler)
	}
}
