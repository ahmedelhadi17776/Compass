package migrations

import (
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/task"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/user"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/project"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/domain/organization"
	"github.com/ahmedelhadi17776/Compass/Backend_go/internal/infrastructure/persistence/postgres/connection"
	"go.uber.org/zap"
)

// AutoMigrate runs database migrations for all models
func AutoMigrate(db *connection.Database, logger *zap.Logger) error {
	logger.Info("Running database migrations...")

	// Enable UUID extension for PostgreSQL
	if err := db.Exec(`CREATE EXTENSION IF NOT EXISTS "uuid-ossp";`).Error; err != nil {
		logger.Error("Failed to create UUID extension", zap.Error(err))
		return err
	}

	// Auto-migrate all models
	if err := db.AutoMigrate(
		&user.User{},
		&task.Task{},
		&project.Project{},
		&organization.Organization{},
	); err != nil {
		logger.Error("Failed to run migrations", zap.Error(err))
		return err
	}

	logger.Info("Database migrations completed successfully")
	return nil
}
