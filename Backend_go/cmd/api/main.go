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

	_ "github.com/ahmedelhadi17776/Compass/Backend_go/docs" // swagger docs
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/handlers"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/routes"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/project"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/migrations"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/config"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
	"go.uber.org/zap"
)

// @title           Compass API
// @version         1.0
// @description     A task management API with user authentication and authorization.
// @termsOfService  http://swagger.io/terms/

// @contact.name   API Support
// @contact.url    http://www.swagger.io/support
// @contact.email  support@swagger.io

// @host      localhost:8000
// @BasePath  /api

// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization
// @description Type "Bearer" followed by a space and JWT token.

// RequestLoggerMiddleware logs all incoming HTTP requests
func RequestLoggerMiddleware(log *logger.Logger) gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		method := c.Request.Method

		log.Info("Request started",
			zap.String("path", path),
			zap.String("method", method),
			zap.String("client_ip", c.ClientIP()),
		)

		c.Next()

		log.Info("Request completed",
			zap.String("path", path),
			zap.String("method", method),
			zap.Int("status", c.Writer.Status()),
			zap.Duration("latency", time.Since(start)),
		)
	}
}

func main() {
	// Load configuration
	cfg, err := config.LoadConfig("") // Empty string will make it search in default locations
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	// Initialize logger
	log := logger.NewLogger()
	defer log.Sync()

	log.Info("Configuration loaded successfully")
	log.Info("Server mode: " + cfg.Server.Mode)

	// Set up Gin
	if cfg.Server.Mode == "production" {
		gin.SetMode(gin.ReleaseMode)
	} else {
		gin.SetMode(gin.DebugMode)
	}

	router := gin.New()

	// Add middleware
	router.Use(gin.Recovery())
	router.Use(RequestLoggerMiddleware(log))
	router.Use(cors.New(cors.Config{
		AllowOrigins:     cfg.CORS.AllowedOrigins,
		AllowMethods:     cfg.CORS.AllowedMethods,
		AllowHeaders:     cfg.CORS.AllowedHeaders,
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: cfg.CORS.AllowCredentials,
		MaxAge:           12 * time.Hour,
	}))

	// Connect to database
	db, err := connection.NewDatabase(cfg)
	if err != nil {
		log.Fatal("Failed to connect to database", zap.Error(err))
	}

	// Run database migrations
	if err := migrations.AutoMigrate(db, log.Logger); err != nil {
		log.Fatal("Failed to run database migrations", zap.Error(err))
	}

	// Initialize repositories
	taskRepo := task.NewRepository(db)
	userRepo := user.NewRepository(db)
	projectRepo := project.NewRepository(db)

	// Initialize services
	taskService := task.NewService(taskRepo)
	userService := user.NewService(userRepo)
	projectService := project.NewService(projectRepo)

	// Initialize handlers
	userHandler := handlers.NewUserHandler(userService)
	taskHandler := handlers.NewTaskHandler(taskService)
	projectHandler := handlers.NewProjectHandler(projectService)

	// Debug: Print all registered routes
	log.Info("Registering routes...")

	// Swagger documentation endpoint
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	log.Info("Registered swagger route at /swagger/*")

	// Set up user routes
	userRoutes := routes.NewUserRoutes(userHandler, cfg.Auth.JWTSecret)
	userRoutes.RegisterRoutes(router)
	log.Info("Registered user routes at /api/users")

	// Health check routes (no /api prefix as these are system endpoints)
	router.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"timestamp": time.Now().UTC(),
		})
	})
	router.GET("/health/ready", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":    "ready",
			"timestamp": time.Now().UTC(),
		})
	})
	log.Info("Registered health check routes at /health and /health/ready")

	// Task routes (protected)
	taskRoutes := routes.NewTaskRoutes(taskHandler, cfg.Auth.JWTSecret)
	taskRoutes.RegisterRoutes(router)
	log.Info("Registered task routes at /api/tasks")

	// Project routes (protected)
	projectRoutes := routes.NewProjectRoutes(projectHandler, cfg.Auth.JWTSecret)
	projectRoutes.RegisterRoutes(router)
	log.Info("Registered project routes at /api/projects")

	// Print all registered routes for debugging
	for _, route := range router.Routes() {
		log.Info("Route registered",
			zap.String("method", route.Method),
			zap.String("path", route.Path),
		)
	}

	// Start server
	server := &http.Server{
		Addr:    fmt.Sprintf(":%d", cfg.Server.Port),
		Handler: router,
	}

	// Graceful shutdown
	go func() {
		log.Info(fmt.Sprintf("Server starting on port %d", cfg.Server.Port))
		log.Info("Swagger documentation available at http://localhost:8000/swagger/index.html")
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("Failed to start server", zap.Error(err))
		}
	}()

	// Wait for interrupt signal
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	// Shutdown with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	log.Info("Shutting down server...")
	if err := server.Shutdown(ctx); err != nil {
		log.Fatal("Server forced to shutdown", zap.Error(err))
	}

	log.Info("Server exited properly")
}
