package superadmin

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"net"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"go.uber.org/zap"
	"heartguard-superadmin/internal/audit"
	mw "heartguard-superadmin/internal/middleware"
)

type Handlers struct {
	repo     *Repo
	logger   *zap.Logger
	validate *validator.Validate
}

func NewHandlers(r *Repo, l *zap.Logger) *Handlers {
	v := validator.New(validator.WithRequiredStructEnabled())
	return &Handlers{repo: r, logger: l, validate: v}
}

type problem struct {
	Code    string            `json:"code"`
	Message string            `json:"message"`
	Fields  map[string]string `json:"fields,omitempty"`
}

func writeProblem(w http.ResponseWriter, status int, code, msg string, fields map[string]string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(problem{Code: code, Message: msg, Fields: fields})
}

func writeJSON(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func parseLimitOffset(r *http.Request) (int, int) {
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	if limit <= 0 || limit > 200 {
		limit = 50
	}
	offset, _ := strconv.Atoi(r.URL.Query().Get("offset"))
	if offset < 0 {
		offset = 0
	}
	return limit, offset
}

func decodeAndValidate[T any](r *http.Request, v *T, validate *validator.Validate) (map[string]string, error) {
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(v); err != nil {
		return nil, err
	}
	if err := validate.Struct(v); err != nil {
		if verrs, ok := err.(validator.ValidationErrors); ok {
			fe := make(map[string]string, len(verrs))
			for _, e := range verrs {
				fe[e.Field()] = e.Tag()
			}
			return fe, errors.New("validation error")
		}
		return nil, err
	}
	return nil, nil
}

// actorPtr recupera el user_id real (desde JWT) para auditoría.
func actorPtr(r *http.Request) *string {
	if v, ok := r.Context().Value(mw.CtxUserIDKey).(string); ok && v != "" {
		return &v
	}
	return nil
}

// clientIP intenta obtener la IP del cliente desde X-Forwarded-For o RemoteAddr.
func clientIP(r *http.Request) *string {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		ip := strings.TrimSpace(strings.Split(xff, ",")[0])
		if ip != "" {
			return &ip
		}
	}
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err == nil && host != "" {
		return &host
	}
	return nil
}

// Organizations

type orgReq struct {
	Code string `json:"code" validate:"required,uppercase,min=2,max=60"`
	Name string `json:"name" validate:"required,min=3,max=160"`
}

func (h *Handlers) CreateOrganization(w http.ResponseWriter, r *http.Request) {
	var req orgReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	org, err := h.repo.CreateOrganization(ctx, req.Code, req.Name)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "ORG_CREATE", "organization", &org.ID, map[string]any{"code": org.Code}, clientIP(r))
		c()
	}
	writeJSON(w, 201, org)
}

func (h *Handlers) ListOrganizations(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseLimitOffset(r)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListOrganizations(ctx, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

func (h *Handlers) GetOrganization(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	org, err := h.repo.GetOrganization(ctx, id)
	if err != nil {
		writeProblem(w, 404, "not_found", "organization not found", nil)
		return
	}
	writeJSON(w, 200, org)
}

type orgPatch struct {
	Code *string `json:"code"`
	Name *string `json:"name"`
}

func (h *Handlers) UpdateOrganization(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var req orgPatch
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", nil)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	org, err := h.repo.UpdateOrganization(ctx, id, req.Code, req.Name)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "ORG_UPDATE", "organization", &org.ID, map[string]any{"code": org.Code}, clientIP(r))
		c()
	}
	writeJSON(w, 200, org)
}

func (h *Handlers) DeleteOrganization(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteOrganization(ctx, id); err != nil {
		writeProblem(w, 404, "not_found", "organization not found", nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "ORG_DELETE", "organization", &id, nil, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

// Invitations

type inviteReq struct {
	OrgRoleID string  `json:"org_role_id" validate:"required,uuid4"`
	Email     *string `json:"email" validate:"omitempty,email"`
	TTLHours  int     `json:"ttl_hours" validate:"required,min=1,max=720"`
}

func (h *Handlers) CreateInvitation(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "id")
	var req inviteReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	inv, err := h.repo.CreateInvitation(ctx, orgID, req.OrgRoleID, req.Email, time.Duration(req.TTLHours)*time.Hour, actorPtr(r))
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "INVITE_CREATE", "org_invitation", &inv.ID, map[string]any{"org_id": orgID}, clientIP(r))
		c()
	}
	writeJSON(w, 201, inv)
}

type consumeReq struct {
	UserID string `json:"user_id" validate:"required,uuid4"`
}

func (h *Handlers) ConsumeInvitation(w http.ResponseWriter, r *http.Request) {
	token := chi.URLParam(r, "token")
	var req consumeReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.ConsumeInvitation(ctx, token, req.UserID); err != nil {
		writeProblem(w, 400, "invalid_token", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "INVITE_CONSUME", "org_invitation", nil, map[string]any{"token": token}, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

// Memberships

type addMemberReq struct {
	UserID    string `json:"user_id" validate:"required,uuid4"`
	OrgRoleID string `json:"org_role_id" validate:"required,uuid4"`
}

func (h *Handlers) AddMember(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "id")
	var req addMemberReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.AddMember(ctx, orgID, req.UserID, req.OrgRoleID); err != nil {
		writeProblem(w, 400, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "MEMBER_ADD", "membership", nil, map[string]any{"org_id": orgID}, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

func (h *Handlers) RemoveMember(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "id")
	userID := chi.URLParam(r, "userId")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.RemoveMember(ctx, orgID, userID); err != nil {
		writeProblem(w, 404, "not_found", "membership not found", nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "MEMBER_REMOVE", "membership", nil, map[string]any{"org_id": orgID}, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

// Users

func (h *Handlers) SearchUsers(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query().Get("q")
	limit, offset := parseLimitOffset(r)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.SearchUsers(ctx, q, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

type statusReq struct {
	Status string `json:"status" validate:"required,oneof=active blocked pending"`
}

func (h *Handlers) UpdateUserStatus(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var req statusReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.UpdateUserStatus(ctx, id, req.Status); err != nil {
		writeProblem(w, 400, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "USER_STATUS_UPDATE", "user", &id, map[string]any{"status": req.Status}, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

// API Keys

type apiKeyCreateReq struct {
	Label     string     `json:"label" validate:"required,min=3,max=120"`
	ExpiresAt *time.Time `json:"expires_at"`
	RawKey    string     `json:"raw_key" validate:"required,min=24"`
	OwnerUser *string    `json:"owner_user_id" validate:"omitempty,uuid4"`
}

func (h *Handlers) CreateAPIKey(w http.ResponseWriter, r *http.Request) {
	var req apiKeyCreateReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	hash := sha256.Sum256([]byte(req.RawKey))
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	id, err := h.repo.CreateAPIKey(ctx, req.Label, req.ExpiresAt, hex.EncodeToString(hash[:]), req.OwnerUser)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "APIKEY_CREATE", "api_key", &id, map[string]any{"label": req.Label}, clientIP(r))
		c()
	}
	writeJSON(w, 201, map[string]string{"id": id, "hash": hex.EncodeToString(hash[:])})
}

type apiKeyPermsReq struct {
	Permissions []string `json:"permissions" validate:"required,min=1,dive,required"`
}

func (h *Handlers) SetAPIKeyPermissions(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var req apiKeyPermsReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.SetAPIKeyPermissions(ctx, id, req.Permissions); err != nil {
		writeProblem(w, 400, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "APIKEY_SET_PERMS", "api_key", &id, map[string]any{"count": len(req.Permissions)}, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

func (h *Handlers) RevokeAPIKey(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.RevokeAPIKey(ctx, id); err != nil {
		writeProblem(w, 400, "db_error", err.Error(), nil)
		return
	}
	if ctxA, c := audit.Ctx(ctx); true {
		_ = audit.Write(ctxA, h.repo.pool, actorPtr(r), "APIKEY_REVOKE", "api_key", &id, nil, clientIP(r))
		c()
	}
	w.WriteHeader(204)
}

func (h *Handlers) ListAPIKeys(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseLimitOffset(r)
	activeOnly := parseBool(r.URL.Query().Get("active_only"), false)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListAPIKeys(ctx, activeOnly, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

// Audit

func (h *Handlers) ListAuditLogs(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	var from, to *time.Time
	if s := q.Get("from"); s != "" {
		if t, err := time.Parse(time.RFC3339, s); err == nil {
			from = &t
		}
	}
	if s := q.Get("to"); s != "" {
		if t, err := time.Parse(time.RFC3339, s); err == nil {
			to = &t
		}
	}
	var action *string
	if s := q.Get("action"); s != "" {
		action = &s
	}
	limit, offset := parseLimitOffset(r)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListAudit(ctx, from, to, action, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

// Healthz
func (h *Handlers) Healthz(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	if err := h.repo.pool.Ping(ctx); err != nil {
		writeProblem(w, http.StatusServiceUnavailable, "db_down", err.Error(), nil)
		return
	}
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
}

// Helpers

func parseBool(s string, def bool) bool {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "1", "t", "true", "yes", "y":
		return true
	case "0", "f", "false", "no", "n":
		return false
	default:
		return def
	}
}
