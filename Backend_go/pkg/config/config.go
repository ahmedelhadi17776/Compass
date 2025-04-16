package config

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strconv"

	"github.com/spf13/viper"
)

type Config struct {
	Server struct {
		Port int    `mapstructure:"port"`
		Mode string `mapstructure:"mode"`
	} `mapstructure:"server"`

	Database struct {
		Host            string `mapstructure:"host"`
		Port            int    `mapstructure:"port"`
		User            string `mapstructure:"user"`
		Password        string `mapstructure:"password"`
		Name            string `mapstructure:"name"`
		SSLMode         string `mapstructure:"sslmode"`
		MaxOpenConns    int    `mapstructure:"max_open_conns"`
		MaxIdleConns    int    `mapstructure:"max_idle_conns"`
		ConnMaxLifetime string `mapstructure:"conn_max_lifetime"`
	} `mapstructure:"database"`

	Redis struct {
		Host     string `mapstructure:"host"`
		Port     int    `mapstructure:"port"`
		Password string `mapstructure:"password"`
		DB       int    `mapstructure:"db"`
	} `mapstructure:"redis"`

	Auth struct {
		JWTSecret        string `mapstructure:"jwt_secret"`
		TokenExpiryHours int    `mapstructure:"token_expiry_hours"`
		Issuer           string `mapstructure:"issuer"`
	} `mapstructure:"auth"`
}

func getEnv(key, fallback string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return fallback
}

func LoadConfig(configPath string) (*Config, error) {
	var config Config

	// Get the directory of the current file (config.go)
	_, filename, _, _ := runtime.Caller(0)
	pkgConfigDir := filepath.Dir(filename)

	// Get the project root directory (two levels up from pkg/config)
	projectRoot := filepath.Join(pkgConfigDir, "..", "..")
	projectRoot, err := filepath.Abs(projectRoot)
	if err != nil {
		return nil, fmt.Errorf("failed to get project root: %v", err)
	}

	// Add config paths
	searchPaths := []string{
		pkgConfigDir, // pkg/config/
		projectRoot,  // Project root
		filepath.Join(projectRoot, "pkg", "config"), // pkg/config from root
	}

	if configPath != "" {
		searchPaths = append([]string{configPath}, searchPaths...)
	}

	// Add all search paths to viper
	for _, path := range searchPaths {
		viper.AddConfigPath(path)
	}

	// Set default values from environment variables first
	viper.SetDefault("database.host", getEnv("DB_HOST", "localhost"))
	viper.SetDefault("database.port", getEnv("DB_PORT", "5432"))
	viper.SetDefault("database.user", getEnv("DB_USER", "ahmed"))
	viper.SetDefault("database.password", getEnv("DB_PASSWORD", ""))
	viper.SetDefault("database.name", getEnv("DB_NAME", "compass"))
	viper.SetDefault("database.sslmode", getEnv("DB_SSLMODE", "disable"))
	viper.SetDefault("auth.jwt_secret", getEnv("JWT_SECRET", "a82552a2c8133eddce94cc781f716cdcb911d065528783a8a75256aff6731886"))

	// Load main config file
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("error loading config.yaml: %v", err)
	}

	// Convert database port to integer
	dbPort := viper.GetString("database.port")
	port, err := strconv.Atoi(dbPort)
	if err != nil {
		return nil, fmt.Errorf("invalid database port number: %v", err)
	}
	viper.Set("database.port", port)

	err = viper.Unmarshal(&config)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %v", err)
	}

	return &config, nil
}
