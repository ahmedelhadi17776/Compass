.PHONY: build run dev test swagger fmt lint clean

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GORUN=$(GOCMD) run
GOTEST=$(GOCMD) test
GOFMT=$(GOCMD) fmt
GOMOD=$(GOCMD) mod
BINARY_NAME=server.exe
GOPATH=$(shell go env GOPATH)

# Detect OS
ifeq ($(OS),Windows_NT)
    SHELL := powershell.exe
    .SHELLFLAGS := -NoProfile -Command
    RM_F_CMD = Remove-Item -Force -Recurse -ErrorAction Ignore
    BINARY_EXTENSION=.exe
else
    RM_F_CMD = rm -rf
    BINARY_EXTENSION=
endif

# Build the application
build:
	$(GOBUILD) -o bin/$(BINARY_NAME) cmd/api/main.go

# Run the application
run: build
	./bin/$(BINARY_NAME)

# Run with hot reload using air
dev:
	$(GOPATH)/bin/air

# Run tests
test:
	$(GOTEST) -v ./...

# Generate swagger documentation
swagger:
	$(GOPATH)/bin/swag init -g cmd/api/main.go -o docs/swagger

# Format code
fmt:
	$(GOFMT) ./...

# Run linter
lint:
	$(GOPATH)/bin/golangci-lint run

# Clean build artifacts
clean:
	$(RM_F_CMD) bin/
	$(RM_F_CMD) docs/swagger/
	$(RM_F_CMD) tmp/

# Install development dependencies
setup:
	$(GOCMD) install github.com/air-verse/air@latest
	$(GOCMD) install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	$(GOCMD) install github.com/swaggo/swag/cmd/swag@latest
	$(GOMOD) tidy

# Create database
createdb:
	createdb compass_db

# Drop database
dropdb:
	dropdb compass_db

# Run database migrations
migrate-up:
	migrate -path migrations -database "postgresql://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)?sslmode=$(DB_SSL_MODE)" up

# Rollback database migrations
migrate-down:
	migrate -path migrations -database "postgresql://$(DB_USER):$(DB_PASSWORD)@$(DB_HOST):$(DB_PORT)/$(DB_NAME)?sslmode=$(DB_SSL_MODE)" down

# Create a new migration file
migrate-create:
	@read -p "Enter migration name: " name; \
	migrate create -ext sql -dir migrations -seq $$name 