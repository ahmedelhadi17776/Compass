package main

import (
    "flag"
    "fmt"
    "log"
    "os"

    "github.com/golang-migrate/migrate/v4"
    _ "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
)

func main() {
    var migrationDir string
    var dbURL string
    var command string

    flag.StringVar(&migrationDir, "path", "migrations", "Directory with migration files")
    flag.StringVar(&dbURL, "db", os.Getenv("DATABASE_URL"), "Database connection string")
    flag.StringVar(&command, "command", "up", "Migration command (up, down, version)")
    flag.Parse()

    m, err := migrate.New(
        "file://"+migrationDir,
        dbURL,
    )
    if err != nil {
        log.Fatal(err)
    }

    switch command {
    case "up":
        if err := m.Up(); err != nil && err != migrate.ErrNoChange {
            log.Fatal(err)
        }
    case "down":
        if err := m.Down(); err != nil && err != migrate.ErrNoChange {
            log.Fatal(err)
        }
    case "version":
        version, dirty, err := m.Version()
        if err != nil {
            log.Fatal(err)
        }
        fmt.Printf("Version: %d, Dirty: %v\n", version, dirty)
    default:
        log.Fatalf("Unknown command: %s", command)
    }

    log.Printf("Migration command '%s' executed successfully", command)
}