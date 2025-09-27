package middleware

import "go.uber.org/zap"

type Logger interface {
	Info(msg string, fields ...zap.Field)
	Error(msg string, fields ...zap.Field)
	Fatal(msg string, fields ...zap.Field)
	Sync() error
}

func NewLogger(env string) *zap.Logger {
	if env == "prod" {
		l, _ := zap.NewProduction()
		return l
	}
	l, _ := zap.NewDevelopment()
	return l
}

func Field(key string, v interface{}) zap.Field { return zap.Any(key, v) }
