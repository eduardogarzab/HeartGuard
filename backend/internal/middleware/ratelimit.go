package middleware

import (
	"fmt"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/redis/go-redis/v9"
)

var rateLimitScript = redis.NewScript(`
local count = redis.call('INCR', KEYS[1])
if count == 1 then
  redis.call('PEXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('PTTL', KEYS[1])
return {count, ttl}
`)

// Usa X-Forwarded-For si está disponible, de lo contrario RemoteAddr (RealIP middleware debería haberlo normalizado).
func clientIP(r *http.Request) string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		ip := strings.TrimSpace(strings.Split(xff, ",")[0])
		if ip != "" {
			return ip
		}
	}
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
			res, err := rateLimitScript.Run(r.Context(), rdb, []string{key}, window.Milliseconds()).Result()
			if err != nil {
				next.ServeHTTP(w, r)
				return
			}
			vals, ok := res.([]interface{})
			if !ok || len(vals) != 2 {
				next.ServeHTTP(w, r)
				return
			}
			current := toInt64(vals[0])
			ttl := toInt64(vals[1])
			remaining := limit - current
			if remaining < 0 {
				remaining = 0
			}
			resetUnix := time.Now().Add(time.Second)
			if ttl > 0 {
				resetUnix = time.Now().Add(time.Duration(ttl) * time.Millisecond)
			}
			w.Header().Set("X-RateLimit-Limit", strconv.FormatInt(limit, 10))
			w.Header().Set("X-RateLimit-Remaining", strconv.FormatInt(max64(remaining, 0), 10))
			w.Header().Set("X-RateLimit-Reset", strconv.FormatInt(resetUnix.Unix(), 10))
			if current > limit {
				retryAfter := 1
				if ttl > 0 {
					retryAfter = int(time.Duration(ttl) * time.Millisecond / time.Second)
					if retryAfter <= 0 {
						retryAfter = 1
					}
				}
				w.Header().Set("Retry-After", strconv.Itoa(retryAfter))
				http.Error(w, "rate limit", http.StatusTooManyRequests)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func toInt64(v interface{}) int64 {
	switch t := v.(type) {
	case int64:
		return t
	case int:
		return int64(t)
	case float64:
		return int64(t)
	case string:
		n, _ := strconv.ParseInt(t, 10, 64)
		return n
	default:
		return 0
	}
}

func max64(a, b int64) int64 {
	if a > b {
		return a
	}
	return b
}
