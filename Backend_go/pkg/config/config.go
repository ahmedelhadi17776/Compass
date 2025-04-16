package config

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"

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

	// Load main config file first
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	if err := viper.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("error loading config.yaml: %v", err)
	}

	// Enable environment variable override
	viper.AutomaticEnv()
	viper.SetEnvKeyReplacer(strings.NewReplacer(".", "_"))

	// Override with environment variables if they exist
	if host := os.Getenv("DB_HOST"); host != "" {
		viper.Set("database.host", host)
	}
	if port := os.Getenv("DB_PORT"); port != "" {
		portInt, err := strconv.Atoi(port)
		if err != nil {
			return nil, fmt.Errorf("invalid database port number: %v", err)
		}
		viper.Set("database.port", portInt)
	}
	if user := os.Getenv("DB_USER"); user != "" {
		viper.Set("database.user", user)
	}
	if password := os.Getenv("DB_PASSWORD"); password != "" {
		viper.Set("database.password", password)
	}
	if name := os.Getenv("DB_NAME"); name != "" {
		viper.Set("database.name", name)
	}
	if sslmode := os.Getenv("DB_SSLMODE"); sslmode != "" {
		viper.Set("database.sslmode", sslmode)
	}

	// Unmarshal config
	err = viper.Unmarshal(&config)
	if err != nil {
		return nil, fmt.Errorf("failed to unmarshal config: %v", err)
	}

	return &config, nil
}
