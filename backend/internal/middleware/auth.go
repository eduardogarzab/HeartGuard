package middleware

import (
	"context"
	"net/http"
	"strings"
	"time"

	"heartguard-superadmin/internal/models"
	"heartguard-superadmin/internal/session"
)

type ctxKey string

const (
	CtxUserIDKey          ctxKey = "actor_user_id"
	CtxSessionJTIKey      ctxKey = "session_jti"
	CtxCSRFFromSession    ctxKey = "csrf_token"
	CtxCurrentUserKey     ctxKey = "current_user"
	CtxIsSuperadminKey    ctxKey = "is_superadmin"
	CtxSessionExpiresAtKey ctxKey = "session_expires_at"
)

// repoIface aggregates dependencies required by session middleware.
type repoIface interface {
	IsSuperadmin(ctx context.Context, userID string) (bool, error)
	GetUserSummary(ctx context.Context, userID string) (*models.User, error)
}

func SessionLoader(sm *session.Manager, repo repoIface) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if sm == nil {
				next.ServeHTTP(w, r)
				return
			}
			cookie, err := r.Cookie(sm.CookieName())
			if err != nil || cookie.Value == "" {
				next.ServeHTTP(w, r)
				return
			}
			claims, err := sm.Validate(r.Context(), cookie.Value)
			if err != nil {
				http.SetCookie(w, sm.ClearCookie())
				next.ServeHTTP(w, r)
				return
			}

			ctx := r.Context()
			ctx = context.WithValue(ctx, CtxUserIDKey, claims.UserID)
			ctx = context.WithValue(ctx, CtxSessionJTIKey, claims.JTI)

			if repo != nil && claims.UserID != "" {
				if user, err := repo.GetUserSummary(r.Context(), claims.UserID); err == nil {
					ctx = context.WithValue(ctx, CtxCurrentUserKey, user)
				}
				if ok, err := repo.IsSuperadmin(r.Context(), claims.UserID); err == nil {
					ctx = context.WithValue(ctx, CtxIsSuperadminKey, ok)
				}
			}

			if csrf, err := sm.EnsureCSRF(r.Context(), claims.JTI); err == nil {
				ctx = context.WithValue(ctx, CtxCSRFFromSession, csrf)
			}

			sm.Refresh(r.Context(), claims.JTI)
			
			// Add session expiration time to context
			if ttl := sm.RemainingTTL(r.Context(), claims.JTI); ttl > 0 {
				expiresAt := time.Now().Add(ttl)
				ctx = context.WithValue(ctx, CtxSessionExpiresAtKey, expiresAt)
			}
			
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func RequireAuthenticated() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			uid := UserIDFromContext(r.Context())
			if uid == "" {
				http.Redirect(w, r, "/login", http.StatusSeeOther)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func RequireSuperadmin(sm *session.Manager, repo repoIface) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return RequireAuthenticated()(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			uid := UserIDFromContext(r.Context())
			if uid == "" {
				http.Redirect(w, r, "/login", http.StatusSeeOther)
				return
			}
			if repo == nil {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			ok := false
			if v, present := r.Context().Value(CtxIsSuperadminKey).(bool); present {
				ok = v
			} else {
				if res, err := repo.IsSuperadmin(r.Context(), uid); err == nil {
					ok = res
				}
			}
			if !ok {
				http.Error(w, "forbidden", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		}))
	}
}

func CSRF(sm *session.Manager) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			switch r.Method {
			case http.MethodGet, http.MethodHead, http.MethodOptions, http.MethodTrace:
				next.ServeHTTP(w, r)
				return
			}
			jti := SessionJTIFromContext(r.Context())
			if jti == "" {
				http.Error(w, "unauthorized", http.StatusUnauthorized)
				return
			}
			
			// Handle both regular forms and multipart forms
			var token string
			contentType := r.Header.Get("Content-Type")
			
			// Check if it's a multipart form
			if strings.HasPrefix(contentType, "multipart/form-data") {
				// For multipart forms, parse it first
				if err := r.ParseMultipartForm(32 << 20); err != nil {
					http.Error(w, "invalid form", http.StatusBadRequest)
					return
				}
				token = r.FormValue("_csrf")
			} else {
				// For regular forms, use ParseForm
				if err := r.ParseForm(); err != nil {
					http.Error(w, "invalid form", http.StatusBadRequest)
					return
				}
				token = r.FormValue("_csrf")
			}
			
			// Fallback to header if not in form
			if token == "" {
				token = r.Header.Get("X-CSRF-Token")
			}
			
			if err := sm.ValidateCSRF(r.Context(), jti, token); err != nil {
				http.Error(w, "csrf failure", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}

func UserIDFromContext(ctx context.Context) string {
	if v, ok := ctx.Value(CtxUserIDKey).(string); ok {
		return v
	}
	return ""
}

func SessionJTIFromContext(ctx context.Context) string {
	if v, ok := ctx.Value(CtxSessionJTIKey).(string); ok {
		return v
	}
	return ""
}

func CSRFFromContext(ctx context.Context) string {
	if v, ok := ctx.Value(CtxCSRFFromSession).(string); ok {
		return v
	}
	return ""
}

func UserFromContext(ctx context.Context) *models.User {
	if v, ok := ctx.Value(CtxCurrentUserKey).(*models.User); ok {
		return v
	}
	return nil
}

func IsSuperadmin(ctx context.Context) bool {
	if v, ok := ctx.Value(CtxIsSuperadminKey).(bool); ok {
		return v
	}
	return false
}

func SessionExpiresAtFromContext(ctx context.Context) *time.Time {
	if v, ok := ctx.Value(CtxSessionExpiresAtKey).(time.Time); ok {
		return &v
	}
	return nil
}
