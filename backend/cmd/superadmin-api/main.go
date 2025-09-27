package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"heartguard-superadmin/internal/config"
	"heartguard-superadmin/internal/db"
	hhttp "heartguard-superadmin/internal/http"
	"heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/superadmin"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("config: %v", err)
	}

	logger := middleware.NewLogger(cfg.Env)
	defer logger.Sync()

	pool, err := db.NewPool(cfg)
	if err != nil {
		logger.Fatal("db pool", middleware.Field("err", err))
	}
	defer pool.Close()

	repo := superadmin.NewRepo(pool)
	handlers := superadmin.NewHandlers(repo, logger)

	router := hhttp.NewRouter(logger, cfg, handlers)
	srv := hhttp.NewServer(cfg, router)

	go func() {
		if err := srv.ListenAndServe(); err != nil && err.Error() != "http: Server closed" {
			logger.Fatal("http server", middleware.Field("err", err))
		}
	}()

	logger.Info("listening", middleware.Field("addr", cfg.HTTPAddr))

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	_ = srv.Shutdown(ctx)
}
