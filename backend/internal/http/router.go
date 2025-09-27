package http

import (
	"net/http"
	"path/filepath"

	chi "github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"heartguard-superadmin/internal/config"
	authmw "heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/superadmin"
)

// NewRouter arma todas las rutas: API bajo /v1/... y UI estática bajo /
func NewRouter(logger authmw.Logger, cfg *config.Config, h *superadmin.Handlers) http.Handler {
	r := chi.NewRouter()
	r.Use(middleware.RequestID)
	r.Use(middleware.RealIP)
	r.Use(middleware.Recoverer)

	// Health
	r.Get("/healthz", h.Healthz)

	// API superadmin
	r.Route("/v1/superadmin", func(r chi.Router) {
		r.Use(authmw.RequireSuperadmin(cfg, nil))

		r.Route("/organizations", func(r chi.Router) {
			r.Post("/", h.CreateOrganization)
			r.Get("/", h.ListOrganizations)
			r.Get("/{id}", h.GetOrganization)
			r.Patch("/{id}", h.UpdateOrganization)
			r.Delete("/{id}", h.DeleteOrganization)

			r.Post("/{id}/invitations", h.CreateInvitation)
			r.Post("/{id}/members", h.AddMember)
			r.Delete("/{id}/members/{userId}", h.RemoveMember)
		})

		r.Post("/invitations/{token}/consume", h.ConsumeInvitation)

		r.Get("/users", h.SearchUsers)
		r.Patch("/users/{id}/status", h.UpdateUserStatus)

		r.Post("/api-keys", h.CreateAPIKey)
		r.Post("/api-keys/{id}/permissions", h.SetAPIKeyPermissions)
		r.Delete("/api-keys/{id}", h.RevokeAPIKey)
		r.Get("/api-keys", h.ListAPIKeys)

		r.Get("/audit-logs", h.ListAuditLogs)
	})

	// UI estática desde ./web
	static := http.Dir(filepath.Clean("web"))
	r.Handle("/*", spa(static))

	return r
}

func NewServer(cfg *config.Config, h http.Handler) *http.Server {
	return &http.Server{
		Addr:    cfg.HTTPAddr,
		Handler: h,
	}
}

// spa: sirve index.html como fallback para rutas desconocidas (hash-router o client-side routing)
func spa(root http.FileSystem) http.Handler {
	fs := http.FileServer(root)
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		path := r.URL.Path
		f, err := root.Open(path)
		if err == nil {
			defer f.Close()
			stat, _ := f.Stat()
			if stat != nil && !stat.IsDir() {
				fs.ServeHTTP(w, r)
				return
			}
		}
		// fallback a /index.html
		index, err := root.Open("/index.html")
		if err != nil {
			http.Error(w, "index not found", http.StatusInternalServerError)
			return
		}
		defer index.Close()
		info, _ := index.Stat()
		http.ServeContent(w, r, "index.html", info.ModTime(), index)
	})
}
