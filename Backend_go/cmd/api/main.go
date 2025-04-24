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
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/middleware"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/api/routes"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/calendar"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/habits"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/organization"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/project"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/roles"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/todos"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/workflow"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/cache"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/migrations"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/config"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/logger"
	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/security/auth"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"
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
// @BasePath

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

	// Initialize logrus logger for workflow service
	workflowLogger := logrus.New()
	workflowLogger.SetFormatter(&logrus.JSONFormatter{})
	if cfg.Server.Mode == "production" {
		workflowLogger.SetLevel(logrus.InfoLevel)
	} else {
		workflowLogger.SetLevel(logrus.DebugLevel)
	}

	// Initialize repositories
	taskRepo := task.NewRepository(db)
	userRepo := user.NewRepository(db)
	projectRepo := project.NewRepository(db)
	organizationRepo := organization.NewRepository(db)
	rolesRepo := roles.NewRepository(db.DB)
	habitsRepo := habits.NewRepository(db)
	calendarRepo := calendar.NewRepository(db.DB)
	workflowRepo := workflow.NewRepository(db.DB, workflowLogger)
	todosRepo := todos.NewTodoRepository(db)

	// Initialize Redis
	redisConfig := cache.NewConfigFromEnv(cfg)
	redisClient, err := cache.NewRedisClient(redisConfig)
	if err != nil {
		log.Fatal("Failed to connect to Redis", zap.Error(err))
	}
	defer redisClient.Close()

	// Initialize rate limiter with Redis client
	rateLimiter := auth.NewRedisRateLimiter(redisClient.GetClient(), 1*time.Minute, 100)

	// Create cache middleware
	cacheMiddleware := middleware.NewCacheMiddleware(redisClient, "compass", 5*time.Minute)

	// Initialize services
	rolesService := roles.NewService(rolesRepo)
	userService := user.NewService(userRepo, rolesService)
	taskService := task.NewService(taskRepo)
	projectService := project.NewService(projectRepo)
	organizationService := organization.NewService(organizationRepo)
	habitsService := habits.NewService(habitsRepo)
	calendarService := calendar.NewService(calendarRepo)
	workflowService := workflow.NewService(workflow.ServiceConfig{
		Repository: workflowRepo,
		Logger:     workflowLogger,
	})
	todosService := todos.NewService(todosRepo)

	// Initialize handlers
	userHandler := handlers.NewUserHandler(userService, cfg.Auth.JWTSecret)
	taskHandler := handlers.NewTaskHandler(taskService)
	authHandler := handlers.NewAuthHandler(rolesService)
	projectHandler := handlers.NewProjectHandler(projectService)
	organizationHandler := handlers.NewOrganizationHandler(organizationService)
	habitsHandler := handlers.NewHabitsHandler(habitsService)
	calendarHandler := handlers.NewCalendarHandler(calendarService)
	workflowHandler := handlers.NewWorkflowHandler(workflowService)
	todosHandler := handlers.NewTodoHandler(todosService)

	// Debug: Print all registered routes
	log.Info("Registering routes...")

	// Swagger documentation endpoint
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	log.Info("Registered swagger route at /swagger/*")

	// Set up user routes
	userRoutes := routes.NewUserRoutes(userHandler, cfg.Auth.JWTSecret, rateLimiter)
	userRoutes.RegisterRoutes(router)
	log.Info("Registered user routes at /api/users")

	// Set up auth routes
	authRoutes := routes.NewAuthRoutes(authHandler, cfg.Auth.JWTSecret)
	authRoutes.RegisterRoutes(router)
	log.Info("Registered auth routes at /api/roles")

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

	// Add cache health check
	router.GET("/health/cache", func(c *gin.Context) {
		if err := redisClient.HealthCheck(c); err != nil {
			c.JSON(http.StatusServiceUnavailable, gin.H{
				"status":    "unhealthy",
				"component": "cache",
				"error":     err.Error(),
			})
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"status":    "healthy",
			"component": "cache",
			"metrics":   redisClient.GetMetrics(),
		})
	})

	// Apply rate limiting middleware globally
	router.Use(middleware.RateLimitMiddleware(rateLimiter))

	// Task routes (protected)
	taskRoutes := routes.NewTaskRoutes(taskHandler, cfg.Auth.JWTSecret)
	taskRoutes.RegisterRoutes(router, cacheMiddleware)
	log.Info("Registered task routes at /api/tasks")

	// Project routes (protected)
	projectRoutes := routes.NewProjectRoutes(projectHandler, cfg.Auth.JWTSecret)
	projectRoutes.RegisterRoutes(router, cacheMiddleware)
	log.Info("Registered project routes at /api/projects")

	// Organization routes (protected)
	organizationRoutes := routes.NewOrganizationRoutes(organizationHandler, cfg.Auth.JWTSecret)
	organizationRoutes.RegisterRoutes(router)
	log.Info("Registered organization routes at /api/organizations")

	// Habits routes (protected)
	habitsRoutes := routes.NewHabitsRoutes(habitsHandler, cfg.Auth.JWTSecret)
	habitsRoutes.RegisterRoutes(router)
	log.Info("Registered habits routes at /habits")

	// Calendar routes (protected)
	calendarRoutes := routes.NewCalendarRoutes(calendarHandler, cfg.Auth.JWTSecret)
	calendarRoutes.RegisterRoutes(router)
	log.Info("Registered calendar routes at /api/calendar")

	// Workflow routes (protected)
	workflowRoutes := routes.NewWorkflowRoutes(workflowHandler, cfg.Auth.JWTSecret)
	workflowRoutes.RegisterRoutes(router)
	log.Info("Registered workflow routes at /api/workflows")

	// Todos routes (protected)
	todosRoutes := routes.NewTodosRoutes(todosHandler, cfg.Auth.JWTSecret)
	todosRoutes.RegisterRoutes(router, cacheMiddleware)
	log.Info("Registered todos routes at /api/todos")

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
