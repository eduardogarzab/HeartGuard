package db

import (
	"context"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"heartguard-superadmin/internal/config"
)

func NewPool(cfg *config.Config) (*pgxpool.Pool, error) {
	pc, err := pgxpool.ParseConfig(cfg.DatabaseURL)
	if err != nil {
		return nil, err
	}
	pc.MaxConns = 10
	pc.MinConns = 1
	pc.MaxConnLifetime = time.Hour
	pc.MaxConnIdleTime = 15 * time.Minute
	pc.HealthCheckPeriod = time.Minute
	return pgxpool.NewWithConfig(context.Background(), pc)
}
