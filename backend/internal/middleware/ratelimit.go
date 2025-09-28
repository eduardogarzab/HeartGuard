package middleware

import (
	"fmt"
	"net"
	"net/http"
	"time"

	"github.com/redis/go-redis/v9"
)

// Usa RemoteAddr (confiando en chi/middleware.RealIP antes en la cadena).
func clientIP(r *http.Request) string {
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil && host != "" {
		return host
	}
	return "unknown"
}

// RateLimit: ventana fija de 1s, permite rps + burst por segundo por (método,ruta,IP).
// Nota: Asegúrate de registrar primero chi/middleware.RealIP en el router.
func RateLimit(rdb *redis.Client, rps, burst int) func(http.Handler) http.Handler {
	if rps <= 0 {
		rps = 10
	}
	if burst < 0 {
		burst = 0
	}
	limit := int64(rps + burst) // máximo por segundo
	window := time.Second

	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ip := clientIP(r)
			// Incluye método para diferenciar GET/POST en el mismo path
			key := fmt.Sprintf("rl:%s:%s:%s", r.Method, r.URL.Path, ip)

			// INCR y setea expiración la primera vez
			pipe := rdb.TxPipeline()
			incr := pipe.Incr(r.Context(), key)
			pipe.Expire(r.Context(), key, window)
			_, _ = pipe.Exec(r.Context())

			n, err := incr.Result()
			if err == nil && n > limit {
				// 429 con Retry-After aproximado
				w.Header().Set("Retry-After", "1")
				http.Error(w, "rate limit", http.StatusTooManyRequests)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
