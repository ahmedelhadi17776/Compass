.PHONY: build run dev test swagger fmt lint clean docker-build docker-run docker-compose-up docker-compose-down

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GORUN=$(GOCMD) run
GOTEST=$(GOCMD) test
GOFMT=$(GOCMD) fmt
GOMOD=$(GOCMD) mod
BINARY_NAME=server
GOPATH=$(shell go env GOPATH)

# Docker parameters
DOCKER_COMPOSE=docker compose
DOCKER=docker

# Database parameters
DB_USER ?= ahmed
DB_PASSWORD ?= 0502747598
DB_NAME ?= compass
DB_HOST ?= localhost
DB_PORT ?= 5432
DB_SSL_MODE ?= disable

# Detect OS
ifeq ($(OS),Windows_NT)
    SHELL := powershell.exe
    .SHELLFLAGS := -NoProfile -Command
    RM_F_CMD = Remove-Item -Force -Recurse -ErrorAction Ignore
    BINARY_EXTENSION=.exe
    AIR_CMD=$(GOPATH)/bin/air.exe
else
    RM_F_CMD = rm -rf
    BINARY_EXTENSION=
    AIR_CMD=$(GOPATH)/bin/air
endif

# Build the application
build:
	$(GOBUILD) -o bin/$(BINARY_NAME)$(BINARY_EXTENSION) ./cmd/api/main.go

# Run the application
run: build
	./bin/$(BINARY_NAME)$(BINARY_EXTENSION)

# Run with hot reload using air
dev:
ifeq ($(OS),Windows_NT)
	go run github.com/air-verse/air@latest
else
	$(AIR_CMD)
endif

# Run tests
test:
	$(GOTEST) -v -race -cover ./...

# Run tests with coverage report
test-coverage:
	$(GOTEST) -v -race -coverprofile=coverage.out ./...
	$(GOCMD) tool cover -html=coverage.out -o coverage.html

# Generate swagger documentation
swagger:
	$(GOPATH)/bin/swag.exe init -g cmd/api/main.go -o docs/swagger

# Format code
fmt:
	$(GOFMT) ./...

# Run linter
lint:
	$(GOPATH)/bin/golangci-lint.exe run

# Clean build artifacts
clean:
	$(RM_F_CMD) bin/
	$(RM_F_CMD) docs/swagger/
	$(RM_F_CMD) tmp/
	$(RM_F_CMD) coverage.out
	$(RM_F_CMD) coverage.html

# Install development dependencies
setup:
ifeq ($(OS),Windows_NT)
	$(GOCMD) install github.com/air-verse/air@latest
	$(GOCMD) install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	$(GOCMD) install github.com/swaggo/swag/cmd/swag@latest
	$(GOCMD) install github.com/golang-migrate/migrate/v4/cmd/migrate@latest
	$(GOMOD) tidy
else
	$(GOCMD) install github.com/air-verse/air@latest
	$(GOCMD) install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	$(GOCMD) install github.com/swaggo/swag/cmd/swag@latest
	$(GOCMD) install github.com/golang-migrate/migrate/v4/cmd/migrate@latest
	$(GOMOD) tidy
endif

# Docker commands
docker-build:
	$(DOCKER) build -t compass-api .

docker-run:
	$(DOCKER) run -p 8000:8000 compass-api

docker-compose-up:
	$(DOCKER_COMPOSE) up --build -d

docker-compose-down:
	$(DOCKER_COMPOSE) down -v

# Database commands
createdb:
	createdb $(DB_NAME)

dropdb:
	dropdb $(DB_NAME)

migrate-up:
	migrate -path migrations -database "postgresql://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)?sslmode=$(DB_SSL_MODE)" up

migrate-down:
	migrate -path migrations -database "postgresql://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)?sslmode=$(DB_SSL_MODE)" down

migrate-create:
	@read -p "Enter migration name: " name; \
	migrate create -ext sql -dir migrations -seq $$name

# Generate mock files for testing
generate-mocks:
	mockgen -source=internal/domain/task/repository.go -destination=internal/domain/task/mocks/repository_mock.go
	mockgen -source=internal/domain/user/repository.go -destination=internal/domain/user/mocks/repository_mock.go 