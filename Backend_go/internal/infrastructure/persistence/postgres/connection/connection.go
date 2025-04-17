package connection

import (
	"fmt"
	"time"

	"github.com/ahmedelhadi17776/Compass/Backend_go/pkg/config"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Database struct {
	*gorm.DB
}

func NewDatabase(cfg *config.Config) (*Database, error) {
	dsn := fmt.Sprintf(
		"host=%s user=%s password=%s dbname=%s port=%d sslmode=%s",
		cfg.Database.Host,
		cfg.Database.User,
		cfg.Database.Password,
		cfg.Database.Name,
		cfg.Database.Port,
		cfg.Database.SSLMode,
	)

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		PrepareStmt: true,
	})
	if err != nil {
		return nil, fmt.Errorf("failed to connect to database: %w", err)
	}

	sqlDB, err := db.DB()
	if err != nil {
		return nil, err
	}

	// Configure connection pool using config values
	sqlDB.SetMaxIdleConns(cfg.Database.MaxIdleConns)
	sqlDB.SetMaxOpenConns(cfg.Database.MaxOpenConns)

	// Parse and set connection max lifetime
	lifetime, err := time.ParseDuration(cfg.Database.ConnMaxLifetime)
	if err != nil {
		lifetime = time.Hour // default to 1 hour if parsing fails
	}
	sqlDB.SetConnMaxLifetime(lifetime)

	return &Database{db}, nil
}
