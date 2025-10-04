package http

import (
	"net/http"
	"path/filepath"

	chi "github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/redis/go-redis/v9"

	"heartguard-superadmin/internal/auth"
	"heartguard-superadmin/internal/config"
	authmw "heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/superadmin"
)

func NewRouter(logger authmw.Logger, cfg *config.Config, repo *superadmin.Repo, rdb *redis.Client, h *superadmin.Handlers) http.Handler {
	r := chi.NewRouter()
	r.Use(middleware.RequestID, middleware.RealIP, middleware.Recoverer)
	r.Use(authmw.RateLimit(rdb, cfg.RateLimitRPS, cfg.RateLimitBurst))

	// Health
	r.Get("/healthz", h.Healthz)

	// Auth públicas
	ah := auth.NewHandlers(cfg, repo)
	r.Route("/v1/auth", func(r chi.Router) {
		r.Post("/login", ah.Login)
		r.Post("/refresh", ah.Refresh)
		r.Post("/logout", ah.Logout)
	})

	// Superadmin protegidas
	r.Route("/v1/superadmin", func(s chi.Router) {
		s.Use(authmw.RequireSuperadmin(cfg, rdb, repo))

		s.Route("/organizations", func(r chi.Router) {
			r.Post("/", h.CreateOrganization)
			r.Get("/", h.ListOrganizations)
			r.Get("/{id}", h.GetOrganization)
			r.Patch("/{id}", h.UpdateOrganization)
			r.Delete("/{id}", h.DeleteOrganization)
			r.Get("/{id}/members", h.ListMembers)
			r.Post("/{id}/members", h.AddMember)
			r.Delete("/{id}/members/{userId}", h.RemoveMember)
		})

		s.Route("/invitations", func(r chi.Router) {
			r.Get("/", h.ListInvitations)
			r.Post("/", h.CreateInvitation)
			r.Post("/{token}/consume", h.ConsumeInvitation)
			r.Delete("/{id}", h.CancelInvitation)
		})

		s.Route("/catalogs", func(r chi.Router) {
			r.Get("/{catalog}", h.ListCatalog)
			r.Post("/{catalog}", h.CreateCatalogItem)
			r.Patch("/{catalog}/{id}", h.UpdateCatalogItem)
			r.Delete("/{catalog}/{id}", h.DeleteCatalogItem)
		})

		s.Get("/metrics/overview", h.MetricsOverview)
		s.Get("/metrics/activity", h.MetricsRecentActivity)
		s.Get("/metrics/users/status-breakdown", h.MetricsUserStatusBreakdown)
		s.Get("/metrics/invitations/breakdown", h.MetricsInvitationBreakdown)
		s.Get("/users", h.SearchUsers)
		s.Patch("/users/{id}/status", h.UpdateUserStatus)
		s.Post("/api-keys", h.CreateAPIKey)
		s.Post("/api-keys/{id}/permissions", h.SetAPIKeyPermissions)
		s.Delete("/api-keys/{id}", h.RevokeAPIKey)
		s.Get("/api-keys", h.ListAPIKeys)
		s.Get("/audit-logs", h.ListAuditLogs)
	})

	// Static web/ (lo que ya tienes)
	fs := http.Dir("web")
	r.Get("/*", func(w http.ResponseWriter, req *http.Request) {
		up := req.URL.Path
		if up == "/" {
			up = "/index.html"
		}
		f, err := fs.Open(up)
		if err == nil {
			defer f.Close()
			fi, _ := f.Stat()
			http.ServeContent(w, req, filepath.Base(up), fi.ModTime(), f)
			return
		}
		idx, err := fs.Open("/index.html")
		if err != nil {
			http.Error(w, "index not found", http.StatusInternalServerError)
			return
		}
		defer idx.Close()
		fi, _ := idx.Stat()
		http.ServeContent(w, req, "index.html", fi.ModTime(), idx)
	})

	return r
}
