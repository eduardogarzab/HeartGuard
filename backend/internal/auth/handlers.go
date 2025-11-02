package auth

import (
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"strings"
	"time"

	"go.uber.org/zap"
	"golang.org/x/crypto/bcrypt"

	"heartguard-superadmin/internal/config"
	"heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/models"
	"heartguard-superadmin/internal/session"
	"heartguard-superadmin/internal/ui"
)

// AuthRepo expone las operaciones necesarias para autenticación.
type AuthRepo interface {
	GetUserByEmail(ctx context.Context, email string) (*models.User, string, error)
	IsSuperadmin(ctx context.Context, userID string) (bool, error)
	GetSystemSettings(ctx context.Context) (*models.SystemSettings, error)
}

type Handlers struct {
	cfg      *config.Config
	repo     AuthRepo
	renderer *ui.Renderer
	sessions *session.Manager
	logger   *zap.Logger
}

func NewHandlers(cfg *config.Config, repo AuthRepo, renderer *ui.Renderer, sessions *session.Manager, logger *zap.Logger) *Handlers {
	return &Handlers{cfg: cfg, repo: repo, renderer: renderer, sessions: sessions, logger: logger}
}

type loginPageData struct {
	Email    string
	Error    string
	Logout   bool
	Settings *models.SystemSettings
}

func (h *Handlers) LoginForm(w http.ResponseWriter, r *http.Request) {
	if middleware.UserIDFromContext(r.Context()) != "" {
		http.Redirect(w, r, "/superadmin/dashboard", http.StatusSeeOther)
		return
	}
	settings, err := h.repo.GetSystemSettings(r.Context())
	if err != nil && h.logger != nil && !errors.Is(err, context.Canceled) && !errors.Is(err, context.DeadlineExceeded) {
		h.logger.Error("login settings load", zap.Error(err))
	}
	token, err := h.sessions.IssueGuestCSRF(r.Context(), 10*time.Minute)
	if err != nil {
		http.Error(w, "no se pudo preparar el formulario", http.StatusInternalServerError)
		return
	}
	http.SetCookie(w, h.sessions.GuestCSRFCookie(token, 10*time.Minute))
	data := loginPageData{
		Logout:   r.URL.Query().Get("logout") == "1",
		Settings: settings,
	}
	view := ui.ViewData{
		Title:     "Iniciar sesión",
		CSRFToken: token,
		Data:      data,
	}
	if err := h.renderer.Render(w, "login.html", view); err != nil && h.logger != nil {
		h.logger.Error("render login", zap.Error(err))
	}
}

func (h *Handlers) LoginSubmit(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	formToken := r.FormValue("_csrf")
	cookie, err := r.Cookie(h.sessions.GuestCookieName())
	if err != nil || cookie.Value == "" {
		if h.cfg.Env != "dev" {
			http.Error(w, "csrf inválido", http.StatusForbidden)
			return
		}
	}
	if err := h.sessions.ValidateGuestCSRF(r.Context(), formToken); err != nil {
		http.Error(w, "csrf inválido", http.StatusForbidden)
		return
	}
	if cookie != nil && cookie.Value != "" && cookie.Value != formToken {
		if h.cfg.Env != "dev" {
			http.Error(w, "csrf inválido", http.StatusForbidden)
			return
		}
	}
	h.sessions.ConsumeGuestCSRF(r.Context(), formToken)
	http.SetCookie(w, h.sessions.ClearGuestCSRFCookie())

	email := strings.TrimSpace(strings.ToLower(r.FormValue("email")))
	password := r.FormValue("password")
	if email == "" || password == "" {
		h.renderLoginWithError(w, r, email, "Correo y contraseña son obligatorios")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	user, hash, err := h.repo.GetUserByEmail(ctx, email)
	if err != nil {
		h.renderLoginWithError(w, r, email, "Credenciales inválidas")
		return
	}
	if bcrypt.CompareHashAndPassword([]byte(hash), []byte(password)) != nil {
		h.renderLoginWithError(w, r, email, "Credenciales inválidas")
		return
	}
	ok, err := h.repo.IsSuperadmin(ctx, user.ID)
	if err != nil || !ok {
		h.renderLoginWithError(w, r, email, "Acceso restringido al panel de superadministración")
		return
	}

	token, jti, _, err := h.sessions.Issue(r.Context(), user.ID)
	if err != nil {
		http.Error(w, "no se pudo iniciar sesión", http.StatusInternalServerError)
		return
	}
	http.SetCookie(w, h.sessions.SessionCookie(token, h.cfg.AccessTokenTTL))
	h.sessions.PushFlash(r.Context(), jti, session.Flash{Type: "success", Message: "¡Bienvenido de nuevo!"})
	http.Redirect(w, r, "/superadmin/dashboard", http.StatusSeeOther)
}

func (h *Handlers) Logout(w http.ResponseWriter, r *http.Request) {
	jti := middleware.SessionJTIFromContext(r.Context())
	if jti != "" {
		h.sessions.Revoke(r.Context(), jti)
	}
	http.SetCookie(w, h.sessions.ClearCookie())
	http.Redirect(w, r, "/login?logout=1", http.StatusSeeOther)
}

func (h *Handlers) RefreshSession(w http.ResponseWriter, r *http.Request) {
	userID := middleware.UserIDFromContext(r.Context())
	jti := middleware.SessionJTIFromContext(r.Context())
	if userID == "" || jti == "" {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(map[string]any{"success": false, "error": "No session"})
		return
	}

	// Refresh the session TTL in Redis
	h.sessions.Refresh(r.Context(), jti)

	// Get remaining TTL to return to client
	ttl := h.sessions.RemainingTTL(r.Context(), jti)
	if ttl <= 0 {
		w.WriteHeader(http.StatusUnauthorized)
		json.NewEncoder(w).Encode(map[string]any{"success": false, "error": "Session expired"})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	expiresAt := time.Now().Add(ttl)
	json.NewEncoder(w).Encode(map[string]any{
		"success":   true,
		"expiresAt": expiresAt.Unix(),
		"expiresIn": int(ttl.Seconds()),
	})
}


func (h *Handlers) renderLoginWithError(w http.ResponseWriter, r *http.Request, email, message string) {
	settings, err := h.repo.GetSystemSettings(r.Context())
	if err != nil && h.logger != nil && !errors.Is(err, context.Canceled) && !errors.Is(err, context.DeadlineExceeded) {
		h.logger.Error("login settings load", zap.Error(err))
	}
	token, err := h.sessions.IssueGuestCSRF(r.Context(), 10*time.Minute)
	if err != nil {
		http.Error(w, "no se pudo preparar el formulario", http.StatusInternalServerError)
		return
	}
	http.SetCookie(w, h.sessions.GuestCSRFCookie(token, 10*time.Minute))
	data := loginPageData{
		Email:    email,
		Error:    message,
		Settings: settings,
	}
	view := ui.ViewData{
		Title:     "Iniciar sesión",
		CSRFToken: token,
		Data:      data,
	}
	if err := h.renderer.Render(w, "login.html", view); err != nil && h.logger != nil {
		h.logger.Error("render login error", zap.Error(err))
	}
}
