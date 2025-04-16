package config

import (
	"github.com/spf13/viper"
)

type DatabaseConfig struct {
    Host     string
    Port     string
    User     string
    Password string
    DBName   string
    SSLMode  string
}

func LoadDatabaseConfig() *DatabaseConfig {
    return &DatabaseConfig{
        Host:     viper.GetString("DB_HOST"),
        Port:     viper.GetString("DB_PORT"),
        User:     viper.GetString("DB_USER"),
        Password: viper.GetString("DB_PASSWORD"),
        DBName:   viper.GetString("DB_NAME"),
        SSLMode:  viper.GetString("DB_SSLMODE"),
    }
}