package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/redis/go-redis/v9"
	"heartguard-superadmin/internal/auth"
	"heartguard-superadmin/internal/config"
)

type ctxKey string

const CtxUserIDKey ctxKey = "actor_user_id"

func unauthorized(w http.ResponseWriter, msg string) {
	w.Header().Set("WWW-Authenticate", `Bearer realm="heartguard", error="invalid_token"`)
	http.Error(w, msg, http.StatusUnauthorized)
}

func RequireAuth(cfg *config.Config, rdb *redis.Client) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			h := r.Header.Get("Authorization")
			if h == "" || !strings.HasPrefix(h, "Bearer ") {
				unauthorized(w, "missing bearer")
				return
			}
			tok := strings.TrimSpace(strings.TrimPrefix(h, "Bearer "))
			if tok == "" {
				unauthorized(w, "missing bearer")
				return
			}

			claims, err := auth.ParseJWT(cfg.JWTSecret, tok)
			if err != nil {
				unauthorized(w, "invalid token")
				return
			}
			if claims.JTI == "" || claims.UserID == "" {
				unauthorized(w, "invalid token")
				return
			}

			// denylist por jti (opcional si rdb == nil)
			if rdb != nil {
				key := "jwt:deny:" + claims.JTI
				if ok, _ := rdb.Exists(r.Context(), key).Result(); ok == 1 {
					unauthorized(w, "token revoked")
					return
				}
			}

			ctx := context.WithValue(r.Context(), CtxUserIDKey, claims.UserID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// repoIface pequeño para verificar el rol
type repoIface interface {
	IsSuperadmin(ctx context.Context, userID string) (bool, error)
}

func RequireSuperadmin(cfg *config.Config, rdb *redis.Client, repo repoIface) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return RequireAuth(cfg, rdb)(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			uid, _ := r.Context().Value(CtxUserIDKey).(string)
			if uid == "" {
				unauthorized(w, "invalid token")
				return
			}
			ok, err := repo.IsSuperadmin(r.Context(), uid)
			if err != nil || !ok {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		}))
	}
}
