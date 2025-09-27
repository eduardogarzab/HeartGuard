package config

import (
	"errors"
	"os"
)

type Config struct {
	Env                 string
	HTTPAddr            string
	DatabaseURL         string
	AccessTokenSecret   string
	SuperadminTestToken string
}

func Load() (*Config, error) {
	cfg := &Config{
		Env:                 getenv("ENV", "dev"),
		HTTPAddr:            getenv("HTTP_ADDR", ":8080"),
		DatabaseURL:         os.Getenv("DATABASE_URL"),
		AccessTokenSecret:   getenv("ACCESS_TOKEN_SECRET", "dev-secret-change"),
		SuperadminTestToken: os.Getenv("SUPERADMIN_TEST_TOKEN"),
	}
	if cfg.DatabaseURL == "" {
		return nil, errors.New("DATABASE_URL is required")
	}
	return cfg, nil
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return def
}
