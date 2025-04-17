package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/ahmedelhadi17776/Compass/Backend_go/docs" // This will be created by swag
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/routes"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/config"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	"go.uber.org/zap"
)


func main() {
	// Load configuration
	cfg, err := config.LoadConfig("") // Empty string will make it search in default locations
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize logger
	logger := logger.NewLogger()
	defer logger.Sync()

	logger.Info("Configuration loaded successfully")
	logger.Info(fmt.Sprintf("Server mode: %s", cfg.Server.Mode))

	// Connect to database
	db, err := connection.NewDatabase(cfg)
	if err != nil {
		logger.Fatal("Failed to connect to database", zap.Error(err))
	}

	// Initialize repositories
	taskRepo := task.NewRepository(db)
	userRepo := user.NewRepository(db)

	// Initialize services
	taskService := task.NewService(taskRepo)
	userService := user.NewService(userRepo)

	// Set up Gin
	if cfg.Server.Mode == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(gin.Recovery())

	// Setup API routes
	api := router.Group("/api")
	routes.SetupTaskRoutes(api, taskService)
	routes.SetupUserRoutes(api, userService)

	// Swagger documentation endpoint
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// Start server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Server.Port),
		Handler: router,
	}

	// Graceful shutdown
	go func() {
		logger.Info(fmt.Sprintf("Server started on port %d", cfg.Server.Port))
		logger.Info("Swagger documentation available at http://localhost:8000/swagger/index.html")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	// Shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	logger.Info("Shutting down server...")
	if err := server.Shutdown(ctx); err != nil {
		logger.Fatal("Server forced to shutdown", zap.Error(err))
	}

	logger.Info("Server exited properly")
}
