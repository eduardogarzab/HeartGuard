package config

import (
	"fmt"
	"os"
	"strconv"
	"time"
)

type Config struct {
	Env               string
	HTTPAddr          string
	DatabaseURL       string

	JWTSecret         string
	AccessTokenTTL    time.Duration
	RefreshTokenTTL   time.Duration

	RedisURL          string
	RateLimitRPS      int
	RateLimitBurst    int
}

func Load() (*Config, error) {
	c := &Config{
		Env:         getenv("ENV", "dev"),
		HTTPAddr:    getenv("HTTP_ADDR", ":8080"),
		DatabaseURL: os.Getenv("DATABASE_URL"),
		JWTSecret:   os.Getenv("JWT_SECRET"),
		RedisURL:    os.Getenv("REDIS_URL"),
	}

	if c.DatabaseURL == "" {
		return nil, fmt.Errorf("DATABASE_URL is required")
	}
	if c.JWTSecret == "" {
		return nil, fmt.Errorf("JWT_SECRET is required")
	}
	if c.RedisURL == "" {
		return nil, fmt.Errorf("REDIS_URL is required")
	}

	var err error
	if c.AccessTokenTTL, err = time.ParseDuration(getenv("ACCESS_TOKEN_TTL", "15m")); err != nil {
		return nil, fmt.Errorf("bad ACCESS_TOKEN_TTL: %w", err)
	}
	if c.RefreshTokenTTL, err = time.ParseDuration(getenv("REFRESH_TOKEN_TTL", "720h")); err != nil {
		return nil, fmt.Errorf("bad REFRESH_TOKEN_TTL: %w", err)
	}

	if c.RateLimitRPS, err = atoi(getenv("RATE_LIMIT_RPS", "10")); err != nil {
		return nil, fmt.Errorf("bad RATE_LIMIT_RPS: %w", err)
	}
	if c.RateLimitBurst, err = atoi(getenv("RATE_LIMIT_BURST", "20")); err != nil {
		return nil, fmt.Errorf("bad RATE_LIMIT_BURST: %w", err)
	}

	return c, nil
}

func getenv(k, def string) string {
	if v := os.Getenv(k); v != "" { return v }
	return def
}

func atoi(s string) (int, error) {
	n, err := strconv.Atoi(s)
	if err != nil { return 0, err }
	return n, nil
}
