package rediscli

import (
	"context"
	"log"

	"github.com/redis/go-redis/v9"
)

var Ctx = context.Background()

func New(url string) *redis.Client {
	opt, err := redis.ParseURL(url)
	if err != nil { log.Fatalf("redis parse: %v", err) }
	return redis.NewClient(opt)
}
