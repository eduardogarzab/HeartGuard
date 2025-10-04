package main

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"heartguard-superadmin/internal/config"
	"heartguard-superadmin/internal/db"
	hhttp "heartguard-superadmin/internal/http"
	"heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/rediscli"
	"heartguard-superadmin/internal/superadmin"
)

func main() {
	// Load config (2 valores)
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	// Logger
	logger := middleware.NewLogger(cfg.Env) // asegúrate que Config tenga campo Env string
	defer logger.Sync()

	// DB
	pool, err := db.NewPool(cfg)
	if err != nil {
		logger.Fatal("db pool", middleware.Field("err", err))
	}
	defer pool.Close()

	// Redis
	rdb := rediscli.New(cfg.RedisURL)
	defer func() { _ = rdb.Close() }()

	// Repo + handlers
	repo := superadmin.NewRepo(pool, rdb)
	handlers := superadmin.NewHandlers(repo, logger)

	// Router
	router := hhttp.NewRouter(logger, cfg, repo, rdb, handlers)

	// Servidor HTTP estándar (reemplaza hhttp.NewServer)
	srv := &http.Server{
		Addr:              cfg.HTTPAddr,
		Handler:           router,
		ReadHeaderTimeout: 10 * time.Second,
	}

	// Arranque HTTP
	go func() {
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			logger.Fatal("http server", middleware.Field("err", err))
		}
	}()
	logger.Info("listening", middleware.Field("addr", cfg.HTTPAddr))

	// Shutdown ordenado
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}
