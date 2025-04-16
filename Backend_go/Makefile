.PHONY: build run dev test swagger fmt lint clean

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GORUN=$(GOCMD) run
GOTEST=$(GOCMD) test
GOFMT=$(GOCMD) fmt
GOMOD=$(GOCMD) mod
BINARY_NAME=server

# Build the application
build:
	$(GOBUILD) -o bin/$(BINARY_NAME) cmd/api/main.go

# Run the application
run: build
	./bin/$(BINARY_NAME)

# Run with hot reload using air (requires air: go install github.com/cosmtrek/air@latest)
dev:
	air

# Run tests
test:
	$(GOTEST) -v ./...

# Generate swagger documentation
swagger:
	swag init -g cmd/api/main.go -o docs/swagger

# Format code
fmt:
	$(GOFMT) ./...

# Run linter (requires golangci-lint: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest)
lint:
	golangci-lint run

# Clean build artifacts
clean:
	rm -rf bin/
	rm -rf docs/swagger/

# Install development dependencies
setup:
	go install github.com/cosmtrek/air@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install github.com/swaggo/swag/cmd/swag@latest
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