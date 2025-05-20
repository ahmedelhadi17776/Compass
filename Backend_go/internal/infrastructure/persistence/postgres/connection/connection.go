package connection

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/config"
	"github.com/lib/pq"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
	"gorm.io/gorm/logger"
)

type Database struct {
	*gorm.DB
}

func NewDatabase(cfg *config.Config) (*Database, error) {
	// First try to establish a basic SQL connection
	sqlDB, err := sql.Open("postgres", fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		cfg.Database.Host,
		cfg.Database.Port,
		cfg.Database.User,
		cfg.Database.Password,
		cfg.Database.Name,
	))
	if err != nil {
		return nil, fmt.Errorf("failed to create sql.DB: %w", err)
	}

	// Test the connection
	err = sqlDB.Ping()
	if err != nil {
		sqlErr, ok := err.(*pq.Error)
		if ok {
			return nil, fmt.Errorf("postgres error: code=%s, message=%s, detail=%s", sqlErr.Code, sqlErr.Message, sqlErr.Detail)
		}
		return nil, fmt.Errorf("failed to ping database: %w", err)
	}

	// Close the test connection
	sqlDB.Close()

	// Now set up GORM with detailed logging
	gormConfig := &gorm.Config{
		Logger: logger.Default.LogMode(logger.Info),
	}

	dsn := fmt.Sprintf(
		"host=%s port=%d user=%s password=%s dbname=%s sslmode=disable",
		cfg.Database.Host,
		cfg.Database.Port,
		cfg.Database.User,
		cfg.Database.Password,
		cfg.Database.Name,
	)

	db, err := gorm.Open(postgres.Open(dsn), gormConfig)
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database with GORM: %w", err)
	}

	// Get the underlying *sql.DB
	sqlDB, err = db.DB()
	if err != nil {
		return nil, fmt.Errorf("failed to get underlying *sql.DB: %w", err)
	}

	// Configure connection pool
	sqlDB.SetMaxIdleConns(cfg.Database.MaxIdleConns)
	sqlDB.SetMaxOpenConns(cfg.Database.MaxOpenConns)
	sqlDB.SetConnMaxLifetime(time.Hour)

	return &Database{db}, nil
}
