package routes

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/gin-gonic/gin"
)

type DashboardRoutes struct {
	handler   *handlers.DashboardHandler
	jwtSecret string
}

func NewDashboardRoutes(handler *handlers.DashboardHandler, jwtSecret string) *DashboardRoutes {
	return &DashboardRoutes{handler: handler, jwtSecret: jwtSecret}
}

func (r *DashboardRoutes) RegisterRoutes(router *gin.Engine) {
	dashboard := router.Group("/api/dashboard")
	dashboard.Use(middleware.NewAuthMiddleware(r.jwtSecret))
	dashboard.GET("/metrics", r.handler.GetDashboardMetrics)
}
