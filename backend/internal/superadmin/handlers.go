//go:build rest_api_legacy
// +build rest_api_legacy

package superadmin

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
	"unicode"

	"heartguard-superadmin/internal/audit"
	mw "heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/models"

	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
	gofpdf "github.com/jung-kurt/gofpdf"
	"go.uber.org/zap"
)

type Repository interface {
	AuditPool() *pgxpool.Pool
	Ping(context.Context) error

	CreateOrganization(ctx context.Context, code, name string) (*models.Organization, error)
	ListOrganizations(ctx context.Context, limit, offset int) ([]models.Organization, error)
	GetOrganization(ctx context.Context, id string) (*models.Organization, error)
	UpdateOrganization(ctx context.Context, id string, code, name *string) (*models.Organization, error)
	DeleteOrganization(ctx context.Context, id string) error

	CreateInvitation(ctx context.Context, orgID, orgRoleID string, email *string, ttlHours int, createdBy *string) (*models.OrgInvitation, error)
	ListInvitations(ctx context.Context, orgID *string, limit, offset int) ([]models.OrgInvitation, error)
	ConsumeInvitation(ctx context.Context, token, userID string) error
	CancelInvitation(ctx context.Context, invitationID string) error

	AddMember(ctx context.Context, orgID, userID, orgRoleID string) error
	RemoveMember(ctx context.Context, orgID, userID string) error
	ListMembers(ctx context.Context, orgID string, limit, offset int) ([]models.Membership, error)

	ListCatalog(ctx context.Context, catalog string, limit, offset int) ([]models.CatalogItem, error)
	CreateCatalogItem(ctx context.Context, catalog, code, label string, weight *int) (*models.CatalogItem, error)
	UpdateCatalogItem(ctx context.Context, catalog, id string, code, label *string, weight *int) (*models.CatalogItem, error)
	DeleteCatalogItem(ctx context.Context, catalog, id string) error

	ListContent(ctx context.Context, filters models.ContentFilters) ([]models.ContentItem, error)
	GetContent(ctx context.Context, id string) (*models.ContentDetail, error)
	CreateContent(ctx context.Context, input models.ContentCreateInput, actorID *string) (*models.ContentDetail, error)
	UpdateContent(ctx context.Context, id string, input models.ContentUpdateInput, actorID *string) (*models.ContentDetail, error)
	DeleteContent(ctx context.Context, id string) error
	ListContentVersions(ctx context.Context, id string, limit, offset int) ([]models.ContentVersion, error)

	MetricsOverview(ctx context.Context) (*models.MetricsOverview, error)
	MetricsRecentActivity(ctx context.Context, limit int) ([]models.ActivityEntry, error)
	MetricsUserStatusBreakdown(ctx context.Context) ([]models.StatusBreakdown, error)
	MetricsInvitationBreakdown(ctx context.Context) ([]models.InvitationBreakdown, error)
	MetricsContentSnapshot(ctx context.Context) (*models.ContentMetrics, error)
	MetricsContentReport(ctx context.Context, filters models.ContentReportFilters) (*models.ContentReportResult, error)
	MetricsOperationsReport(ctx context.Context, filters models.OperationsReportFilters) (*models.OperationsReportResult, error)
	MetricsUserActivityReport(ctx context.Context, filters models.UserActivityReportFilters) (*models.UserActivityReportResult, error)

	SearchUsers(ctx context.Context, q string, limit, offset int) ([]models.User, error)
	UpdateUserStatus(ctx context.Context, userID, status string) error
	ListRoles(ctx context.Context, limit, offset int) ([]models.Role, error)
	CreateRole(ctx context.Context, name string, description *string) (*models.Role, error)
	UpdateRole(ctx context.Context, id string, name, description *string) (*models.Role, error)
	DeleteRole(ctx context.Context, id string) error
	ListUserRoles(ctx context.Context, userID string) ([]models.UserRole, error)
	AssignRoleToUser(ctx context.Context, userID, roleID string) (*models.UserRole, error)
	RemoveRoleFromUser(ctx context.Context, userID, roleID string) error
	GetSystemSettings(ctx context.Context) (*models.SystemSettings, error)
	UpdateSystemSettings(ctx context.Context, payload models.SystemSettingsInput, updatedBy *string) (*models.SystemSettings, error)

	CreateAPIKey(ctx context.Context, label string, expires *time.Time, hashHex string, ownerUserID *string) (string, error)
	SetAPIKeyPermissions(ctx context.Context, id string, permCodes []string) error
	RevokeAPIKey(ctx context.Context, id string) error
	ListAPIKeys(ctx context.Context, activeOnly bool, limit, offset int) ([]models.APIKey, error)
	ListPermissions(ctx context.Context) ([]models.Permission, error)

	ListAudit(ctx context.Context, from, to *time.Time, action *string, limit, offset int) ([]models.AuditLog, error)
}

type Handlers struct {
	repo     Repository
	logger   *zap.Logger
	validate *validator.Validate
}

func NewHandlers(r Repository, l *zap.Logger) *Handlers {
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

func humanizeToken(input string) string {
	if input == "" {
		return ""
	}
	normalized := strings.ReplaceAll(strings.ReplaceAll(input, "-", " "), "_", " ")
	chunks := strings.Fields(strings.ToLower(normalized))
	for i, chunk := range chunks {
		runes := []rune(chunk)
		if len(runes) == 0 {
			continue
		}
		runes[0] = unicode.ToUpper(runes[0])
		chunks[i] = string(runes)
	}
	return strings.Join(chunks, " ")
}

func computePeriodDays(from, to *time.Time) int {
	if from != nil && to != nil {
		start := from.Truncate(24 * time.Hour)
		end := to.Truncate(24 * time.Hour)
		if !end.After(start) {
			return 1
		}
		return int(end.Sub(start).Hours()/24) + 1
	}
	if from != nil {
		start := from.Truncate(24 * time.Hour)
		now := time.Now().Truncate(24 * time.Hour)
		if !now.After(start) {
			return 1
		}
		return int(now.Sub(start).Hours()/24) + 1
	}
	if to != nil {
		end := to.Truncate(24 * time.Hour)
		start := end.AddDate(0, 0, -29)
		return int(end.Sub(start).Hours()/24) + 1
	}
	return 30
}

func formatTimestampLocal(ts *time.Time) string {
	if ts == nil {
		return ""
	}
	return ts.In(time.Local).Format("2006-01-02 15:04")
}

func averagePerDay(total int, days int) float64 {
	if days <= 0 {
		days = 1
	}
	return float64(total) / float64(days)
}

var operationLabels = map[string]string{
	"ORG_CREATE":         "Alta de organización",
	"ORG_UPDATE":         "Actualización de organización",
	"ORG_DELETE":         "Eliminación de organización",
	"INVITE_CREATE":      "Emisión de invitación",
	"INVITE_CANCEL":      "Cancelación de invitación",
	"INVITE_CONSUME":     "Consumo de invitación",
	"MEMBER_ADD":         "Alta de miembro",
	"MEMBER_REMOVE":      "Baja de miembro",
	"USER_STATUS_UPDATE": "Actualización de estatus de usuario",
	"APIKEY_CREATE":      "Creación de API Key",
	"APIKEY_SET_PERMS":   "Configuración de permisos de API Key",
	"APIKEY_REVOKE":      "Revocación de API Key",
	"CATALOG_CREATE":     "Alta en catálogo",
	"CATALOG_UPDATE":     "Actualización de catálogo",
	"CATALOG_DELETE":     "Eliminación de catálogo",
	"AUDIT_EXPORT":       "Exportación de auditoría",
}

func operationLabel(code string) string {
	if code == "" {
		return ""
	}
	upper := strings.ToUpper(code)
	if label, ok := operationLabels[upper]; ok {
		return label
	}
	return humanizeToken(upper)
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

func (h *Handlers) writeAudit(ctx context.Context, r *http.Request, action, entity string, entityID *string, details map[string]any) {
	pool := h.repo.AuditPool()
	if pool == nil {
		return
	}
	ctxA, cancel := audit.Ctx(ctx)
	defer cancel()
	_ = audit.Write(ctxA, pool, actorPtr(r), action, entity, entityID, details, nil)
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
	h.writeAudit(ctx, r, "ORG_CREATE", "organization", &org.ID, map[string]any{"code": org.Code})
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
	h.writeAudit(ctx, r, "ORG_UPDATE", "organization", &org.ID, map[string]any{"code": org.Code})
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
	h.writeAudit(ctx, r, "ORG_DELETE", "organization", &id, nil)
	w.WriteHeader(204)
}

// Invitations

type catalogMeta struct {
	Label          string
	RequiresWeight bool
}

var allowedCatalogs = map[string]catalogMeta{
	"user_statuses":         {Label: "Estatus de usuarios"},
	"signal_types":          {Label: "Tipos de señal"},
	"alert_channels":        {Label: "Canales de alerta"},
	"alert_levels":          {Label: "Niveles de alerta", RequiresWeight: true},
	"sexes":                 {Label: "Sexos"},
	"platforms":             {Label: "Plataformas"},
	"service_statuses":      {Label: "Estados de servicio"},
	"delivery_statuses":     {Label: "Estados de entrega"},
	"batch_export_statuses": {Label: "Estados de exportación"},
	"org_roles":             {Label: "Roles de organización"},
	"content_statuses":      {Label: "Estatus de contenido", RequiresWeight: true},
	"content_categories":    {Label: "Categorías de contenido"},
}

func catalogInfo(slug string) (catalogMeta, bool) {
	meta, ok := allowedCatalogs[slug]
	return meta, ok
}

type inviteReq struct {
	OrgID     string  `json:"org_id" validate:"required,uuid4"`
	OrgRoleID string  `json:"org_role_id" validate:"required,uuid4"`
	Email     *string `json:"email" validate:"omitempty,email"`
	TTLHours  int     `json:"ttl_hours" validate:"required,min=1,max=720"`
}

func (h *Handlers) CreateInvitation(w http.ResponseWriter, r *http.Request) {
	var req inviteReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	inv, err := h.repo.CreateInvitation(ctx, req.OrgID, req.OrgRoleID, req.Email, req.TTLHours, actorPtr(r))
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "org role not found", nil)
			return
		}
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23503" {
			writeProblem(w, 400, "constraint_violation", pgErr.Message, nil)
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "INVITE_CREATE", "org_invitation", &inv.ID, map[string]any{"org_id": req.OrgID})
	writeJSON(w, 201, inv)
}

func (h *Handlers) ListInvitations(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseLimitOffset(r)
	var orgID *string
	if s := strings.TrimSpace(r.URL.Query().Get("org_id")); s != "" {
		orgID = &s
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListInvitations(ctx, orgID, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
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
	h.writeAudit(ctx, r, "INVITE_CONSUME", "org_invitation", nil, map[string]any{"token": token})
	w.WriteHeader(204)
}

func (h *Handlers) CancelInvitation(w http.ResponseWriter, r *http.Request) {
	invitationID := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.CancelInvitation(ctx, invitationID); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "invitation not found or already processed", nil)
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "INVITE_CANCEL", "org_invitation", &invitationID, nil)
	w.WriteHeader(204)
}

// Catalogs

type catalogCreateReq struct {
	Code   string `json:"code" validate:"required,min=1,max=60"`
	Label  string `json:"label" validate:"required,min=1,max=160"`
	Weight *int   `json:"weight"`
}

type catalogUpdateReq struct {
	Code   *string `json:"code"`
	Label  *string `json:"label"`
	Weight *int    `json:"weight"`
}

func (h *Handlers) ListCatalog(w http.ResponseWriter, r *http.Request) {
	catalog := chi.URLParam(r, "catalog")
	if _, ok := catalogInfo(catalog); !ok {
		writeProblem(w, 404, "not_found", "catalog not found", nil)
		return
	}
	limit, offset := parseLimitOffset(r)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListCatalog(ctx, catalog, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

func (h *Handlers) CreateCatalogItem(w http.ResponseWriter, r *http.Request) {
	catalog := chi.URLParam(r, "catalog")
	meta, ok := catalogInfo(catalog)
	if !ok {
		writeProblem(w, 404, "not_found", "catalog not found", nil)
		return
	}
	var req catalogCreateReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	code := strings.TrimSpace(req.Code)
	label := strings.TrimSpace(req.Label)
	fieldErrors := make(map[string]string)
	if code == "" {
		fieldErrors["code"] = "required"
	}
	if label == "" {
		fieldErrors["label"] = "required"
	}
	if len(fieldErrors) > 0 {
		writeProblem(w, 422, "validation_error", "code and label are required", fieldErrors)
		return
	}
	weight := req.Weight
	if meta.RequiresWeight {
		if weight == nil {
			writeProblem(w, 422, "validation_error", "weight is required for this catalog", map[string]string{"weight": "required"})
			return
		}
	} else {
		weight = nil
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	item, err := h.repo.CreateCatalogItem(ctx, catalog, code, label, weight)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) {
			switch pgErr.Code {
			case "23505":
				writeProblem(w, 409, "conflict", "duplicate entry", nil)
				return
			case "23503":
				writeProblem(w, 400, "constraint_violation", pgErr.Message, nil)
				return
			}
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "CATALOG_CREATE", "catalog_item", &item.ID, map[string]any{"catalog": catalog})
	writeJSON(w, 201, item)
}

func (h *Handlers) UpdateCatalogItem(w http.ResponseWriter, r *http.Request) {
	catalog := chi.URLParam(r, "catalog")
	meta, ok := catalogInfo(catalog)
	if !ok {
		writeProblem(w, 404, "not_found", "catalog not found", nil)
		return
	}
	id := chi.URLParam(r, "id")
	var req catalogUpdateReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	var trimmedCode *string
	if req.Code != nil {
		val := strings.TrimSpace(*req.Code)
		if val == "" {
			writeProblem(w, 422, "validation_error", "code cannot be empty", map[string]string{"code": "required"})
			return
		}
		trimmedCode = &val
	}
	var trimmedLabel *string
	if req.Label != nil {
		val := strings.TrimSpace(*req.Label)
		if val == "" {
			writeProblem(w, 422, "validation_error", "label cannot be empty", map[string]string{"label": "required"})
			return
		}
		trimmedLabel = &val
	}
	weight := req.Weight
	if !meta.RequiresWeight {
		weight = nil
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	item, err := h.repo.UpdateCatalogItem(ctx, catalog, id, trimmedCode, trimmedLabel, weight)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "catalog item not found", nil)
			return
		}
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			writeProblem(w, 409, "conflict", "duplicate entry", nil)
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "CATALOG_UPDATE", "catalog_item", &item.ID, map[string]any{"catalog": catalog})
	writeJSON(w, 200, item)
}

func (h *Handlers) DeleteCatalogItem(w http.ResponseWriter, r *http.Request) {
	catalog := chi.URLParam(r, "catalog")
	if _, ok := catalogInfo(catalog); !ok {
		writeProblem(w, 404, "not_found", "catalog not found", nil)
		return
	}
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteCatalogItem(ctx, catalog, id); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "catalog item not found", nil)
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "CATALOG_DELETE", "catalog_item", &id, map[string]any{"catalog": catalog})
	w.WriteHeader(204)
}

// Metrics

func (h *Handlers) MetricsOverview(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	data, err := h.repo.MetricsOverview(ctx)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, data)
}

func (h *Handlers) MetricsRecentActivity(w http.ResponseWriter, r *http.Request) {
	limit, _ := strconv.Atoi(r.URL.Query().Get("limit"))
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.MetricsRecentActivity(ctx, limit)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

func (h *Handlers) MetricsUserStatusBreakdown(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.MetricsUserStatusBreakdown(ctx)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

func (h *Handlers) MetricsInvitationBreakdown(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.MetricsInvitationBreakdown(ctx)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

func (h *Handlers) MetricsContentInsights(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	data, err := h.repo.MetricsContentSnapshot(ctx)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, data)
}

func parseDateParam(raw string) (*time.Time, error) {
	value := strings.TrimSpace(raw)
	if value == "" {
		return nil, nil
	}
	if t, err := time.Parse("2006-01-02", value); err == nil {
		return &t, nil
	}
	if t, err := time.Parse(time.RFC3339, value); err == nil {
		return &t, nil
	}
	return nil, fmt.Errorf("invalid date")
}

func (h *Handlers) MetricsOperationsReport(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseLimitOffset(r)
	q := r.URL.Query()

	from, err := parseDateParam(q.Get("from"))
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid 'from' date", map[string]string{"from": "invalid"})
		return
	}
	to, err := parseDateParam(q.Get("to"))
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid 'to' date", map[string]string{"to": "invalid"})
		return
	}
	if from != nil && to != nil && to.Before(*from) {
		writeProblem(w, 400, "bad_request", "'to' must be on or after 'from'", map[string]string{"to": "before_from"})
		return
	}

	var (
		actionPtr    *string
		actionFilter string
	)
	if v := strings.TrimSpace(q.Get("action")); v != "" {
		actionFilter = strings.ToUpper(v)
		actionPtr = &actionFilter
	}

	format := strings.ToLower(strings.TrimSpace(q.Get("format")))
	filters := models.OperationsReportFilters{
		From:   from,
		To:     to,
		Action: actionPtr,
		Limit:  limit,
		Offset: offset,
	}

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	result, err := h.repo.MetricsOperationsReport(ctx, filters)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	if result == nil {
		result = &models.OperationsReportResult{}
	}
	if result.Rows == nil {
		result.Rows = make([]models.OperationsReportRow, 0)
	}
	result.Limit = limit
	result.Offset = offset

	periodDays := computePeriodDays(filters.From, filters.To)
	result.PeriodDays = periodDays
	for i := range result.Rows {
		row := &result.Rows[i]
		row.ActionLabel = operationLabel(row.Action)
		row.AvgPerDay = averagePerDay(row.TotalEvents, periodDays)
	}

	filename := fmt.Sprintf("operaciones-%s", time.Now().Format("20060102-150405"))

	switch format {
	case "csv":
		w.Header().Set("Content-Type", "text/csv; charset=utf-8")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.csv\"", filename))
		if _, err := w.Write([]byte{0xEF, 0xBB, 0xBF}); err != nil {
			if h.logger != nil {
				h.logger.Error("csv bom write error", zap.Error(err))
			}
		}
		writer := csv.NewWriter(w)
		headers := []string{"Acción", "Código", "Eventos", "Usuarios únicos", "Entidades únicas", "Primera actividad", "Última actividad", "Promedio diario"}
		if err := writer.Write(headers); err != nil {
			if h.logger != nil {
				h.logger.Error("csv header write error", zap.Error(err))
			}
			writer.Flush()
			h.writeAudit(ctx, r, "AUDIT_EXPORT", "operations_report", nil, map[string]any{"format": "csv", "rows": len(result.Rows)})
			return
		}
		for _, row := range result.Rows {
			record := []string{
				row.ActionLabel,
				row.Action,
				strconv.Itoa(row.TotalEvents),
				strconv.Itoa(row.UniqueUsers),
				strconv.Itoa(row.UniqueEntities),
				formatTimestampLocal(row.FirstEvent),
				formatTimestampLocal(row.LastEvent),
				fmt.Sprintf("%.2f", row.AvgPerDay),
			}
			if err := writer.Write(record); err != nil {
				if h.logger != nil {
					h.logger.Error("csv row write error", zap.Error(err))
				}
				break
			}
		}
		writer.Flush()
		if err := writer.Error(); err != nil && h.logger != nil {
			h.logger.Error("csv export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "AUDIT_EXPORT", "operations_report", nil, map[string]any{
			"format": "csv",
			"rows":   len(result.Rows),
			"from":   q.Get("from"),
			"to":     q.Get("to"),
			"action": actionFilter,
		})
		return
	case "pdf":
		w.Header().Set("Content-Type", "application/pdf")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.pdf\"", filename))
		pdf := gofpdf.New("L", "mm", "A4", "")
		pdf.SetTitle("Reporte de operaciones", false)
		pdf.SetMargins(12, 16, 12)
		pdf.SetAutoPageBreak(true, 18)
		pdf.AddPage()
		translator := pdf.UnicodeTranslatorFromDescriptor("")
		pdf.SetFont("Helvetica", "B", 16)
		pdf.Cell(0, 10, translator("Resumen de operaciones"))
		pdf.Ln(12)
		pdf.SetFont("Helvetica", "", 11)
		meta := fmt.Sprintf("Generado %s | Periodo %d días | Total filas %d", time.Now().Format("02/01/2006 15:04"), periodDays, result.Total)
		pdf.Cell(0, 8, translator(meta))
		pdf.Ln(10)
		headers := []string{"Acción", "Código", "Eventos", "Usuarios únicos", "Entidades únicas", "Primera actividad", "Última actividad", "Promedio diario"}
		widths := []float64{58, 34, 26, 32, 32, 42, 42, 30}
		rowHeight := 6.2
		pdf.SetFont("Helvetica", "B", 10)
		pdf.SetFillColor(40, 64, 96)
		pdf.SetDrawColor(210, 218, 235)
		pdf.SetLineWidth(0.15)
		pdf.SetTextColor(255, 255, 255)
		for i, head := range headers {
			pdf.CellFormat(widths[i], 8, translator(head), "1", 0, "L", true, 0, "")
		}
		pdf.Ln(-1)
		pdf.SetFont("Helvetica", "", 9)
		pdf.SetTextColor(0, 0, 0)
		fill := false
		leftMargin, _, _, _ := pdf.GetMargins()
		dash := translator("-")
		formatDate := func(ts *time.Time) string {
			if ts == nil {
				return dash
			}
			str := formatTimestampLocal(ts)
			if str == "" {
				return dash
			}
			return translator(str)
		}
		for _, row := range result.Rows {
			fill = !fill
			if fill {
				pdf.SetFillColor(245, 247, 252)
			} else {
				pdf.SetFillColor(255, 255, 255)
			}
			label := strings.TrimSpace(row.ActionLabel)
			if label == "" {
				label = "-"
			}
			label = translator(label)
			labelLines := pdf.SplitLines([]byte(label), widths[0])
			cellHeight := float64(len(labelLines)) * rowHeight
			if cellHeight < rowHeight {
				cellHeight = rowHeight
			}
			y := pdf.GetY()
			pdf.SetXY(leftMargin, y)
			pdf.MultiCell(widths[0], rowHeight, label, "1", "L", fill)
			x := leftMargin + widths[0]
			pdf.SetXY(x, y)
			pdf.CellFormat(widths[1], cellHeight, translator(row.Action), "1", 0, "L", fill, 0, "")
			x += widths[1]
			pdf.SetXY(x, y)
			pdf.CellFormat(widths[2], cellHeight, strconv.Itoa(row.TotalEvents), "1", 0, "R", fill, 0, "")
			x += widths[2]
			pdf.CellFormat(widths[3], cellHeight, strconv.Itoa(row.UniqueUsers), "1", 0, "R", fill, 0, "")
			x += widths[3]
			pdf.CellFormat(widths[4], cellHeight, strconv.Itoa(row.UniqueEntities), "1", 0, "R", fill, 0, "")
			x += widths[4]
			pdf.CellFormat(widths[5], cellHeight, formatDate(row.FirstEvent), "1", 0, "L", fill, 0, "")
			x += widths[5]
			pdf.CellFormat(widths[6], cellHeight, formatDate(row.LastEvent), "1", 0, "L", fill, 0, "")
			x += widths[6]
			pdf.CellFormat(widths[7], cellHeight, fmt.Sprintf("%.2f", row.AvgPerDay), "1", 0, "R", fill, 0, "")
			pdf.SetXY(leftMargin, y+cellHeight)
		}
		if err := pdf.Output(w); err != nil && h.logger != nil {
			h.logger.Error("pdf export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "AUDIT_EXPORT", "operations_report", nil, map[string]any{
			"format": "pdf",
			"rows":   len(result.Rows),
			"from":   q.Get("from"),
			"to":     q.Get("to"),
			"action": actionFilter,
		})
		return
	default:
		w.Header().Set("X-Total-Count", strconv.Itoa(result.Total))
		writeJSON(w, 200, result)
	}
}

func (h *Handlers) MetricsUsersReport(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseLimitOffset(r)
	q := r.URL.Query()

	from, err := parseDateParam(q.Get("from"))
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid 'from' date", map[string]string{"from": "invalid"})
		return
	}
	to, err := parseDateParam(q.Get("to"))
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid 'to' date", map[string]string{"to": "invalid"})
		return
	}
	if from != nil && to != nil && to.Before(*from) {
		writeProblem(w, 400, "bad_request", "'to' must be on or after 'from'", map[string]string{"to": "before_from"})
		return
	}

	var (
		statusFilter string
		statusPtr    *string
		searchValue  string
		searchPtr    *string
	)
	if v := strings.TrimSpace(q.Get("status")); v != "" {
		statusFilter = strings.ToLower(v)
		statusPtr = &statusFilter
	}
	if v := strings.TrimSpace(q.Get("search")); v != "" {
		searchValue = v
		searchPtr = &searchValue
	}

	format := strings.ToLower(strings.TrimSpace(q.Get("format")))
	filters := models.UserActivityReportFilters{
		From:   from,
		To:     to,
		Status: statusPtr,
		Search: searchPtr,
		Limit:  limit,
		Offset: offset,
	}

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()

	result, err := h.repo.MetricsUserActivityReport(ctx, filters)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	if result == nil {
		result = &models.UserActivityReportResult{}
	}
	if result.Rows == nil {
		result.Rows = make([]models.UserActivityReportRow, 0)
	}
	result.Limit = limit
	result.Offset = offset

	periodDays := computePeriodDays(filters.From, filters.To)
	result.PeriodDays = periodDays
	for i := range result.Rows {
		row := &result.Rows[i]
		if row.StatusLabel == "" {
			row.StatusLabel = humanizeToken(row.StatusCode)
		}
		row.AvgActionsPerDay = averagePerDay(row.ActionsCount, periodDays)
	}

	filename := fmt.Sprintf("usuarios-%s", time.Now().Format("20060102-150405"))

	switch format {
	case "csv":
		w.Header().Set("Content-Type", "text/csv; charset=utf-8")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.csv\"", filename))
		if _, err := w.Write([]byte{0xEF, 0xBB, 0xBF}); err != nil {
			if h.logger != nil {
				h.logger.Error("csv bom write error", zap.Error(err))
			}
		}
		writer := csv.NewWriter(w)
		headers := []string{"Nombre", "Email", "Estatus", "Organizaciones", "Acciones periodo", "Acciones únicas", "Primera actividad", "Última actividad", "Promedio diario", "Registrado"}
		if err := writer.Write(headers); err != nil {
			if h.logger != nil {
				h.logger.Error("csv header write error", zap.Error(err))
			}
			writer.Flush()
			h.writeAudit(ctx, r, "AUDIT_EXPORT", "users_report", nil, map[string]any{"format": "csv", "rows": len(result.Rows)})
			return
		}
		for _, row := range result.Rows {
			name := row.Name
			if strings.TrimSpace(name) == "" {
				name = row.Email
			}
			record := []string{
				name,
				row.Email,
				row.StatusLabel,
				strconv.Itoa(row.Organizations),
				strconv.Itoa(row.ActionsCount),
				strconv.Itoa(row.DistinctActions),
				formatTimestampLocal(row.FirstAction),
				formatTimestampLocal(row.LastAction),
				fmt.Sprintf("%.2f", row.AvgActionsPerDay),
				row.CreatedAt.In(time.Local).Format("2006-01-02 15:04"),
			}
			if err := writer.Write(record); err != nil {
				if h.logger != nil {
					h.logger.Error("csv row write error", zap.Error(err))
				}
				break
			}
		}
		writer.Flush()
		if err := writer.Error(); err != nil && h.logger != nil {
			h.logger.Error("csv export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "AUDIT_EXPORT", "users_report", nil, map[string]any{
			"format": "csv",
			"rows":   len(result.Rows),
			"from":   q.Get("from"),
			"to":     q.Get("to"),
			"status": statusFilter,
			"search": searchValue,
		})
		return
	case "pdf":
		w.Header().Set("Content-Type", "application/pdf")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.pdf\"", filename))
		pdf := gofpdf.New("L", "mm", "A4", "")
		pdf.SetTitle("Reporte de usuarios", false)
		pdf.SetMargins(12, 16, 12)
		pdf.SetAutoPageBreak(true, 18)
		pdf.AddPage()
		translator := pdf.UnicodeTranslatorFromDescriptor("")
		pdf.SetFont("Helvetica", "B", 16)
		pdf.Cell(0, 10, translator("Actividad de usuarios"))
		pdf.Ln(12)
		pdf.SetFont("Helvetica", "", 11)
		meta := fmt.Sprintf("Generado %s | Periodo %d días | Total filas %d", time.Now().Format("02/01/2006 15:04"), periodDays, result.Total)
		pdf.Cell(0, 8, translator(meta))
		pdf.Ln(10)
		headers := []string{"Nombre", "Email", "Estatus", "Org", "Acciones", "Únicas", "Primera actividad", "Última actividad", "Promedio diario"}
		widths := []float64{52, 58, 30, 18, 24, 26, 38, 38, 30}
		rowHeight := 6.0
		pdf.SetFont("Helvetica", "B", 10)
		pdf.SetFillColor(40, 64, 96)
		pdf.SetDrawColor(210, 218, 235)
		pdf.SetLineWidth(0.15)
		pdf.SetTextColor(255, 255, 255)
		for i, head := range headers {
			pdf.CellFormat(widths[i], 8, translator(head), "1", 0, "L", true, 0, "")
		}
		pdf.Ln(-1)
		pdf.SetFont("Helvetica", "", 9)
		pdf.SetTextColor(0, 0, 0)
		fill := false
		leftMargin, _, _, _ := pdf.GetMargins()
		dash := translator("-")
		formatDate := func(ts *time.Time) string {
			if ts == nil {
				return dash
			}
			str := formatTimestampLocal(ts)
			if str == "" {
				return dash
			}
			return translator(str)
		}
		for _, row := range result.Rows {
			fill = !fill
			if fill {
				pdf.SetFillColor(245, 247, 252)
			} else {
				pdf.SetFillColor(255, 255, 255)
			}
			name := strings.TrimSpace(row.Name)
			if name == "" {
				name = row.Email
			}
			if name == "" {
				name = "-"
			}
			nameText := translator(name)
			emailText := translator(row.Email)
			if emailText == "" {
				emailText = dash
			}
			statusText := translator(row.StatusLabel)
			nameLines := pdf.SplitLines([]byte(nameText), widths[0])
			emailLines := pdf.SplitLines([]byte(emailText), widths[1])
			maxLines := len(nameLines)
			if len(emailLines) > maxLines {
				maxLines = len(emailLines)
			}
			if maxLines < 1 {
				maxLines = 1
			}
			cellHeight := float64(maxLines) * rowHeight
			y := pdf.GetY()
			pdf.SetXY(leftMargin, y)
			pdf.MultiCell(widths[0], rowHeight, nameText, "1", "L", fill)
			x := leftMargin + widths[0]
			pdf.SetXY(x, y)
			pdf.MultiCell(widths[1], rowHeight, emailText, "1", "L", fill)
			x += widths[1]
			pdf.SetXY(x, y)
			pdf.CellFormat(widths[2], cellHeight, statusText, "1", 0, "L", fill, 0, "")
			x += widths[2]
			pdf.CellFormat(widths[3], cellHeight, strconv.Itoa(row.Organizations), "1", 0, "C", fill, 0, "")
			x += widths[3]
			pdf.CellFormat(widths[4], cellHeight, strconv.Itoa(row.ActionsCount), "1", 0, "R", fill, 0, "")
			x += widths[4]
			pdf.CellFormat(widths[5], cellHeight, strconv.Itoa(row.DistinctActions), "1", 0, "R", fill, 0, "")
			x += widths[5]
			pdf.CellFormat(widths[6], cellHeight, formatDate(row.FirstAction), "1", 0, "L", fill, 0, "")
			x += widths[6]
			pdf.CellFormat(widths[7], cellHeight, formatDate(row.LastAction), "1", 0, "L", fill, 0, "")
			x += widths[7]
			pdf.CellFormat(widths[8], cellHeight, fmt.Sprintf("%.2f", row.AvgActionsPerDay), "1", 0, "R", fill, 0, "")
			pdf.SetXY(leftMargin, y+cellHeight)
		}
		if err := pdf.Output(w); err != nil && h.logger != nil {
			h.logger.Error("pdf export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "AUDIT_EXPORT", "users_report", nil, map[string]any{
			"format": "pdf",
			"rows":   len(result.Rows),
			"from":   q.Get("from"),
			"to":     q.Get("to"),
			"status": statusFilter,
			"search": searchValue,
		})
		return
	default:
		w.Header().Set("X-Total-Count", strconv.Itoa(result.Total))
		writeJSON(w, 200, result)
	}
}

func (h *Handlers) MetricsContentReport(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	limit := 50
	if raw := strings.TrimSpace(q.Get("limit")); raw != "" {
		if val, err := strconv.Atoi(raw); err == nil {
			limit = val
		}
	}
	if limit <= 0 {
		limit = 50
	} else if limit > 500 {
		limit = 500
	}
	offset := 0
	if raw := strings.TrimSpace(q.Get("offset")); raw != "" {
		if val, err := strconv.Atoi(raw); err == nil && val >= 0 {
			offset = val
		}
	}

	from, err := parseDateParam(q.Get("from"))
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid 'from' date", map[string]string{"from": "invalid"})
		return
	}
	to, err := parseDateParam(q.Get("to"))
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid 'to' date", map[string]string{"to": "invalid"})
		return
	}

	var statusPtr *string
	if v := strings.TrimSpace(q.Get("status")); v != "" {
		s := v
		statusPtr = &s
	}
	var categoryPtr *string
	if v := strings.TrimSpace(q.Get("category")); v != "" {
		s := v
		categoryPtr = &s
	}
	var searchPtr *string
	if v := strings.TrimSpace(q.Get("search")); v != "" {
		s := v
		searchPtr = &s
	}
	sortKey := strings.TrimSpace(q.Get("sort"))
	direction := strings.ToLower(strings.TrimSpace(q.Get("direction")))
	if direction != "asc" {
		direction = "desc"
	}
	format := strings.ToLower(strings.TrimSpace(q.Get("format")))

	filters := models.ContentReportFilters{
		From:      from,
		To:        to,
		Status:    statusPtr,
		Category:  categoryPtr,
		Search:    searchPtr,
		Sort:      sortKey,
		Direction: direction,
		Limit:     limit,
		Offset:    offset,
	}

	ctx, cancel := context.WithTimeout(r.Context(), 10*time.Second)
	defer cancel()
	result, err := h.repo.MetricsContentReport(ctx, filters)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}

	formatTimestamp := func(t *time.Time) string {
		if t == nil {
			return ""
		}
		return t.In(time.Local).Format("2006-01-02 15:04")
	}
	valueOrEmpty := func(v *string) string {
		if v == nil {
			return ""
		}
		return *v
	}

	filename := fmt.Sprintf("contenido-%s", time.Now().Format("20060102-150405"))

	switch format {
	case "csv":
		w.Header().Set("Content-Type", "text/csv; charset=utf-8")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.csv\"", filename))
		if _, err := w.Write([]byte{0xEF, 0xBB, 0xBF}); err != nil {
			if h.logger != nil {
				h.logger.Error("csv bom write error", zap.Error(err))
			}
		}
		writer := csv.NewWriter(w)
		headers := []string{"ID", "Título", "Categoría", "Estatus", "Autor", "Email", "Publicado", "Actualizado", "Última edición", "Editor", "Actualizaciones 30d"}
		if err := writer.Write(headers); err != nil {
			if h.logger != nil {
				h.logger.Error("csv header write error", zap.Error(err))
			}
			writer.Flush()
			h.writeAudit(ctx, r, "AUDIT_EXPORT", "content_report", nil, map[string]any{"format": "csv", "rows": len(result.Rows)})
			return
		}
		for _, row := range result.Rows {
			record := []string{
				row.ID,
				row.Title,
				row.CategoryLabel,
				row.StatusLabel,
				valueOrEmpty(row.AuthorName),
				valueOrEmpty(row.AuthorEmail),
				formatTimestamp(row.PublishedAt),
				row.UpdatedAt.In(time.Local).Format("2006-01-02 15:04"),
				formatTimestamp(row.LastUpdateAt),
				valueOrEmpty(row.LastEditorName),
				strconv.Itoa(row.Updates30d),
			}
			if err := writer.Write(record); err != nil {
				if h.logger != nil {
					h.logger.Error("csv row write error", zap.Error(err))
				}
				break
			}
		}
		writer.Flush()
		if err := writer.Error(); err != nil && h.logger != nil {
			h.logger.Error("csv export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "AUDIT_EXPORT", "content_report", nil, map[string]any{"format": "csv", "rows": len(result.Rows)})
		return
	case "pdf":
		w.Header().Set("Content-Type", "application/pdf")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.pdf\"", filename))
		pdf := gofpdf.New("L", "mm", "A4", "")
		pdf.SetTitle("Reporte de contenido", false)
		pdf.SetMargins(12, 16, 12)
		pdf.SetAutoPageBreak(true, 18)
		pdf.AddPage()
		translator := pdf.UnicodeTranslatorFromDescriptor("")
		pdf.SetFont("Helvetica", "B", 16)
		pdf.Cell(0, 10, translator("Reporte de contenido editorial"))
		pdf.Ln(12)
		pdf.SetFont("Helvetica", "", 11)
		pdf.Cell(0, 8, translator(fmt.Sprintf("Generado %s | Total registros %d", time.Now().Format("02/01/2006 15:04"), result.Total)))
		pdf.Ln(10)
		headers := []string{"Título", "Categoría", "Estatus", "Autor", "Publicado", "Actualizado", "Última edición", "Editor", "Actualizaciones"}
		widths := []float64{60, 32, 28, 42, 24, 24, 28, 24, 15}
		rowHeight := 6.2
		pdf.SetFont("Helvetica", "B", 10)
		pdf.SetFillColor(40, 64, 96)
		pdf.SetDrawColor(210, 218, 235)
		pdf.SetLineWidth(0.15)
		pdf.SetTextColor(255, 255, 255)
		for i, head := range headers {
			pdf.CellFormat(widths[i], 8, translator(head), "1", 0, "L", true, 0, "")
		}
		pdf.Ln(-1)
		pdf.SetFont("Helvetica", "", 9)
		pdf.SetTextColor(0, 0, 0)
		fill := false
		leftMargin, _, _, _ := pdf.GetMargins()
		for _, row := range result.Rows {
			fill = !fill
			if fill {
				pdf.SetFillColor(245, 247, 252)
			} else {
				pdf.SetFillColor(255, 255, 255)
			}
			cells := []string{
				row.Title,
				row.CategoryLabel,
				row.StatusLabel,
				valueOrEmpty(row.AuthorName),
				formatTimestamp(row.PublishedAt),
				row.UpdatedAt.In(time.Local).Format("2006-01-02 15:04"),
				formatTimestamp(row.LastUpdateAt),
				valueOrEmpty(row.LastEditorName),
				strconv.Itoa(row.Updates30d),
			}
			joinedLines := make([]string, len(cells))
			maxLines := 1
			for i, cell := range cells {
				translated := translator(strings.TrimSpace(cell))
				if translated == "" {
					translated = translator("-")
				}
				split := pdf.SplitLines([]byte(translated), widths[i])
				if len(split) == 0 {
					split = [][]byte{[]byte(translated)}
				}
				if len(split) > maxLines {
					maxLines = len(split)
				}
				joinedLines[i] = string(bytes.Join(split, []byte("\n")))
			}
			y := pdf.GetY()
			x := leftMargin
			totalHeight := float64(maxLines) * rowHeight
			for i := range joinedLines {
				pdf.SetXY(x, y)
				pdf.MultiCell(widths[i], rowHeight, joinedLines[i], "1", "L", fill)
				x += widths[i]
			}
			pdf.SetXY(leftMargin, y+totalHeight)
		}
		if err := pdf.Output(w); err != nil && h.logger != nil {
			h.logger.Error("pdf export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "AUDIT_EXPORT", "content_report", nil, map[string]any{"format": "pdf", "rows": len(result.Rows)})
		return
	default:
		w.Header().Set("X-Total-Count", strconv.Itoa(result.Total))
		writeJSON(w, 200, result)
	}
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
	h.writeAudit(ctx, r, "MEMBER_ADD", "membership", &req.UserID, map[string]any{"org_id": orgID, "user_id": req.UserID})
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
	h.writeAudit(ctx, r, "MEMBER_REMOVE", "membership", &userID, map[string]any{"org_id": orgID, "user_id": userID})
	w.WriteHeader(204)
}

func (h *Handlers) ListMembers(w http.ResponseWriter, r *http.Request) {
	orgID := chi.URLParam(r, "id")
	limit, offset := parseLimitOffset(r)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListMembers(ctx, orgID, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
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
	h.writeAudit(ctx, r, "USER_STATUS_UPDATE", "user", &id, map[string]any{"status": req.Status})
	w.WriteHeader(204)
}

type roleCreateReq struct {
	Name        string  `json:"name" validate:"required,min=3,max=50"`
	Description *string `json:"description" validate:"omitempty,max=250"`
}

type roleUpdateReq struct {
	Name        *string `json:"name" validate:"omitempty,min=3,max=50"`
	Description *string `json:"description" validate:"omitempty,max=250"`
}

func (h *Handlers) ListRoles(w http.ResponseWriter, r *http.Request) {
	limit, offset := parseLimitOffset(r)
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListRoles(ctx, limit, offset)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, list)
}

func (h *Handlers) CreateRole(w http.ResponseWriter, r *http.Request) {
	var req roleCreateReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	name := strings.TrimSpace(req.Name)
	if name == "" {
		writeProblem(w, 422, "validation_error", "name is required", map[string]string{"name": "required"})
		return
	}
	var desc *string
	if req.Description != nil {
		trimmed := strings.TrimSpace(*req.Description)
		if trimmed != "" {
			desc = &trimmed
		}
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	role, err := h.repo.CreateRole(ctx, name, desc)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) {
			switch pgErr.Code {
			case "23505":
				writeProblem(w, 409, "conflict", "role already exists", map[string]string{"name": "unique"})
				return
			}
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "ROLE_CREATE", "role", &role.ID, map[string]any{"name": role.Name})
	writeJSON(w, 201, role)
}

func (h *Handlers) UpdateRole(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	var req roleUpdateReq
	dec := json.NewDecoder(r.Body)
	dec.DisallowUnknownFields()
	if err := dec.Decode(&req); err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", nil)
		return
	}
	if req.Name != nil {
		trimmed := strings.TrimSpace(*req.Name)
		if trimmed == "" {
			writeProblem(w, 422, "validation_error", "name cannot be empty", map[string]string{"name": "required"})
			return
		}
		req.Name = &trimmed
	}
	if req.Description != nil {
		trimmed := strings.TrimSpace(*req.Description)
		req.Description = &trimmed
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	role, err := h.repo.UpdateRole(ctx, id, req.Name, req.Description)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "role not found", nil)
			return
		}
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			writeProblem(w, 409, "conflict", "role already exists", map[string]string{"name": "unique"})
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "ROLE_UPDATE", "role", &role.ID, map[string]any{"name": role.Name})
	writeJSON(w, 200, role)
}

func (h *Handlers) DeleteRole(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteRole(ctx, id); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "role not found", nil)
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "ROLE_DELETE", "role", &id, nil)
	w.WriteHeader(204)
}

type assignRoleReq struct {
	RoleID string `json:"role_id" validate:"required,uuid4"`
}

func (h *Handlers) ListUserRoles(w http.ResponseWriter, r *http.Request) {
	userID := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	roles, err := h.repo.ListUserRoles(ctx, userID)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, roles)
}

func (h *Handlers) AssignUserRole(w http.ResponseWriter, r *http.Request) {
	userID := chi.URLParam(r, "id")
	var req assignRoleReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	assignment, err := h.repo.AssignRoleToUser(ctx, userID, req.RoleID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "role not found", nil)
			return
		}
		writeProblem(w, 400, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "USER_ROLE_ASSIGN", "user", &userID, map[string]any{"role_id": req.RoleID})
	writeJSON(w, 201, assignment)
}

func (h *Handlers) RemoveUserRole(w http.ResponseWriter, r *http.Request) {
	userID := chi.URLParam(r, "id")
	roleID := chi.URLParam(r, "roleId")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.RemoveRoleFromUser(ctx, userID, roleID); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			writeProblem(w, 404, "not_found", "role assignment not found", nil)
			return
		}
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	h.writeAudit(ctx, r, "USER_ROLE_REMOVE", "user", &userID, map[string]any{"role_id": roleID})
	w.WriteHeader(204)
}

type systemSettingsReq struct {
	BrandName          string  `json:"brand_name" validate:"required,min=2,max=160"`
	SupportEmail       string  `json:"support_email" validate:"required,email"`
	PrimaryColor       string  `json:"primary_color" validate:"required,hexcolor"`
	SecondaryColor     *string `json:"secondary_color" validate:"omitempty,hexcolor"`
	LogoURL            *string `json:"logo_url" validate:"omitempty,url"`
	ContactPhone       *string `json:"contact_phone" validate:"omitempty,min=5,max=40"`
	DefaultLocale      string  `json:"default_locale" validate:"required,min=2,max=16"`
	DefaultTimezone    string  `json:"default_timezone" validate:"required,min=2,max=64"`
	MaintenanceMode    bool    `json:"maintenance_mode"`
	MaintenanceMessage *string `json:"maintenance_message" validate:"omitempty,max=500"`
}

func (h *Handlers) GetSystemSettings(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	settings, err := h.repo.GetSystemSettings(ctx)
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	writeJSON(w, 200, settings)
}

func (h *Handlers) UpdateSystemSettings(w http.ResponseWriter, r *http.Request) {
	var req systemSettingsReq
	fields, err := decodeAndValidate(r, &req, h.validate)
	if err != nil {
		writeProblem(w, 400, "bad_request", "invalid payload", fields)
		return
	}
	payload := models.SystemSettingsInput{
		BrandName:       strings.TrimSpace(req.BrandName),
		SupportEmail:    strings.TrimSpace(req.SupportEmail),
		PrimaryColor:    strings.TrimSpace(req.PrimaryColor),
		DefaultLocale:   strings.TrimSpace(req.DefaultLocale),
		DefaultTimezone: strings.TrimSpace(req.DefaultTimezone),
		MaintenanceMode: req.MaintenanceMode,
	}
	if req.SecondaryColor != nil {
		trimmed := strings.TrimSpace(*req.SecondaryColor)
		if trimmed != "" {
			payload.SecondaryColor = &trimmed
		}
	}
	if req.LogoURL != nil {
		trimmed := strings.TrimSpace(*req.LogoURL)
		if trimmed != "" {
			payload.LogoURL = &trimmed
		}
	}
	if req.ContactPhone != nil {
		trimmed := strings.TrimSpace(*req.ContactPhone)
		if trimmed != "" {
			payload.ContactPhone = &trimmed
		}
	}
	if req.MaintenanceMessage != nil {
		trimmed := strings.TrimSpace(*req.MaintenanceMessage)
		if trimmed != "" {
			payload.MaintenanceMessage = &trimmed
		}
	}
	payload.PrimaryColor = strings.ToUpper(payload.PrimaryColor)
	if payload.SecondaryColor != nil {
		upper := strings.ToUpper(*payload.SecondaryColor)
		payload.SecondaryColor = &upper
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	updated, err := h.repo.UpdateSystemSettings(ctx, payload, actorPtr(r))
	if err != nil {
		writeProblem(w, 500, "db_error", err.Error(), nil)
		return
	}
	entity := "system_settings"
	var entityID string = "singleton"
	h.writeAudit(ctx, r, "SYSTEM_SETTINGS_UPDATE", entity, &entityID, map[string]any{"brand_name": updated.BrandName, "maintenance_mode": updated.MaintenanceMode})
	writeJSON(w, 200, updated)
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
	h.writeAudit(ctx, r, "APIKEY_CREATE", "api_key", &id, map[string]any{"label": req.Label})
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
	h.writeAudit(ctx, r, "APIKEY_SET_PERMS", "api_key", &id, map[string]any{"count": len(req.Permissions)})
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
	h.writeAudit(ctx, r, "APIKEY_REVOKE", "api_key", &id, nil)
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
	if err := h.repo.Ping(ctx); err != nil {
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
