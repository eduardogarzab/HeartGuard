package middleware

import (
	"context"
	"net/http"
	"strings"

	"go.uber.org/zap"
	"heartguard-superadmin/internal/config"
)

type ctxKey string

const ctxUserID ctxKey = "userID"

// RequireSuperadmin: demo-only auth. Acepta:
// - X-Demo-Superadmin: 1
// - Authorization: Bearer <SUPERADMIN_TEST_TOKEN>
func RequireSuperadmin(cfg *config.Config, logger *zap.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if r.Header.Get("X-Demo-Superadmin") == "1" {
				ctx := context.WithValue(r.Context(), ctxUserID, "00000000-0000-0000-0000-000000000001")
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}
			auth := r.Header.Get("Authorization")
			if !strings.HasPrefix(auth, "Bearer ") {
				http.Error(w, "missing bearer", http.StatusUnauthorized)
				return
			}
			tok := strings.TrimPrefix(auth, "Bearer ")
			if tok == "" || (cfg.SuperadminTestToken != "" && tok != cfg.SuperadminTestToken) {
				http.Error(w, "invalid token", http.StatusUnauthorized)
				return
			}
			ctx := context.WithValue(r.Context(), ctxUserID, "00000000-0000-0000-0000-000000000001")
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}
