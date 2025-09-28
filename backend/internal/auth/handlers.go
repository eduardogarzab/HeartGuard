package auth

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
	"heartguard-superadmin/internal/config"
	"heartguard-superadmin/internal/models"
)

// Interfaz mínima para romper el acoplamiento con superadmin.Repo
type AuthRepo interface {
	GetUserByEmail(ctx context.Context, email string) (*models.User, string, error)
	IssueRefreshToken(ctx context.Context, userID, tokenHash string, ttl time.Duration) error
	ValidateRefreshToken(ctx context.Context, raw string) (string, error)
	RevokeRefreshToken(ctx context.Context, raw string) error
}

type problem struct {
	Code    string            `json:"code"`
	Message string            `json:"message"`
	Fields  map[string]string `json:"fields,omitempty"`
}

func writeProblem(w http.ResponseWriter, status int, code, msg string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(problem{Code: code, Message: msg})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

type Handlers struct {
	cfg  *config.Config
	repo AuthRepo
}

func NewHandlers(cfg *config.Config, repo AuthRepo) *Handlers {
	return &Handlers{cfg: cfg, repo: repo}
}

type loginReq struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

func (h *Handlers) Login(w http.ResponseWriter, r *http.Request) {
	var req loginReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeProblem(w, http.StatusBadRequest, "bad_request", "invalid json")
		return
	}
	req.Email = strings.TrimSpace(strings.ToLower(req.Email))
	if req.Email == "" || req.Password == "" {
		writeProblem(w, http.StatusBadRequest, "bad_request", "email/password required")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	u, passHash, err := h.repo.GetUserByEmail(ctx, req.Email)
	if err != nil {
		writeProblem(w, http.StatusUnauthorized, "invalid_credentials", "email or password incorrect")
		return
	}
	if bcrypt.CompareHashAndPassword([]byte(passHash), []byte(req.Password)) != nil {
		writeProblem(w, http.StatusUnauthorized, "invalid_credentials", "email or password incorrect")
		return
	}

	jti := uuid.NewString()
	at, err := SignJWT(h.cfg.JWTSecret, u.ID, jti, h.cfg.AccessTokenTTL)
	if err != nil {
		writeProblem(w, http.StatusInternalServerError, "server_error", err.Error())
		return
	}

	rawRefresh, err := randomToken()
	if err != nil {
		writeProblem(w, http.StatusInternalServerError, "server_error", err.Error())
		return
	}
	sum := sha256.Sum256([]byte(rawRefresh))
	if err := h.repo.IssueRefreshToken(ctx, u.ID, hex.EncodeToString(sum[:]), h.cfg.RefreshTokenTTL); err != nil {
		writeProblem(w, http.StatusInternalServerError, "server_error", err.Error())
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"access_token":  at,
		"refresh_token": rawRefresh,
		"user":          u,
	})
}

type refreshReq struct {
	RefreshToken string `json:"refresh_token"`
}

func (h *Handlers) Refresh(w http.ResponseWriter, r *http.Request) {
	var req refreshReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeProblem(w, http.StatusBadRequest, "bad_request", "invalid json")
		return
	}
	if strings.TrimSpace(req.RefreshToken) == "" {
		writeProblem(w, http.StatusBadRequest, "bad_request", "missing token")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	uid, err := h.repo.ValidateRefreshToken(ctx, req.RefreshToken)
	if err != nil {
		writeProblem(w, http.StatusUnauthorized, "invalid_token", err.Error())
		return
	}

	// opcional: rotación de refresh
	if err := h.repo.RevokeRefreshToken(ctx, req.RefreshToken); err != nil {
		writeProblem(w, http.StatusUnauthorized, "invalid_token", err.Error())
		return
	}

	newRaw, err := randomToken()
	if err != nil {
		writeProblem(w, http.StatusInternalServerError, "server_error", err.Error())
		return
	}
	sum := sha256.Sum256([]byte(newRaw))
	if err := h.repo.IssueRefreshToken(ctx, uid, hex.EncodeToString(sum[:]), h.cfg.RefreshTokenTTL); err != nil {
		writeProblem(w, http.StatusInternalServerError, "server_error", err.Error())
		return
	}

	jti := uuid.NewString()
	at, err := SignJWT(h.cfg.JWTSecret, uid, jti, h.cfg.AccessTokenTTL)
	if err != nil {
		writeProblem(w, http.StatusInternalServerError, "server_error", err.Error())
		return
	}

	writeJSON(w, http.StatusOK, map[string]any{
		"access_token":  at,
		"refresh_token": newRaw,
	})
}

type logoutReq struct {
	RefreshToken string `json:"refresh_token"`
}

func (h *Handlers) Logout(w http.ResponseWriter, r *http.Request) {
	var req logoutReq
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeProblem(w, http.StatusBadRequest, "bad_request", "invalid json")
		return
	}
	if strings.TrimSpace(req.RefreshToken) == "" {
		writeProblem(w, http.StatusBadRequest, "bad_request", "missing token")
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	if err := h.repo.RevokeRefreshToken(ctx, req.RefreshToken); err != nil {
		writeProblem(w, http.StatusBadRequest, "invalid_token", err.Error())
		return
	}
	w.WriteHeader(http.StatusNoContent)
}

func randomToken() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	return hex.EncodeToString(b), nil
}
