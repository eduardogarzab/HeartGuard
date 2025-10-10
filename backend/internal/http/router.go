package http

import (
	"net/http"
	"strings"

	chi "github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
	"github.com/redis/go-redis/v9"

	"heartguard-superadmin/internal/auth"
	"heartguard-superadmin/internal/config"
	authmw "heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/session"
	"heartguard-superadmin/internal/superadmin"
)

func NewRouter(logger authmw.Logger, cfg *config.Config, repo superadmin.Repository, rdb *redis.Client, sessions *session.Manager, authHandlers *auth.Handlers, uiHandlers *superadmin.Handlers) http.Handler {
	r := chi.NewRouter()
	r.Use(authmw.LoopbackOnly(logger))
	r.Use(middleware.RequestID, middleware.RealIP, middleware.Recoverer)
	r.Use(authmw.RateLimit(rdb, cfg.RateLimitRPS, cfg.RateLimitBurst))
	r.Use(authmw.SecurityHeaders())
	r.Use(authmw.SessionLoader(sessions, repo))

	r.Get("/healthz", uiHandlers.Healthz)

	r.Get("/", func(w http.ResponseWriter, req *http.Request) {
		if authmw.UserIDFromContext(req.Context()) != "" {
			http.Redirect(w, req, "/superadmin/dashboard", http.StatusSeeOther)
			return
		}
		http.Redirect(w, req, "/login", http.StatusSeeOther)
	})

	r.Get("/login", authHandlers.LoginForm)
	r.Post("/login", authHandlers.LoginSubmit)
	r.With(authmw.CSRF(sessions)).Post("/logout", authHandlers.Logout)

	r.Route("/superadmin", func(s chi.Router) {
		s.Use(authmw.RequireSuperadmin(sessions, repo))
		s.Use(authmw.CSRF(sessions))

		s.Get("/dashboard", uiHandlers.Dashboard)

		s.Route("/organizations", func(or chi.Router) {
			or.Get("/", uiHandlers.OrganizationsIndex)
			or.Post("/", uiHandlers.OrganizationsCreate)
			or.Get("/{id}", uiHandlers.OrganizationDetail)
			or.Post("/{id}/delete", uiHandlers.OrganizationDelete)
		})

		s.Route("/content", func(cr chi.Router) {
			cr.Get("/", uiHandlers.ContentIndex)
			cr.Get("/new", uiHandlers.ContentNew)
			cr.Post("/", uiHandlers.ContentCreate)
			cr.Get("/{id}", uiHandlers.ContentEdit)
			cr.Post("/{id}", uiHandlers.ContentUpdate)
			cr.Post("/{id}/delete", uiHandlers.ContentDelete)
		})

		s.Route("/invitations", func(ir chi.Router) {
			ir.Get("/", uiHandlers.InvitationsIndex)
			ir.Post("/", uiHandlers.InvitationsCreate)
			ir.Post("/{id}/cancel", uiHandlers.InvitationCancel)
		})

		s.Route("/users", func(ur chi.Router) {
			ur.Get("/", uiHandlers.UsersIndex)
			ur.Post("/{id}/status", uiHandlers.UsersUpdateStatus)
		})

		s.Route("/roles", func(rr chi.Router) {
			rr.Get("/", uiHandlers.RolesIndex)
			rr.Post("/", uiHandlers.RolesCreate)
			rr.Post("/users/{id}", uiHandlers.RolesUpdateUserAssignment)
			rr.Post("/{id}/delete", uiHandlers.RolesDelete)
		})

		s.Route("/catalogs", func(cr chi.Router) {
			cr.Get("/", uiHandlers.CatalogsIndex)
			cr.Get("/{catalog}", uiHandlers.CatalogsIndex)
			cr.Post("/{catalog}", uiHandlers.CatalogsCreate)
			cr.Post("/{catalog}/{id}/update", uiHandlers.CatalogsUpdate)
			cr.Post("/{catalog}/{id}/delete", uiHandlers.CatalogsDelete)
		})

		s.Route("/api-keys", func(ar chi.Router) {
			ar.Get("/", uiHandlers.APIKeysIndex)
			ar.Post("/", uiHandlers.APIKeysCreate)
			ar.Post("/{id}/permissions", uiHandlers.APIKeysUpdatePermissions)
			ar.Post("/{id}/revoke", uiHandlers.APIKeysRevoke)
		})

		s.Get("/audit", uiHandlers.AuditIndex)
		s.Get("/settings/system", uiHandlers.SystemSettingsForm)
		s.Post("/settings/system", uiHandlers.SystemSettingsUpdate)
	})

	uiFileServer := http.FileServer(http.Dir("ui/assets"))
	r.Get("/ui-assets/*", func(w http.ResponseWriter, req *http.Request) {
		http.StripPrefix("/ui-assets", uiFileServer).ServeHTTP(w, req)
	})

	r.NotFound(func(w http.ResponseWriter, req *http.Request) {
		if strings.HasPrefix(req.URL.Path, "/ui-assets/") {
			http.NotFound(w, req)
			return
		}
		http.Redirect(w, req, "/", http.StatusSeeOther)
	})

	return r
}
