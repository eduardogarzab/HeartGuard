package superadmin

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"math"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/go-chi/chi/v5"
	"github.com/go-playground/validator/v10"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
	gofpdf "github.com/jung-kurt/gofpdf"
	"go.uber.org/zap"

	"heartguard-superadmin/internal/audit"
	"heartguard-superadmin/internal/middleware"
	"heartguard-superadmin/internal/models"
	"heartguard-superadmin/internal/session"
	"heartguard-superadmin/internal/ui"
)

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

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
	CancelInvitation(ctx context.Context, invitationID string) error

	AddMember(ctx context.Context, orgID, userID, orgRoleID string) error
	RemoveMember(ctx context.Context, orgID, userID string) error
	ListMembers(ctx context.Context, orgID string, limit, offset int) ([]models.Membership, error)

	ListCatalog(ctx context.Context, catalog string, limit, offset int) ([]models.CatalogItem, error)
	CreateCatalogItem(ctx context.Context, catalog, code, label string, weight *int) (*models.CatalogItem, error)
	UpdateCatalogItem(ctx context.Context, catalog, id string, code, label *string, weight *int) (*models.CatalogItem, error)
	DeleteCatalogItem(ctx context.Context, catalog, id string) error

	ListPatients(ctx context.Context, limit, offset int) ([]models.Patient, error)
	CreatePatient(ctx context.Context, input models.PatientInput) (*models.Patient, error)
	UpdatePatient(ctx context.Context, id string, input models.PatientInput) (*models.Patient, error)
	DeletePatient(ctx context.Context, id string) error

	ListDevices(ctx context.Context, limit, offset int) ([]models.Device, error)
	CreateDevice(ctx context.Context, input models.DeviceInput) (*models.Device, error)
	UpdateDevice(ctx context.Context, id string, input models.DeviceInput) (*models.Device, error)
	DeleteDevice(ctx context.Context, id string) error
	ListDeviceTypes(ctx context.Context) ([]models.DeviceType, error)

	ListSignalStreams(ctx context.Context, limit, offset int) ([]models.SignalStream, error)
	CreateSignalStream(ctx context.Context, input models.SignalStreamInput) (*models.SignalStream, error)
	UpdateSignalStream(ctx context.Context, id string, input models.SignalStreamInput) (*models.SignalStream, error)
	DeleteSignalStream(ctx context.Context, id string) error

	ListModels(ctx context.Context, limit, offset int) ([]models.MLModel, error)
	CreateModel(ctx context.Context, input models.MLModelInput) (*models.MLModel, error)
	UpdateModel(ctx context.Context, id string, input models.MLModelInput) (*models.MLModel, error)
	DeleteModel(ctx context.Context, id string) error

	ListEventTypes(ctx context.Context, limit, offset int) ([]models.EventType, error)
	CreateEventType(ctx context.Context, input models.EventTypeInput) (*models.EventType, error)
	UpdateEventType(ctx context.Context, id string, input models.EventTypeInput) (*models.EventType, error)
	DeleteEventType(ctx context.Context, id string) error

	ListInferences(ctx context.Context, limit, offset int) ([]models.Inference, error)
	CreateInference(ctx context.Context, input models.InferenceInput) (*models.Inference, error)
	UpdateInference(ctx context.Context, id string, input models.InferenceInput) (*models.Inference, error)
	DeleteInference(ctx context.Context, id string) error

	ListAlerts(ctx context.Context, limit, offset int) ([]models.Alert, error)
	CreateAlert(ctx context.Context, patientID string, input models.AlertInput) (*models.Alert, error)
	UpdateAlert(ctx context.Context, id string, input models.AlertInput) (*models.Alert, error)
	DeleteAlert(ctx context.Context, id string) error
	ListAlertTypes(ctx context.Context) ([]models.AlertType, error)
	ListAlertStatuses(ctx context.Context) ([]models.AlertStatus, error)

	ListContentBlockTypes(ctx context.Context, limit, offset int) ([]models.ContentBlockType, error)
	CreateContentBlockType(ctx context.Context, code, label string, description *string) (*models.ContentBlockType, error)
	UpdateContentBlockType(ctx context.Context, id string, code, label, description *string) (*models.ContentBlockType, error)
	DeleteContentBlockType(ctx context.Context, id string) error

	ListContent(ctx context.Context, filters models.ContentFilters) ([]models.ContentItem, error)
	GetContent(ctx context.Context, id string) (*models.ContentDetail, error)
	CreateContent(ctx context.Context, input models.ContentCreateInput, actorID *string) (*models.ContentDetail, error)
	UpdateContent(ctx context.Context, id string, input models.ContentUpdateInput, actorID *string) (*models.ContentDetail, error)
	DeleteContent(ctx context.Context, id string) error
	ListContentVersions(ctx context.Context, id string, limit, offset int) ([]models.ContentVersion, error)
	ListContentAuthors(ctx context.Context) ([]models.ContentAuthor, error)

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

	GetUserSummary(ctx context.Context, userID string) (*models.User, error)
	IsSuperadmin(ctx context.Context, userID string) (bool, error)

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
	renderer *ui.Renderer
	sessions *session.Manager
	logger   *zap.Logger
	validate *validator.Validate
}

func NewHandlers(repo Repository, renderer *ui.Renderer, sessions *session.Manager, logger *zap.Logger) *Handlers {
	v := validator.New(validator.WithRequiredStructEnabled())
	return &Handlers{repo: repo, renderer: renderer, sessions: sessions, logger: logger, validate: v}
}

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
	"content_types":         {Label: "Tipos de contenido"},
}

var operationLabels = map[string]string{
	"ORG_CREATE":                "Alta de organización",
	"ORG_UPDATE":                "Actualización de organización",
	"ORG_DELETE":                "Eliminación de organización",
	"INVITE_CREATE":             "Emisión de invitación",
	"INVITE_CANCEL":             "Cancelación de invitación",
	"INVITE_CONSUME":            "Consumo de invitación",
	"MEMBER_ADD":                "Alta de miembro",
	"MEMBER_REMOVE":             "Baja de miembro",
	"USER_STATUS_UPDATE":        "Actualización de estatus de usuario",
	"APIKEY_CREATE":             "Creación de API Key",
	"APIKEY_SET_PERMS":          "Configuración de permisos de API Key",
	"APIKEY_REVOKE":             "Revocación de API Key",
	"CATALOG_CREATE":            "Alta en catálogo",
	"CATALOG_UPDATE":            "Actualización de catálogo",
	"CATALOG_DELETE":            "Eliminación de catálogo",
	"CONTENT_BLOCK_TYPE_CREATE": "Alta de tipo de bloque",
	"CONTENT_BLOCK_TYPE_UPDATE": "Actualización de tipo de bloque",
	"CONTENT_BLOCK_TYPE_DELETE": "Eliminación de tipo de bloque",
	"PATIENT_CREATE":            "Alta de paciente",
	"PATIENT_UPDATE":            "Actualización de paciente",
	"PATIENT_DELETE":            "Eliminación de paciente",
	"DEVICE_CREATE":             "Alta de dispositivo",
	"DEVICE_UPDATE":             "Actualización de dispositivo",
	"DEVICE_DELETE":             "Eliminación de dispositivo",
	"SIGNAL_STREAM_CREATE":      "Alta de stream de señal",
	"SIGNAL_STREAM_UPDATE":      "Actualización de stream de señal",
	"SIGNAL_STREAM_DELETE":      "Eliminación de stream de señal",
	"MODEL_CREATE":              "Alta de modelo ML",
	"MODEL_UPDATE":              "Actualización de modelo ML",
	"MODEL_DELETE":              "Eliminación de modelo ML",
	"EVENT_TYPE_CREATE":         "Alta de tipo de evento",
	"EVENT_TYPE_UPDATE":         "Actualización de tipo de evento",
	"EVENT_TYPE_DELETE":         "Eliminación de tipo de evento",
	"INFERENCE_CREATE":          "Alta de inferencia",
	"INFERENCE_UPDATE":          "Actualización de inferencia",
	"INFERENCE_DELETE":          "Eliminación de inferencia",
	"ALERT_CREATE":              "Alta de alerta",
	"ALERT_UPDATE":              "Actualización de alerta",
	"ALERT_DELETE":              "Eliminación de alerta",
	"AUDIT_EXPORT":              "Exportación de auditoría",
	"CONTENT_CREATE":            "Alta de contenido",
	"CONTENT_UPDATE":            "Actualización de contenido",
	"CONTENT_DELETE":            "Eliminación de contenido",
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

func parseBoolDefault(s string, def bool) bool {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "1", "t", "true", "yes", "y":
		return true
	case "0", "f", "false", "no", "n":
		return false
	default:
		return def
	}
}

func generateAPIKeySecret() (string, error) {
	buf := make([]byte, 32)
	if _, err := rand.Read(buf); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(buf), nil
}

func (h *Handlers) Healthz(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 2*time.Second)
	defer cancel()
	if err := h.repo.Ping(ctx); err != nil {
		http.Error(w, err.Error(), http.StatusServiceUnavailable)
		return
	}
	w.WriteHeader(http.StatusOK)
	_, _ = w.Write([]byte("ok"))
}

func (h *Handlers) render(w http.ResponseWriter, r *http.Request, templateName, title string, data any, breadcrumbs []ui.Breadcrumb) {
	jti := middleware.SessionJTIFromContext(r.Context())
	flashes := h.sessions.PopFlashes(r.Context(), jti)
	csrf := middleware.CSRFFromContext(r.Context())
	currentUser := middleware.UserFromContext(r.Context())
	settings, err := h.repo.GetSystemSettings(r.Context())
	if err != nil && h.logger != nil {
		h.logger.Error("layout settings load", zap.Error(err))
	}
	view := ui.ViewData{
		Title:        title,
		CSRFToken:    csrf,
		Flashes:      flashes,
		CurrentUser:  currentUser,
		Settings:     settings,
		Data:         data,
		Breadcrumbs:  breadcrumbs,
		IsSuperadmin: middleware.IsSuperadmin(r.Context()),
	}
	view.ContentTemplate = templateName + ":content"
	if err := h.renderer.Render(w, templateName, view); err != nil {
		if h.logger != nil {
			h.logger.Error("render", zap.Error(err), zap.String("template", templateName))
		}
		http.Error(w, "error interno", http.StatusInternalServerError)
	}
}

func (h *Handlers) writeAudit(ctx context.Context, r *http.Request, action, entity string, entityID *string, details map[string]any) {
	pool := h.repo.AuditPool()
	if pool == nil {
		return
	}
	ctxA, cancel := audit.Ctx(ctx)
	defer cancel()
	actor := middleware.UserIDFromContext(r.Context())
	var actorPtr *string
	if actor != "" {
		actorPtr = &actor
	}
	_ = audit.Write(ctxA, pool, actorPtr, action, entity, entityID, details, nil)
}

type dashboardMetric struct {
	Label   string
	Value   string
	Caption string
}

type dashboardChartSlice struct {
	Label   string
	Count   int
	Percent float64
	State   string
	Width   int
}

type dashboardOperation struct {
	Code  string
	Label string
	Count int
}

type dashboardActivityEntry struct {
	Timestamp time.Time
	Label     string
	Entity    string
	Actor     string
}

type dashboardActivitySeriesPoint struct {
	Bucket time.Time
	Count  int
}

type dashboardViewData struct {
	Overview                *models.MetricsOverview
	Metrics                 []dashboardMetric
	StatusChart             []dashboardChartSlice
	StatusTotal             int
	InvitationChart         []dashboardChartSlice
	InvitationTotal         int
	RecentOperations        []dashboardOperation
	RecentActivity          []dashboardActivityEntry
	ActivitySeries          []dashboardActivitySeriesPoint
	ContentTotals           *models.ContentTotals
	ContentStatusChart      []dashboardChartSlice
	ContentCategoryChart    []dashboardChartSlice
	ContentRoleChart        []dashboardChartSlice
	ContentAuthorChart      []dashboardChartSlice
	ContentMonthlySeries    []dashboardActivitySeriesPoint
	ContentCumulativeSeries []dashboardActivitySeriesPoint
}

func (h *Handlers) buildDashboardViewData(ctx context.Context) dashboardViewData {
	overview, err := h.repo.MetricsOverview(ctx)
	if err != nil && h.logger != nil {
		h.logger.Error("metrics overview", zap.Error(err))
	}
	recent, err := h.repo.MetricsRecentActivity(ctx, 10)
	if err != nil && h.logger != nil {
		h.logger.Error("metrics recent", zap.Error(err))
	}
	statuses, err := h.repo.MetricsUserStatusBreakdown(ctx)
	if err != nil && h.logger != nil {
		h.logger.Error("metrics statuses", zap.Error(err))
	}
	invites, err := h.repo.MetricsInvitationBreakdown(ctx)
	if err != nil && h.logger != nil {
		h.logger.Error("metrics invites", zap.Error(err))
	}
	content, err := h.repo.MetricsContentSnapshot(ctx)
	if err != nil && h.logger != nil {
		h.logger.Error("metrics content", zap.Error(err))
	}

	metrics := make([]dashboardMetric, 0, 4)
	ops := make([]dashboardOperation, 0)
	activity := make([]dashboardActivityEntry, 0)
	activityBuckets := make(map[time.Time]int)
	if overview != nil {
		metrics = append(metrics,
			dashboardMetric{Label: "Usuarios totales", Value: strconv.Itoa(overview.TotalUsers), Caption: "Usuarios registrados en el sistema"},
			dashboardMetric{Label: "Organizaciones totales", Value: strconv.Itoa(overview.TotalOrganizations), Caption: "Con al menos un usuario"},
			dashboardMetric{Label: "Membresías totales", Value: strconv.Itoa(overview.TotalMemberships), Caption: "Usuarios con rol asignado"},
			dashboardMetric{Label: "Tiempo de respuesta", Value: fmt.Sprintf("%.0f ms", overview.AvgResponseMs), Caption: "Promedio en la última hora"},
		)
		ops = make([]dashboardOperation, 0, len(overview.RecentOperations))
		for _, op := range overview.RecentOperations {
			ops = append(ops, dashboardOperation{
				Code:  op.Type,
				Label: operationLabel(op.Type),
				Count: op.Count,
			})
		}
	}

	if len(recent) > 0 {
		activity = make([]dashboardActivityEntry, 0, len(recent))
		for _, item := range recent {
			entity := ""
			if item.Entity != nil {
				entity = *item.Entity
			}
			actor := ""
			if item.ActorEmail != nil {
				actor = *item.ActorEmail
			}
			activity = append(activity, dashboardActivityEntry{
				Timestamp: item.TS,
				Label:     operationLabel(item.Action),
				Entity:    entity,
				Actor:     actor,
			})
			bucket := item.TS.Truncate(time.Hour)
			activityBuckets[bucket]++
		}
	}

	activitySeries := make([]dashboardActivitySeriesPoint, 0, len(activityBuckets))
	if len(activityBuckets) > 0 {
		bucketKeys := make([]time.Time, 0, len(activityBuckets))
		for ts := range activityBuckets {
			bucketKeys = append(bucketKeys, ts)
		}
		sort.Slice(bucketKeys, func(i, j int) bool {
			return bucketKeys[i].Before(bucketKeys[j])
		})
		for _, ts := range bucketKeys {
			activitySeries = append(activitySeries, dashboardActivitySeriesPoint{Bucket: ts, Count: activityBuckets[ts]})
		}
	}

	statusChart := make([]dashboardChartSlice, 0, len(statuses))
	statusTotal := 0
	for _, item := range statuses {
		statusTotal += item.Count
	}
	for _, item := range statuses {
		percent := 0.0
		if statusTotal > 0 {
			percent = (float64(item.Count) / float64(statusTotal)) * 100
		}
		state := "info"
		switch strings.ToLower(item.Code) {
		case "active", "ok":
			state = "success"
		case "pending", "invited":
			state = "warn"
		case "blocked", "revoked":
			state = "danger"
		}
		width := int(math.Round(percent))
		if width <= 0 && item.Count > 0 {
			width = 4
		}
		if width > 100 {
			width = 100
		}
		statusChart = append(statusChart, dashboardChartSlice{
			Label:   item.Label,
			Count:   item.Count,
			Percent: percent,
			State:   state,
			Width:   width,
		})
	}

	inviteChart := make([]dashboardChartSlice, 0, len(invites))
	inviteTotal := 0
	for _, item := range invites {
		inviteTotal += item.Count
	}
	for _, item := range invites {
		percent := 0.0
		if inviteTotal > 0 {
			percent = (float64(item.Count) / float64(inviteTotal)) * 100
		}
		state := "info"
		switch strings.ToLower(item.Status) {
		case "pending":
			state = "warn"
		case "used", "accepted":
			state = "success"
		case "cancelled", "revoked", "expired":
			state = "danger"
		}
		width := int(math.Round(percent))
		if width <= 0 && item.Count > 0 {
			width = 4
		}
		if width > 100 {
			width = 100
		}
		inviteChart = append(inviteChart, dashboardChartSlice{
			Label:   item.Label,
			Count:   item.Count,
			Percent: percent,
			State:   state,
			Width:   width,
		})
	}

	var (
		totals                  *models.ContentTotals
		contentStatusChart      []dashboardChartSlice
		contentCategoryChart    []dashboardChartSlice
		contentRoleChart        []dashboardChartSlice
		contentAuthorChart      []dashboardChartSlice
		contentMonthlySeries    []dashboardActivitySeriesPoint
		contentCumulativeSeries []dashboardActivitySeriesPoint
	)

	parsePeriod := func(input string) (time.Time, bool) {
		layouts := []string{time.RFC3339, "2006-01-02", "2006-01"}
		for _, layout := range layouts {
			if t, err := time.Parse(layout, input); err == nil {
				if layout == "2006-01" {
					t = time.Date(t.Year(), t.Month(), 1, 0, 0, 0, 0, time.UTC)
				}
				return t, true
			}
		}
		return time.Time{}, false
	}

	if content != nil {
		totals = &content.Totals
		statusTotal := content.Totals.Total
		statusEntries := []struct {
			label string
			count int
			state string
		}{
			{label: "Publicados", count: content.Totals.Published, state: "success"},
			{label: "En revisión", count: content.Totals.InReview, state: "info"},
			{label: "Borradores", count: content.Totals.Drafts, state: "warn"},
			{label: "Programados", count: content.Totals.Scheduled, state: "info"},
			{label: "Archivados", count: content.Totals.Archived, state: "danger"},
		}
		if content.Totals.Stale > 0 {
			statusEntries = append(statusEntries, struct {
				label string
				count int
				state string
			}{label: "Obsoletos", count: content.Totals.Stale, state: "warn"})
		}
		for _, item := range statusEntries {
			if item.count <= 0 {
				continue
			}
			percent := 0.0
			if statusTotal > 0 {
				percent = (float64(item.count) / float64(statusTotal)) * 100
			}
			width := int(math.Round(percent))
			if width <= 0 && item.count > 0 {
				width = 4
			}
			if width > 100 {
				width = 100
			}
			contentStatusChart = append(contentStatusChart, dashboardChartSlice{
				Label:   item.label,
				Count:   item.count,
				Percent: percent,
				State:   item.state,
				Width:   width,
			})
		}

		const maxSlices = 5
		categoriesTotal := 0
		for _, cat := range content.Categories {
			categoriesTotal += cat.Count
		}
		otherCategories := 0
		for _, cat := range content.Categories {
			if cat.Count <= 0 {
				continue
			}
			label := cat.Label
			if label == "" {
				label = cat.Category
			}
			if len(contentCategoryChart) < maxSlices {
				percent := 0.0
				if categoriesTotal > 0 {
					percent = (float64(cat.Count) / float64(categoriesTotal)) * 100
				}
				width := int(math.Round(percent))
				if width <= 0 && cat.Count > 0 {
					width = 4
				}
				if width > 100 {
					width = 100
				}
				contentCategoryChart = append(contentCategoryChart, dashboardChartSlice{
					Label:   label,
					Count:   cat.Count,
					Percent: percent,
					State:   "info",
					Width:   width,
				})
			} else {
				otherCategories += cat.Count
			}
		}
		if otherCategories > 0 && categoriesTotal > 0 {
			percent := (float64(otherCategories) / float64(categoriesTotal)) * 100
			width := int(math.Round(percent))
			if width <= 0 {
				width = 4
			}
			if width > 100 {
				width = 100
			}
			contentCategoryChart = append(contentCategoryChart, dashboardChartSlice{
				Label:   "Otros",
				Count:   otherCategories,
				Percent: percent,
				State:   "info",
				Width:   width,
			})
		}

		roleTotal := 0
		for _, item := range content.RoleActivity {
			roleTotal += item.Count
		}
		for _, item := range content.RoleActivity {
			if item.Count <= 0 {
				continue
			}
			percent := 0.0
			if roleTotal > 0 {
				percent = (float64(item.Count) / float64(roleTotal)) * 100
			}
			width := int(math.Round(percent))
			if width <= 0 && item.Count > 0 {
				width = 4
			}
			if width > 100 {
				width = 100
			}
			label := item.Role
			if label == "" {
				label = "Sin rol"
			}
			contentRoleChart = append(contentRoleChart, dashboardChartSlice{
				Label:   label,
				Count:   item.Count,
				Percent: percent,
				State:   "info",
				Width:   width,
			})
		}
		if len(contentRoleChart) > maxSlices {
			contentRoleChart = contentRoleChart[:maxSlices]
		}

		authorTotal := 0
		for _, author := range content.TopAuthors {
			authorTotal += author.Published
		}
		for _, author := range content.TopAuthors {
			if author.Published <= 0 {
				continue
			}
			label := author.Name
			if label == "" && author.Email != nil {
				label = *author.Email
			}
			if label == "" {
				label = author.UserID
			}
			percent := 0.0
			if authorTotal > 0 {
				percent = (float64(author.Published) / float64(authorTotal)) * 100
			}
			width := int(math.Round(percent))
			if width <= 0 && author.Published > 0 {
				width = 4
			}
			if width > 100 {
				width = 100
			}
			contentAuthorChart = append(contentAuthorChart, dashboardChartSlice{
				Label:   label,
				Count:   author.Published,
				Percent: percent,
				State:   "success",
				Width:   width,
			})
			if len(contentAuthorChart) >= maxSlices {
				break
			}
		}

		for _, point := range content.Monthly {
			if t, ok := parsePeriod(point.Period); ok {
				contentMonthlySeries = append(contentMonthlySeries, dashboardActivitySeriesPoint{
					Bucket: t,
					Count:  point.Total,
				})
			}
		}
		if len(contentMonthlySeries) > 1 {
			sort.Slice(contentMonthlySeries, func(i, j int) bool {
				return contentMonthlySeries[i].Bucket.Before(contentMonthlySeries[j].Bucket)
			})
		}

		for _, point := range content.Cumulative {
			if t, ok := parsePeriod(point.Period); ok {
				contentCumulativeSeries = append(contentCumulativeSeries, dashboardActivitySeriesPoint{
					Bucket: t,
					Count:  point.Count,
				})
			}
		}
		if len(contentCumulativeSeries) > 1 {
			sort.Slice(contentCumulativeSeries, func(i, j int) bool {
				return contentCumulativeSeries[i].Bucket.Before(contentCumulativeSeries[j].Bucket)
			})
		}
	}

	return dashboardViewData{
		Overview:                overview,
		Metrics:                 metrics,
		StatusChart:             statusChart,
		StatusTotal:             statusTotal,
		InvitationChart:         inviteChart,
		InvitationTotal:         inviteTotal,
		RecentOperations:        ops,
		RecentActivity:          activity,
		ActivitySeries:          activitySeries,
		ContentTotals:           totals,
		ContentStatusChart:      contentStatusChart,
		ContentCategoryChart:    contentCategoryChart,
		ContentRoleChart:        contentRoleChart,
		ContentAuthorChart:      contentAuthorChart,
		ContentMonthlySeries:    contentMonthlySeries,
		ContentCumulativeSeries: contentCumulativeSeries,
	}
}

func (h *Handlers) Dashboard(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	data := h.buildDashboardViewData(ctx)

	h.render(w, r, "superadmin/dashboard.html", "Panel", data, []ui.Breadcrumb{{Label: "Panel"}})
}

func (h *Handlers) DashboardExport(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 8*time.Second)
	defer cancel()

	data := h.buildDashboardViewData(ctx)
	format := strings.ToLower(strings.TrimSpace(r.URL.Query().Get("format")))
	if format != "csv" {
		format = "pdf"
	}

	generatedAt := time.Now()
	filename := fmt.Sprintf("dashboard-%s", generatedAt.Format("20060102-150405"))

	formatLocal := func(ts time.Time) string {
		return ts.In(time.Local).Format("2006-01-02 15:04")
	}
	formatPercent := func(val float64) string {
		return fmt.Sprintf("%.2f%%", val)
	}

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
		write := func(record []string) {
			if err := writer.Write(record); err != nil && h.logger != nil {
				h.logger.Error("csv write error", zap.Error(err))
			}
		}
		write([]string{"Reporte de métricas del panel superadmin"})
		write([]string{"Generado", formatLocal(generatedAt)})
		write([]string{})
		write([]string{"Sección", "Métrica", "Valor", "Detalle"})
		sectionName := "Resumen"
		for _, metric := range data.Metrics {
			write([]string{sectionName, metric.Label, metric.Value, metric.Caption})
		}
		if data.Overview != nil {
			write([]string{sectionName, "Invitaciones pendientes", strconv.Itoa(data.Overview.PendingInvitations), "Invitaciones abiertas sin usar"})
		}
		write([]string{})
		write([]string{"Sección", "Estatus", "Total", "Participación"})
		for _, item := range data.StatusChart {
			write([]string{"Usuarios", item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
		}
		if data.StatusTotal > 0 {
			write([]string{"Usuarios", "Total", strconv.Itoa(data.StatusTotal), ""})
		}
		write([]string{})
		write([]string{"Sección", "Estatus", "Total", "Participación"})
		for _, item := range data.InvitationChart {
			write([]string{"Invitaciones", item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
		}
		if data.InvitationTotal > 0 {
			write([]string{"Invitaciones", "Total", strconv.Itoa(data.InvitationTotal), ""})
		}
		write([]string{})
		write([]string{"Sección", "Acción", "Código", "Eventos"})
		for _, op := range data.RecentOperations {
			write([]string{"Operaciones", op.Label, op.Code, strconv.Itoa(op.Count)})
		}
		write([]string{})
		write([]string{"Sección", "Fecha/Hora", "Eventos"})
		for _, bucket := range data.ActivitySeries {
			write([]string{"Actividad por hora", formatLocal(bucket.Bucket), strconv.Itoa(bucket.Count)})
		}
		write([]string{})
		write([]string{"Sección", "Fecha", "Evento", "Actor", "Entidad"})
		for _, entry := range data.RecentActivity {
			write([]string{"Actividad reciente", formatLocal(entry.Timestamp), entry.Label, entry.Actor, entry.Entity})
		}
		if data.ContentTotals != nil {
			write([]string{})
			write([]string{"Sección", "Indicador", "Valor"})
			totals := data.ContentTotals
			write([]string{"Contenido", "Total piezas", strconv.Itoa(totals.Total)})
			write([]string{"Contenido", "Publicados", strconv.Itoa(totals.Published)})
			write([]string{"Contenido", "En revisión", strconv.Itoa(totals.InReview)})
			write([]string{"Contenido", "Borradores", strconv.Itoa(totals.Drafts)})
			write([]string{"Contenido", "Programados", strconv.Itoa(totals.Scheduled)})
			write([]string{"Contenido", "Archivados", strconv.Itoa(totals.Archived)})
			write([]string{"Contenido", "Obsoletos", strconv.Itoa(totals.Stale)})
			write([]string{"Contenido", "Autores activos", strconv.Itoa(totals.ActiveAuthors)})
			write([]string{"Contenido", "Actualizaciones 30 días", strconv.Itoa(totals.UpdatesLast30Days)})
			write([]string{})
			write([]string{"Sección", "Categoria", "Total", "Participación"})
			for _, item := range data.ContentCategoryChart {
				write([]string{"Categorías", item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
			}
			write([]string{})
			write([]string{"Sección", "Rol", "Total", "Participación"})
			for _, item := range data.ContentRoleChart {
				write([]string{"Actividad por rol", item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
			}
			write([]string{})
			write([]string{"Sección", "Estatus", "Total", "Participación"})
			for _, item := range data.ContentStatusChart {
				write([]string{"Estatus de contenido", item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
			}
		}
		if len(data.ContentMonthlySeries) > 0 {
			write([]string{})
			write([]string{"Sección", "Periodo", "Total"})
			for _, point := range data.ContentMonthlySeries {
				write([]string{"Producción mensual", point.Bucket.Format("2006-01"), strconv.Itoa(point.Count)})
			}
		}
		if len(data.ContentCumulativeSeries) > 0 {
			write([]string{})
			write([]string{"Sección", "Periodo", "Acumulado"})
			for _, point := range data.ContentCumulativeSeries {
				write([]string{"Crecimiento acumulado", point.Bucket.Format("2006-01"), strconv.Itoa(point.Count)})
			}
		}
		writer.Flush()
		if err := writer.Error(); err != nil && h.logger != nil {
			h.logger.Error("csv export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "DASHBOARD_EXPORT", "dashboard", nil, map[string]any{"format": "csv", "rows": len(data.RecentActivity)})
		return
	case "pdf":
		w.Header().Set("Content-Type", "application/pdf")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=\"%s.pdf\"", filename))
		pdf := gofpdf.New("L", "mm", "A4", "")
		pdf.SetTitle("Reporte del panel superadmin", false)
		pdf.SetAuthor("HeartGuard", true)
		pdf.SetCreator("HeartGuard SuperAdmin System", true)
		pdf.SetMargins(15, 20, 15)
		pdf.SetAutoPageBreak(true, 25)
		translator := pdf.UnicodeTranslatorFromDescriptor("")

		// Colores corporativos
		primaryColor := struct{ R, G, B int }{26, 32, 44}      // Azul oscuro
		accentColor := struct{ R, G, B int }{59, 130, 246}     // Azul
		lightGrayColor := struct{ R, G, B int }{248, 250, 252} // Gris claro
		darkGrayColor := struct{ R, G, B int }{71, 85, 105}    // Gris oscuro

		// Función para encabezado y pie de página
		headerFooter := func() {
			pdf.SetHeaderFunc(func() {
				pdf.SetY(8)
				pdf.SetFont("Helvetica", "B", 10)
				pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
				pdf.Cell(0, 6, translator("HEARTGUARD - REPORTE EMPRESARIAL"))
				pdf.Ln(8)
				pdf.SetDrawColor(accentColor.R, accentColor.G, accentColor.B)
				pdf.SetLineWidth(0.5)
				pdf.Line(15, 18, 282, 18) // Línea horizontal
				pdf.SetTextColor(0, 0, 0)
			})
			pdf.SetFooterFunc(func() {
				pdf.SetY(-15)
				pdf.SetDrawColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
				pdf.SetLineWidth(0.3)
				pdf.Line(15, pdf.GetY()-2, 282, pdf.GetY()-2)
				pdf.SetFont("Helvetica", "I", 8)
				pdf.SetTextColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
				pdf.CellFormat(0, 5, translator(fmt.Sprintf("Generado: %s", formatLocal(generatedAt))), "", 0, "L", false, 0, "")
				pdf.CellFormat(0, 5, translator(fmt.Sprintf("Página %d", pdf.PageNo())), "", 0, "R", false, 0, "")
				pdf.SetTextColor(0, 0, 0)
			})
		}
		headerFooter()

		// ============ PORTADA ============
		pdf.AddPage()
		pdf.SetY(60)
		
		// Logo simulado / Marca
		pdf.SetFillColor(accentColor.R, accentColor.G, accentColor.B)
		pdf.Rect(125, 50, 15, 15, "F")
		pdf.SetFont("Helvetica", "B", 14)
		pdf.SetTextColor(255, 255, 255)
		pdf.SetXY(125, 57)
		pdf.Cell(15, 5, "HG")
		
		pdf.SetY(75)
		pdf.SetFont("Helvetica", "B", 24)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.CellFormat(0, 15, translator("REPORTE EJECUTIVO"), "", 0, "C", false, 0, "")
		pdf.Ln(15)
		
		pdf.SetFont("Helvetica", "", 14)
		pdf.SetTextColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
		pdf.CellFormat(0, 8, translator("Panel de Administración SuperAdmin"), "", 0, "C", false, 0, "")
		pdf.Ln(40)
		
		// Cuadro de información
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.SetDrawColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
		pdf.SetLineWidth(0.3)
		boxY := pdf.GetY()
		pdf.Rect(80, boxY, 137, 35, "FD")
		
		pdf.SetY(boxY + 8)
		pdf.SetFont("Helvetica", "B", 11)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.CellFormat(0, 6, translator("INFORMACIÓN DEL REPORTE"), "", 0, "C", false, 0, "")
		pdf.Ln(8)
		
		pdf.SetFont("Helvetica", "", 10)
		pdf.SetTextColor(0, 0, 0)
		pdf.CellFormat(0, 5, translator(fmt.Sprintf("Fecha de generación: %s", formatLocal(generatedAt))), "", 0, "C", false, 0, "")
		pdf.Ln(6)
		pdf.CellFormat(0, 5, translator("Sistema: HeartGuard SuperAdmin v1.0"), "", 0, "C", false, 0, "")
		pdf.Ln(6)
		pdf.SetFont("Helvetica", "I", 9)
		pdf.SetTextColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
		pdf.CellFormat(0, 5, translator("Documento confidencial - Uso interno"), "", 0, "C", false, 0, "")
		
		pdf.SetTextColor(0, 0, 0)

		// ============ PÁGINA DE CONTENIDO ============
		pdf.AddPage()
		
		// Resumen ejecutivo
		pdf.SetFont("Helvetica", "B", 16)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.CellFormat(0, 10, translator("RESUMEN EJECUTIVO"), "", 0, "L", true, 0, "")
		pdf.Ln(12)
		
		pdf.SetFont("Helvetica", "", 10)
		pdf.SetTextColor(0, 0, 0)
		summaryText := "Este reporte presenta un análisis detallado de las métricas clave del sistema HeartGuard. "
		summaryText += "Incluye información sobre usuarios activos, invitaciones, operaciones recientes y actividad del sistema. "
		summaryText += "Los datos presentados permiten una evaluación integral del rendimiento y uso de la plataforma."
		pdf.MultiCell(0, 6, translator(summaryText), "", "J", false)
		pdf.Ln(8)

		renderTable := func(title string, headers []string, widths []float64, aligns []string, rows [][]string) {
			if len(headers) != len(widths) {
				return
			}
			
			// Calcular espacio necesario: título (24mm) + encabezado (7mm) + al menos 3 filas (18mm) = ~50mm
			minSpaceNeeded := 50.0
			_, _, _, bottomMargin := pdf.GetMargins()
			pageHeight := 210.0 // A4 height
			availableSpace := pageHeight - pdf.GetY() - bottomMargin
			
			// Si no hay suficiente espacio, crear nueva página
			if availableSpace < minSpaceNeeded {
				pdf.AddPage()
			}
			
			// Separador de sección
			pdf.Ln(4)
			pdf.SetDrawColor(accentColor.R, accentColor.G, accentColor.B)
			pdf.SetLineWidth(0.8)
			currentY := pdf.GetY()
			pdf.Line(15, currentY, 40, currentY)
			pdf.Ln(2)
			
			// Título de la tabla con estilo destacado
			pdf.SetFont("Helvetica", "B", 13)
			pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
			pdf.Cell(0, 8, translator(title))
			pdf.Ln(10)
			
			if len(rows) == 0 {
				pdf.SetFont("Helvetica", "I", 10)
				pdf.SetTextColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
				pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
				pdf.CellFormat(0, 8, translator("   Sin datos disponibles"), "1", 0, "L", true, 0, "")
				pdf.SetTextColor(0, 0, 0)
				pdf.Ln(12)
				return
			}
			
			// Encabezados de tabla mejorados
			pdf.SetFont("Helvetica", "B", 9)
			pdf.SetFillColor(accentColor.R, accentColor.G, accentColor.B)
			pdf.SetDrawColor(200, 208, 220)
			pdf.SetLineWidth(0.2)
			pdf.SetTextColor(255, 255, 255)
			for i, head := range headers {
				align := "L"
				if i < len(aligns) && aligns[i] != "" {
					align = aligns[i]
				}
				pdf.CellFormat(widths[i], 7, translator(head), "1", 0, align, true, 0, "")
			}
			pdf.Ln(-1)
			pdf.SetFont("Helvetica", "", 9)
			pdf.SetTextColor(26, 32, 44)
			fill := false
			leftMargin, _, _, _ := pdf.GetMargins()
			lineHeight := 6.0
			
			for rowIdx, row := range rows {
				// Verificar si hay espacio para la fila actual (considerando altura máxima posible)
				maxPossibleRowHeight := 30.0 // Altura máxima estimada para una fila con texto largo
				availableSpace := pageHeight - pdf.GetY() - bottomMargin
				
				// Si no hay espacio suficiente para la fila, crear nueva página y redibujar encabezados
				if availableSpace < maxPossibleRowHeight {
					pdf.AddPage()
					
					// Redibujar encabezados de tabla en la nueva página
					pdf.SetFont("Helvetica", "B", 9)
					pdf.SetFillColor(accentColor.R, accentColor.G, accentColor.B)
					pdf.SetDrawColor(200, 208, 220)
					pdf.SetLineWidth(0.2)
					pdf.SetTextColor(255, 255, 255)
					for i, head := range headers {
						align := "L"
						if i < len(aligns) && aligns[i] != "" {
							align = aligns[i]
						}
						pdf.CellFormat(widths[i], 7, translator(head), "1", 0, align, true, 0, "")
					}
					pdf.Ln(-1)
					pdf.SetFont("Helvetica", "", 9)
					pdf.SetTextColor(26, 32, 44)
					
					// Resetear el fill pattern para mantener consistencia
					fill = (rowIdx % 2) == 1
				}
				
				fill = !fill
				if fill {
					pdf.SetFillColor(250, 251, 253)
				} else {
					pdf.SetFillColor(255, 255, 255)
				}
				
				y := pdf.GetY()
				x := leftMargin
				rowHeight := lineHeight
				texts := make([]string, len(headers))
				heights := make([]float64, len(headers))
				for i := range headers {
					text := ""
					if i < len(row) {
						text = translator(row[i])
					}
					texts[i] = text
					lines := pdf.SplitLines([]byte(text), widths[i])
					if len(lines) == 0 {
						heights[i] = lineHeight
					} else {
						heights[i] = float64(len(lines)) * lineHeight
					}
					if heights[i] > rowHeight {
						rowHeight = heights[i]
					}
				}
				for i, text := range texts {
					pdf.SetXY(x, y)
					align := "L"
					if i < len(aligns) && aligns[i] != "" {
						align = aligns[i]
					}
					pdf.MultiCell(widths[i], lineHeight, text, "1", align, fill)
					x += widths[i]
				}
				pdf.SetXY(leftMargin, y+rowHeight)
			}
		}

		metricsRows := make([][]string, 0, len(data.Metrics)+1)
		for _, metric := range data.Metrics {
			metricsRows = append(metricsRows, []string{metric.Label, metric.Value, metric.Caption})
		}
		if data.Overview != nil {
			metricsRows = append(metricsRows, []string{"Invitaciones pendientes", strconv.Itoa(data.Overview.PendingInvitations), "Invitaciones abiertas sin usar"})
		}
		
		// Sección: Indicadores Clave
		pdf.SetFont("Helvetica", "B", 14)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.CellFormat(0, 9, translator("1. INDICADORES CLAVE DE RENDIMIENTO"), "", 0, "L", true, 0, "")
		pdf.Ln(8)
		
		renderTable("Resumen general", []string{"Métrica", "Valor", "Detalle"}, []float64{80, 28, 140}, []string{"L", "R", "L"}, metricsRows)

		statusRows := make([][]string, 0, len(data.StatusChart))
		for _, item := range data.StatusChart {
			statusRows = append(statusRows, []string{item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
		}
		if data.StatusTotal > 0 {
			statusRows = append(statusRows, []string{"Total", strconv.Itoa(data.StatusTotal), ""})
		}
		renderTable("Usuarios por estatus", []string{"Estatus", "Total", "Participación"}, []float64{90, 28, 32}, []string{"L", "R", "R"}, statusRows)

		// Sección: Gestión de Invitaciones
		pdf.Ln(6)
		pdf.SetFont("Helvetica", "B", 14)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.CellFormat(0, 9, translator("2. GESTIÓN DE INVITACIONES"), "", 0, "L", true, 0, "")
		pdf.Ln(8)
		
		invRows := make([][]string, 0, len(data.InvitationChart))
		for _, item := range data.InvitationChart {
			invRows = append(invRows, []string{item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
		}
		if data.InvitationTotal > 0 {
			invRows = append(invRows, []string{"Total", strconv.Itoa(data.InvitationTotal), ""})
		}
		renderTable("Invitaciones", []string{"Estatus", "Total", "Participación"}, []float64{90, 28, 32}, []string{"L", "R", "R"}, invRows)

		// Sección: Actividad del Sistema
		pdf.Ln(6)
		pdf.SetFont("Helvetica", "B", 14)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.CellFormat(0, 9, translator("3. ACTIVIDAD DEL SISTEMA"), "", 0, "L", true, 0, "")
		pdf.Ln(8)
		
		opRows := make([][]string, 0, len(data.RecentOperations))
		for _, op := range data.RecentOperations {
			opRows = append(opRows, []string{op.Label, op.Code, strconv.Itoa(op.Count)})
		}
		renderTable("Operaciones recientes (30 días)", []string{"Acción", "Código", "Eventos"}, []float64{140, 40, 28}, []string{"L", "L", "R"}, opRows)

		activityRows := make([][]string, 0, len(data.RecentActivity))
		for idx, entry := range data.RecentActivity {
			if idx >= 25 {
				break
			}
			activityRows = append(activityRows, []string{formatLocal(entry.Timestamp), entry.Label, entry.Actor, entry.Entity})
		}
		renderTable("Actividad más reciente", []string{"Fecha", "Evento", "Actor", "Entidad"}, []float64{40, 110, 60, 60}, []string{"L", "L", "L", "L"}, activityRows)

		// Sección: Análisis Temporal
		pdf.Ln(6)
		pdf.SetFont("Helvetica", "B", 14)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.CellFormat(0, 9, translator("4. ANÁLISIS TEMPORAL"), "", 0, "L", true, 0, "")
		pdf.Ln(8)
		
		timelineRows := make([][]string, 0, len(data.ActivitySeries))
		for _, point := range data.ActivitySeries {
			timelineRows = append(timelineRows, []string{formatLocal(point.Bucket), strconv.Itoa(point.Count)})
		}
		renderTable("Actividad por hora", []string{"Fecha/Hora", "Eventos"}, []float64{60, 28}, []string{"L", "R"}, timelineRows)

		if data.ContentTotals != nil {
			// Nueva página para contenido
			pdf.AddPage()
			
			// Sección: Gestión de Contenido
			pdf.SetFont("Helvetica", "B", 14)
			pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
			pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
			pdf.CellFormat(0, 9, translator("5. GESTIÓN DE CONTENIDO"), "", 0, "L", true, 0, "")
			pdf.Ln(8)
			
			totals := data.ContentTotals
			contentRows := [][]string{
				{"Total piezas", strconv.Itoa(totals.Total)},
				{"Publicados", strconv.Itoa(totals.Published)},
				{"En revisión", strconv.Itoa(totals.InReview)},
				{"Borradores", strconv.Itoa(totals.Drafts)},
				{"Programados", strconv.Itoa(totals.Scheduled)},
				{"Archivados", strconv.Itoa(totals.Archived)},
				{"Obsoletos", strconv.Itoa(totals.Stale)},
				{"Autores activos", strconv.Itoa(totals.ActiveAuthors)},
				{"Actualizaciones 30 días", strconv.Itoa(totals.UpdatesLast30Days)},
			}
			renderTable("Resumen de contenido", []string{"Indicador", "Valor"}, []float64{120, 35}, []string{"L", "R"}, contentRows)

			statusRows := make([][]string, 0, len(data.ContentStatusChart))
			for _, item := range data.ContentStatusChart {
				statusRows = append(statusRows, []string{item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
			}
			renderTable("Estatus de contenido", []string{"Estatus", "Total", "Participación"}, []float64{110, 30, 30}, []string{"L", "R", "R"}, statusRows)

			categoryRows := make([][]string, 0, len(data.ContentCategoryChart))
			for _, item := range data.ContentCategoryChart {
				categoryRows = append(categoryRows, []string{item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
			}
			renderTable("Categorías principales", []string{"Categoría", "Total", "Participación"}, []float64{110, 30, 30}, []string{"L", "R", "R"}, categoryRows)

			roleRows := make([][]string, 0, len(data.ContentRoleChart))
			for _, item := range data.ContentRoleChart {
				roleRows = append(roleRows, []string{item.Label, strconv.Itoa(item.Count), formatPercent(item.Percent)})
			}
			renderTable("Actividad por rol", []string{"Rol", "Total", "Participación"}, []float64{110, 30, 30}, []string{"L", "R", "R"}, roleRows)
		}

		if len(data.ContentMonthlySeries) > 0 {
			// Sección: Tendencias de Producción
			pdf.Ln(6)
			pdf.SetFont("Helvetica", "B", 14)
			pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
			pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
			pdf.CellFormat(0, 9, translator("6. TENDENCIAS DE PRODUCCIÓN"), "", 0, "L", true, 0, "")
			pdf.Ln(8)
			
			monthlyRows := make([][]string, 0, len(data.ContentMonthlySeries))
			for idx, point := range data.ContentMonthlySeries {
				if idx >= 24 {
					break
				}
				monthlyRows = append(monthlyRows, []string{point.Bucket.Format("2006-01"), strconv.Itoa(point.Count)})
			}
			renderTable("Producción mensual", []string{"Periodo", "Total"}, []float64{60, 28}, []string{"L", "R"}, monthlyRows)
		}

		if len(data.ContentCumulativeSeries) > 0 {
			cumulativeRows := make([][]string, 0, len(data.ContentCumulativeSeries))
			for idx, point := range data.ContentCumulativeSeries {
				if idx >= 24 {
					break
				}
				cumulativeRows = append(cumulativeRows, []string{point.Bucket.Format("2006-01"), strconv.Itoa(point.Count)})
			}
			renderTable("Crecimiento acumulado", []string{"Periodo", "Acumulado"}, []float64{60, 28}, []string{"L", "R"}, cumulativeRows)
		}

		// Página final con conclusiones
		pdf.AddPage()
		pdf.SetY(40)
		pdf.SetFont("Helvetica", "B", 16)
		pdf.SetTextColor(primaryColor.R, primaryColor.G, primaryColor.B)
		pdf.SetFillColor(lightGrayColor.R, lightGrayColor.G, lightGrayColor.B)
		pdf.CellFormat(0, 10, translator("CONCLUSIONES Y OBSERVACIONES"), "", 0, "L", true, 0, "")
		pdf.Ln(12)
		
		pdf.SetFont("Helvetica", "", 10)
		pdf.SetTextColor(0, 0, 0)
		conclusionText := "Este reporte ha presentado un análisis exhaustivo de las métricas operativas del sistema HeartGuard. "
		conclusionText += "Los indicadores muestran el estado actual de la plataforma, permitiendo la toma de decisiones informadas "
		conclusionText += "para optimizar el rendimiento y la experiencia del usuario.\n\n"
		conclusionText += "Se recomienda revisar periódicamente estos reportes para identificar tendencias, "
		conclusionText += "detectar anomalías y planificar estrategias de crecimiento."
		pdf.MultiCell(0, 6, translator(conclusionText), "", "J", false)
		pdf.Ln(15)
		
		// Cuadro de firma o aprobación
		pdf.SetDrawColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
		pdf.SetLineWidth(0.3)
		pdf.Line(40, pdf.GetY(), 140, pdf.GetY())
		pdf.Ln(2)
		pdf.SetFont("Helvetica", "I", 9)
		pdf.SetTextColor(darkGrayColor.R, darkGrayColor.G, darkGrayColor.B)
		pdf.CellFormat(100, 5, translator("Sistema HeartGuard - Reporte Automatizado"), "", 0, "L", false, 0, "")
		
		pdf.SetMargins(16, 18, 16)
		pdf.SetAutoPageBreak(true, 20)
		pdf.SetFont("Helvetica", "B", 15)
		pdf.Cell(0, 9, translator("Resumen narrativo"))
		pdf.Ln(11)
		pdf.SetFont("Helvetica", "", 10)

		writeParagraph := func(text string) {
			if strings.TrimSpace(text) == "" {
				return
			}
			pdf.SetFont("Helvetica", "", 10)
			pdf.SetTextColor(68, 76, 96)
			pdf.MultiCell(0, 5.2, translator(text), "", "L", false)
			pdf.SetTextColor(0, 0, 0)
			pdf.Ln(1.5)
		}

		writeSection := func(title, subtitle string, lines []string) {
			pdf.Ln(2)
			pdf.SetFont("Helvetica", "B", 12)
			pdf.SetTextColor(26, 32, 44)
			pdf.Cell(0, 6.5, translator(title))
			pdf.Ln(6)
			if strings.TrimSpace(subtitle) != "" {
				pdf.SetFont("Helvetica", "", 9.3)
				pdf.SetTextColor(90, 99, 120)
				pdf.MultiCell(0, 5, translator(subtitle), "", "L", false)
				pdf.Ln(1)
			}
			if len(lines) == 0 {
				pdf.SetFont("Helvetica", "I", 9)
				pdf.SetTextColor(120, 128, 148)
				pdf.Cell(0, 4.8, translator("Sin datos disponibles"))
				pdf.SetTextColor(0, 0, 0)
				pdf.Ln(4)
				return
			}
			pdf.SetFont("Helvetica", "", 9.3)
			pdf.SetTextColor(33, 37, 41)
			for _, line := range lines {
				trimmed := strings.TrimSpace(line)
				if trimmed == "" {
					continue
				}
				pdf.MultiCell(0, 4.8, translator(fmt.Sprintf("• %s", trimmed)), "", "L", false)
			}
			pdf.SetTextColor(0, 0, 0)
			pdf.Ln(1)
		}

		intro := "Este documento consolida las principales métricas operativas del panel de administración para brindar una visión ejecutiva del estado actual de usuarios, invitaciones, operaciones y contenido."
		writeParagraph(intro)

		metricsLines := make([]string, 0, len(data.Metrics)+1)
		for _, metric := range data.Metrics {
			caption := strings.TrimSpace(metric.Caption)
			if caption != "" {
				metricsLines = append(metricsLines, fmt.Sprintf("%s: %s (%s)", metric.Label, metric.Value, caption))
			} else {
				metricsLines = append(metricsLines, fmt.Sprintf("%s: %s", metric.Label, metric.Value))
			}
		}
		if data.Overview != nil {
			metricsLines = append(metricsLines, fmt.Sprintf("Invitaciones pendientes: %d (invitaciones abiertas sin usar)", data.Overview.PendingInvitations))
		}
		writeSection("Resumen ejecutivo", "Indicadores claves de actividad y capacidad operativa.", metricsLines)

		statusLines := make([]string, 0, len(data.StatusChart)+1)
		for _, item := range data.StatusChart {
			statusLines = append(statusLines, fmt.Sprintf("%s: %d usuarios (%s del total)", item.Label, item.Count, formatPercent(item.Percent)))
		}
		if data.StatusTotal > 0 {
			statusLines = append(statusLines, fmt.Sprintf("Total reportado: %d usuarios", data.StatusTotal))
		}
		writeSection("Distribución de usuarios", "Panorama por estatus de cuenta y participación relativa.", statusLines)

		invLines := make([]string, 0, len(data.InvitationChart)+1)
		for _, item := range data.InvitationChart {
			invLines = append(invLines, fmt.Sprintf("%s: %d invitaciones (%s)", item.Label, item.Count, formatPercent(item.Percent)))
		}
		if data.InvitationTotal > 0 {
			invLines = append(invLines, fmt.Sprintf("Total de invitaciones activas: %d", data.InvitationTotal))
		}
		writeSection("Estatus de invitaciones", "Seguimiento del ciclo de invitaciones emitidas a nivel global.", invLines)

		opLines := make([]string, 0, len(data.RecentOperations))
		for _, op := range data.RecentOperations {
			opLines = append(opLines, fmt.Sprintf("%s (%s): %d eventos registrados", op.Label, strings.ToUpper(op.Code), op.Count))
		}
		writeSection("Operaciones destacadas (30 días)", "Actividades más frecuentes capturadas por el sistema de auditoría.", opLines)

		recentLines := make([]string, 0, min(len(data.RecentActivity), 25))
		for idx, entry := range data.RecentActivity {
			if idx >= 25 {
				break
			}
			actor := entry.Actor
			if actor == "" {
				actor = "Actor no identificado"
			}
			entity := entry.Entity
			if entity == "" {
				entity = "Sin referencia"
			}
			recentLines = append(recentLines, fmt.Sprintf("%s · %s · %s · %s", formatLocal(entry.Timestamp), entry.Label, actor, entity))
		}
		writeSection("Actividad reciente", "Detalle cronológico de los últimos eventos relevantes.", recentLines)

		timelineLines := make([]string, 0, len(data.ActivitySeries))
		for _, point := range data.ActivitySeries {
			timelineLines = append(timelineLines, fmt.Sprintf("%s: %d eventos", formatLocal(point.Bucket), point.Count))
		}
		writeSection("Curva de actividad horaria", "Concentración de eventos a lo largo de las últimas jornadas.", timelineLines)

		if data.ContentTotals != nil {
			totals := data.ContentTotals
			summaryLines := []string{
				fmt.Sprintf("Total de piezas gestionadas: %d", totals.Total),
				fmt.Sprintf("Publicados: %d", totals.Published),
				fmt.Sprintf("En revisión: %d", totals.InReview),
				fmt.Sprintf("Borradores: %d", totals.Drafts),
				fmt.Sprintf("Programados: %d", totals.Scheduled),
				fmt.Sprintf("Archivados: %d", totals.Archived),
			}
			if totals.Stale > 0 {
				summaryLines = append(summaryLines, fmt.Sprintf("Obsoletos identificados: %d", totals.Stale))
			}
			summaryLines = append(summaryLines,
				fmt.Sprintf("Autores activos: %d", totals.ActiveAuthors),
				fmt.Sprintf("Actualizaciones en los últimos 30 días: %d", totals.UpdatesLast30Days),
			)
			writeSection("Panorama de contenidos", "Inventario actualizado de activos editoriales.", summaryLines)

			statusContentLines := make([]string, 0, len(data.ContentStatusChart))
			for _, item := range data.ContentStatusChart {
				statusContentLines = append(statusContentLines, fmt.Sprintf("%s: %d elementos (%s)", item.Label, item.Count, formatPercent(item.Percent)))
			}
			writeSection("Estatus editorial", "Distribución actual de los contenidos según su ciclo de vida.", statusContentLines)

			categoryLines := make([]string, 0, len(data.ContentCategoryChart))
			for _, item := range data.ContentCategoryChart {
				categoryLines = append(categoryLines, fmt.Sprintf("%s: %d piezas (%s)", item.Label, item.Count, formatPercent(item.Percent)))
			}
			writeSection("Categorías con mayor actividad", "Participación de cada categoría sobre el total publicado.", categoryLines)

			roleLines := make([]string, 0, len(data.ContentRoleChart))
			for _, item := range data.ContentRoleChart {
				roleLines = append(roleLines, fmt.Sprintf("%s: %d colaboraciones (%s del total reportado)", item.Label, item.Count, formatPercent(item.Percent)))
			}
			writeSection("Participación por rol", "Colaboración de los distintos roles en la generación de contenido.", roleLines)
		}

		if len(data.ContentMonthlySeries) > 0 {
			monthlyLines := make([]string, 0, min(len(data.ContentMonthlySeries), 24))
			for idx, point := range data.ContentMonthlySeries {
				if idx >= 24 {
					break
				}
				monthlyLines = append(monthlyLines, fmt.Sprintf("%s: %d piezas nuevas", point.Bucket.Format("2006-01"), point.Count))
			}
			writeSection("Producción mensual", "Evolución de piezas generadas mes contra mes.", monthlyLines)
		}

		if len(data.ContentCumulativeSeries) > 0 {
			cumulativeLines := make([]string, 0, min(len(data.ContentCumulativeSeries), 24))
			acum := 0
			for idx, point := range data.ContentCumulativeSeries {
				if idx >= 24 {
					break
				}
				acum = point.Count
				cumulativeLines = append(cumulativeLines, fmt.Sprintf("%s: %d piezas acumuladas", point.Bucket.Format("2006-01"), acum))
			}
			writeSection("Crecimiento acumulado", "Sumatoria histórica de contenido publicado.", cumulativeLines)
		}

		if err := pdf.Output(w); err != nil && h.logger != nil {
			h.logger.Error("pdf export error", zap.Error(err))
		}
		h.writeAudit(ctx, r, "DASHBOARD_EXPORT", "dashboard", nil, map[string]any{"format": "pdf", "rows": len(data.RecentActivity)})
	}
}

type contentListFilters struct {
	Type     string
	Status   string
	Category string
	Search   string
}

type contentListViewData struct {
	Items      []models.ContentItem
	Filters    contentListFilters
	Statuses   []models.CatalogItem
	Categories []models.CatalogItem
	Types      []models.CatalogItem
}

type contentFormFields struct {
	Title           string
	Summary         string
	Slug            string
	Locale          string
	Status          string
	Category        string
	Type            string
	AuthorEmail     string
	Body            string
	Note            string
	PublishedAt     string
	ForceNewVersion bool
}

type contentFormViewData struct {
	Item       *models.ContentDetail
	Form       contentFormFields
	Statuses   []models.CatalogItem
	Categories []models.CatalogItem
	Types      []models.CatalogItem
	Authors    []models.ContentAuthor
	Versions   []models.ContentVersion
	IsNew      bool
	Error      string
}

func (h *Handlers) loadContentCatalogs(ctx context.Context) (statuses, categories, types []models.CatalogItem, err error) {
	statuses, err = h.repo.ListCatalog(ctx, "content_statuses", 100, 0)
	if err != nil {
		return nil, nil, nil, err
	}
	categories, err = h.repo.ListCatalog(ctx, "content_categories", 100, 0)
	if err != nil {
		return nil, nil, nil, err
	}
	types, err = h.repo.ListCatalog(ctx, "content_types", 100, 0)
	if err != nil {
		return nil, nil, nil, err
	}
	return statuses, categories, types, nil
}

func parseDateTimeLocal(input string) (*time.Time, error) {
	trimmed := strings.TrimSpace(input)
	if trimmed == "" {
		return nil, nil
	}
	t, err := time.ParseInLocation("2006-01-02T15:04", trimmed, time.Local)
	if err != nil {
		return nil, err
	}
	return &t, nil
}

func optionalString(raw string) *string {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return nil
	}
	val := trimmed
	return &val
}

func optionalJSON(raw string) (*string, error) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return nil, nil
	}
	if !json.Valid([]byte(trimmed)) {
		return nil, fmt.Errorf("JSON inválido")
	}
	val := trimmed
	return &val, nil
}

func optionalFloat32(raw string) (*float32, error) {
	trimmed := strings.TrimSpace(raw)
	if trimmed == "" {
		return nil, nil
	}
	val, err := strconv.ParseFloat(trimmed, 32)
	if err != nil {
		return nil, err
	}
	f32 := float32(val)
	return &f32, nil
}

func (h *Handlers) ContentIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	rawType := strings.TrimSpace(r.URL.Query().Get("type"))
	rawStatus := strings.TrimSpace(r.URL.Query().Get("status"))
	rawCategory := strings.TrimSpace(r.URL.Query().Get("category"))
	rawSearch := strings.TrimSpace(r.URL.Query().Get("q"))

	filters := models.ContentFilters{Limit: 100, Offset: 0}
	if rawType != "" {
		lower := strings.ToLower(rawType)
		filters.TypeCode = &lower
	}
	if rawStatus != "" {
		lower := strings.ToLower(rawStatus)
		filters.StatusCode = &lower
	}
	if rawCategory != "" {
		lower := strings.ToLower(rawCategory)
		filters.CategoryCode = &lower
	}
	if rawSearch != "" {
		filters.Search = &rawSearch
	}

	items, err := h.repo.ListContent(ctx, filters)
	if err != nil {
		http.Error(w, "No se pudo cargar el contenido", http.StatusInternalServerError)
		return
	}

	statuses, categories, types, err := h.loadContentCatalogs(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los catálogos", http.StatusInternalServerError)
		return
	}

	data := contentListViewData{
		Items: items,
		Filters: contentListFilters{
			Type:     rawType,
			Status:   rawStatus,
			Category: rawCategory,
			Search:   rawSearch,
		},
		Statuses:   statuses,
		Categories: categories,
		Types:      types,
	}

	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Contenido"}}
	h.render(w, r, "superadmin/content_list.html", "Contenido", data, crumbs)
}

func defaultContentForm(statuses, categories, types []models.CatalogItem) contentFormFields {
	form := contentFormFields{Locale: "es"}
	for _, status := range statuses {
		if strings.EqualFold(status.Code, "draft") {
			form.Status = status.Code
			break
		}
	}
	if form.Status == "" && len(statuses) > 0 {
		form.Status = statuses[0].Code
	}
	if len(categories) > 0 {
		form.Category = categories[0].Code
	}
	if len(types) > 0 {
		form.Type = types[0].Code
	}
	return form
}

func (h *Handlers) renderContentForm(w http.ResponseWriter, r *http.Request, title string, data contentFormViewData) {
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Contenido", URL: "/superadmin/content"}}
	switch {
	case data.IsNew:
		crumbs = append(crumbs, ui.Breadcrumb{Label: "Nuevo"})
	case data.Item != nil && data.Item.Title != "":
		crumbs = append(crumbs, ui.Breadcrumb{Label: data.Item.Title})
	default:
		crumbs = append(crumbs, ui.Breadcrumb{Label: title})
	}
	h.render(w, r, "superadmin/content_edit.html", title, data, crumbs)
}

func (h *Handlers) ContentNew(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	statuses, categories, types, err := h.loadContentCatalogs(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los catálogos", http.StatusInternalServerError)
		return
	}

	authors, err := h.repo.ListContentAuthors(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los autores", http.StatusInternalServerError)
		return
	}

	data := contentFormViewData{
		Form:       defaultContentForm(statuses, categories, types),
		Statuses:   statuses,
		Categories: categories,
		Types:      types,
		Authors:    authors,
		IsNew:      true,
	}
	h.renderContentForm(w, r, "Nuevo contenido", data)
}

func (h *Handlers) ContentCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "Formulario inválido", http.StatusBadRequest)
		return
	}

	form := contentFormFields{
		Title:       strings.TrimSpace(r.FormValue("title")),
		Summary:     strings.TrimSpace(r.FormValue("summary")),
		Slug:        strings.TrimSpace(r.FormValue("slug")),
		Locale:      strings.TrimSpace(r.FormValue("locale")),
		Status:      strings.TrimSpace(r.FormValue("status")),
		Category:    strings.TrimSpace(r.FormValue("category")),
		Type:        strings.TrimSpace(r.FormValue("type")),
		AuthorEmail: strings.TrimSpace(r.FormValue("author_email")),
		Body:        strings.TrimSpace(r.FormValue("body")),
		Note:        strings.TrimSpace(r.FormValue("note")),
		PublishedAt: strings.TrimSpace(r.FormValue("published_at")),
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	statuses, categories, types, err := h.loadContentCatalogs(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los catálogos", http.StatusInternalServerError)
		return
	}

	authors, err := h.repo.ListContentAuthors(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los autores", http.StatusInternalServerError)
		return
	}

	validateError := ""
	switch {
	case form.Title == "":
		validateError = "El título es obligatorio"
	case form.Status == "":
		validateError = "Selecciona un estatus"
	case form.Category == "":
		validateError = "Selecciona una categoría"
	case form.Type == "":
		validateError = "Selecciona un tipo de contenido"
	case form.Body == "":
		validateError = "El contenido principal no puede estar vacío"
	}
	if validateError != "" {
		data := contentFormViewData{
			Form:       form,
			Statuses:   statuses,
			Categories: categories,
			Types:      types,
			Authors:    authors,
			IsNew:      true,
			Error:      validateError,
		}
		h.renderContentForm(w, r, "Nuevo contenido", data)
		return
	}

	publishedAt, err := parseDateTimeLocal(form.PublishedAt)
	if err != nil {
		data := contentFormViewData{
			Form:       form,
			Statuses:   statuses,
			Categories: categories,
			Types:      types,
			Authors:    authors,
			IsNew:      true,
			Error:      "Fecha de publicación inválida",
		}
		h.renderContentForm(w, r, "Nuevo contenido", data)
		return
	}

	input := models.ContentCreateInput{
		Title:        form.Title,
		StatusCode:   strings.ToLower(form.Status),
		CategoryCode: strings.ToLower(form.Category),
		TypeCode:     strings.ToLower(form.Type),
		Body:         form.Body,
	}
	if form.Summary != "" {
		input.Summary = &form.Summary
	}
	if form.Slug != "" {
		input.Slug = &form.Slug
	}
	if form.Locale != "" {
		input.Locale = &form.Locale
	}
	if form.AuthorEmail != "" {
		input.AuthorEmail = &form.AuthorEmail
	}
	if form.Note != "" {
		input.Note = &form.Note
	}
	if publishedAt != nil {
		input.PublishedAt = publishedAt
	}

	actorID := middleware.UserIDFromContext(r.Context())
	var actorPtr *string
	if actorID != "" {
		actorPtr = &actorID
	}

	detail, err := h.repo.CreateContent(ctx, input, actorPtr)
	if err != nil {
		message := "No se pudo crear el contenido"
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Message != "" {
			message = pgErr.Message
		}
		if h.logger != nil {
			h.logger.Error("content create", zap.Error(err))
		}
		data := contentFormViewData{
			Form:       form,
			Statuses:   statuses,
			Categories: categories,
			Types:      types,
			Authors:    authors,
			IsNew:      true,
			Error:      message,
		}
		h.renderContentForm(w, r, "Nuevo contenido", data)
		return
	}

	h.writeAudit(ctx, r, "CONTENT_CREATE", "content", &detail.ID, map[string]any{"status": detail.StatusCode, "category": detail.CategoryCode})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Contenido creado"})
	http.Redirect(w, r, fmt.Sprintf("/superadmin/content/%s", detail.ID), http.StatusSeeOther)
}

func (h *Handlers) ContentEdit(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	detail, err := h.repo.GetContent(ctx, id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			http.Error(w, "Contenido no encontrado", http.StatusNotFound)
			return
		}
		http.Error(w, "No se pudo cargar el contenido", http.StatusInternalServerError)
		return
	}

	statuses, categories, types, err := h.loadContentCatalogs(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los catálogos", http.StatusInternalServerError)
		return
	}

	authors, err := h.repo.ListContentAuthors(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los autores", http.StatusInternalServerError)
		return
	}

	versions, err := h.repo.ListContentVersions(ctx, id, 10, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las versiones", http.StatusInternalServerError)
		return
	}

	form := contentFormFields{
		Title:    detail.Title,
		Locale:   detail.Locale,
		Status:   detail.StatusCode,
		Category: detail.CategoryCode,
		Type:     detail.TypeCode,
		Body:     detail.Body,
	}
	if detail.Summary != nil {
		form.Summary = *detail.Summary
	}
	if detail.Slug != nil {
		form.Slug = *detail.Slug
	}
	if detail.AuthorEmail != nil {
		form.AuthorEmail = *detail.AuthorEmail
	}
	if detail.PublishedAt != nil {
		form.PublishedAt = detail.PublishedAt.In(time.Local).Format("2006-01-02T15:04")
	}

	data := contentFormViewData{
		Item:       detail,
		Form:       form,
		Statuses:   statuses,
		Categories: categories,
		Types:      types,
		Authors:    authors,
		Versions:   versions,
		IsNew:      false,
	}
	title := fmt.Sprintf("Editar: %s", detail.Title)
	h.renderContentForm(w, r, title, data)
}

func (h *Handlers) ContentUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "Formulario inválido", http.StatusBadRequest)
		return
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	detail, err := h.repo.GetContent(ctx, id)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			http.Error(w, "Contenido no encontrado", http.StatusNotFound)
			return
		}
		http.Error(w, "No se pudo cargar el contenido", http.StatusInternalServerError)
		return
	}

	statuses, categories, types, err := h.loadContentCatalogs(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los catálogos", http.StatusInternalServerError)
		return
	}

	authors, err := h.repo.ListContentAuthors(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los autores", http.StatusInternalServerError)
		return
	}

	versions, err := h.repo.ListContentVersions(ctx, id, 10, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las versiones", http.StatusInternalServerError)
		return
	}

	form := contentFormFields{
		Title:           strings.TrimSpace(r.FormValue("title")),
		Summary:         strings.TrimSpace(r.FormValue("summary")),
		Slug:            strings.TrimSpace(r.FormValue("slug")),
		Locale:          strings.TrimSpace(r.FormValue("locale")),
		Status:          strings.TrimSpace(r.FormValue("status")),
		Category:        strings.TrimSpace(r.FormValue("category")),
		Type:            strings.TrimSpace(r.FormValue("type")),
		AuthorEmail:     strings.TrimSpace(r.FormValue("author_email")),
		Body:            strings.TrimSpace(r.FormValue("body")),
		Note:            strings.TrimSpace(r.FormValue("note")),
		PublishedAt:     strings.TrimSpace(r.FormValue("published_at")),
		ForceNewVersion: r.FormValue("force_new_version") != "",
	}

	validateError := ""
	switch {
	case form.Title == "":
		validateError = "El título es obligatorio"
	case form.Status == "":
		validateError = "Selecciona un estatus"
	case form.Category == "":
		validateError = "Selecciona una categoría"
	case form.Type == "":
		validateError = "Selecciona un tipo de contenido"
	case form.Body == "":
		validateError = "El contenido principal no puede estar vacío"
	}
	if validateError != "" {
		data := contentFormViewData{
			Item:       detail,
			Form:       form,
			Statuses:   statuses,
			Categories: categories,
			Types:      types,
			Authors:    authors,
			Versions:   versions,
			Error:      validateError,
		}
		title := fmt.Sprintf("Editar: %s", detail.Title)
		h.renderContentForm(w, r, title, data)
		return
	}

	publishedAt, err := parseDateTimeLocal(form.PublishedAt)
	if err != nil {
		data := contentFormViewData{
			Item:       detail,
			Form:       form,
			Statuses:   statuses,
			Categories: categories,
			Types:      types,
			Authors:    authors,
			Versions:   versions,
			Error:      "Fecha de publicación inválida",
		}
		title := fmt.Sprintf("Editar: %s", detail.Title)
		h.renderContentForm(w, r, title, data)
		return
	}

	input := models.ContentUpdateInput{
		ForceNewVersion: form.ForceNewVersion,
	}
	titleCopy := form.Title
	input.Title = &titleCopy
	summaryCopy := form.Summary
	input.Summary = &summaryCopy
	slugCopy := form.Slug
	input.Slug = &slugCopy
	localeCopy := form.Locale
	input.Locale = &localeCopy
	statusCopy := strings.ToLower(form.Status)
	input.StatusCode = &statusCopy
	categoryCopy := strings.ToLower(form.Category)
	input.CategoryCode = &categoryCopy
	typeCopy := strings.ToLower(form.Type)
	input.TypeCode = &typeCopy
	authorCopy := form.AuthorEmail
	input.AuthorEmail = &authorCopy
	bodyCopy := form.Body
	input.Body = &bodyCopy
	noteCopy := form.Note
	if form.Note != "" {
		input.Note = &noteCopy
	}
	if publishedAt != nil {
		input.PublishedAt = publishedAt
	}

	actorID := middleware.UserIDFromContext(r.Context())
	var actorPtr *string
	if actorID != "" {
		actorPtr = &actorID
	}

	updated, err := h.repo.UpdateContent(ctx, id, input, actorPtr)
	if err != nil {
		message := "No se pudo actualizar el contenido"
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Message != "" {
			message = pgErr.Message
		}
		if h.logger != nil {
			h.logger.Error("content update", zap.Error(err), zap.String("id", id))
		}
		data := contentFormViewData{
			Item:       detail,
			Form:       form,
			Statuses:   statuses,
			Categories: categories,
			Types:      types,
			Authors:    authors,
			Versions:   versions,
			Error:      message,
		}
		title := fmt.Sprintf("Editar: %s", detail.Title)
		h.renderContentForm(w, r, title, data)
		return
	}

	h.writeAudit(ctx, r, "CONTENT_UPDATE", "content", &updated.ID, map[string]any{"status": updated.StatusCode})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Contenido actualizado"})
	http.Redirect(w, r, fmt.Sprintf("/superadmin/content/%s", updated.ID), http.StatusSeeOther)
}

func (h *Handlers) ContentDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	if err := h.repo.DeleteContent(ctx, id); err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			http.Error(w, "Contenido no encontrado", http.StatusNotFound)
			return
		}
		http.Error(w, "No se pudo eliminar el contenido", http.StatusInternalServerError)
		return
	}

	h.writeAudit(ctx, r, "CONTENT_DELETE", "content", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Contenido eliminado"})
	http.Redirect(w, r, "/superadmin/content", http.StatusSeeOther)
}

type organizationForm struct {
	Code string `validate:"required,uppercase,min=2,max=60"`
	Name string `validate:"required,min=3,max=160"`
}

type organizationsViewData struct {
	Organizations []models.Organization
	FormError     string
	FormFields    organizationForm
}

func (h *Handlers) OrganizationsIndex(w http.ResponseWriter, r *http.Request) {
	limit := 100
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	list, err := h.repo.ListOrganizations(ctx, limit, 0)
	if err != nil {
		http.Error(w, "no se pudieron cargar las organizaciones", http.StatusInternalServerError)
		return
	}
	data := organizationsViewData{Organizations: list}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Organizaciones"}}
	h.render(w, r, "superadmin/organizations_list.html", "Organizaciones", data, crumbs)
}

func (h *Handlers) OrganizationsCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	form := organizationForm{
		Code: strings.TrimSpace(strings.ToUpper(r.FormValue("code"))),
		Name: strings.TrimSpace(r.FormValue("name")),
	}
	if err := h.validate.Struct(&form); err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Datos inválidos"})
		http.Redirect(w, r, "/superadmin/organizations", http.StatusSeeOther)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	org, err := h.repo.CreateOrganization(ctx, form.Code, form.Name)
	if err != nil {
		message := "No se pudo crear la organización"
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			message = "Ya existe una organización con ese código"
		}
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: message})
		http.Redirect(w, r, "/superadmin/organizations", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "ORG_CREATE", "organization", &org.ID, map[string]any{"code": org.Code})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Organización creada"})
	http.Redirect(w, r, "/superadmin/organizations", http.StatusSeeOther)
}

type organizationDetailData struct {
	Organization *models.Organization
	Members      []models.Membership
	Invitations  []models.OrgInvitation
}

func (h *Handlers) OrganizationDetail(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	org, err := h.repo.GetOrganization(ctx, id)
	if err != nil {
		http.Error(w, "Organización no encontrada", http.StatusNotFound)
		return
	}
	members, err := h.repo.ListMembers(ctx, id, 100, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los miembros", http.StatusInternalServerError)
		return
	}
	invitations, err := h.repo.ListInvitations(ctx, &id, 50, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las invitaciones", http.StatusInternalServerError)
		return
	}
	data := organizationDetailData{
		Organization: org,
		Members:      members,
		Invitations:  invitations,
	}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Organizaciones", URL: "/superadmin/organizations"}, {Label: org.Name}}
	h.render(w, r, "superadmin/organization_detail.html", org.Name, data, crumbs)
}

func (h *Handlers) OrganizationDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteOrganization(ctx, id); err != nil {
		status := http.StatusInternalServerError
		msg := "No se pudo eliminar la organización"
		if errors.Is(err, pgx.ErrNoRows) {
			status = http.StatusNotFound
			msg = "Organización no encontrada"
		}
		http.Error(w, msg, status)
		return
	}
	h.writeAudit(ctx, r, "ORG_DELETE", "organization", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Organización eliminada"})
	http.Redirect(w, r, "/superadmin/organizations", http.StatusSeeOther)
}

type invitationsViewData struct {
	Invitations   []models.OrgInvitation
	Organizations []models.Organization
	OrgNames      map[string]string
	SelectedOrgID string
}

type userStatusOption struct {
	Code  string
	Label string
}

var userStatusOptions = []userStatusOption{
	{Code: "active", Label: "Activo"},
	{Code: "pending", Label: "Pendiente"},
	{Code: "blocked", Label: "Bloqueado"},
}

var userStatusAllowed = map[string]bool{
	"active":  true,
	"pending": true,
	"blocked": true,
}

type usersViewData struct {
	Users  []models.User
	Query  string
	Status []userStatusOption
	Roles  []models.Role
}

type rolesViewData struct {
	Roles     []models.Role
	FormError string
	FormName  string
	FormDesc  string
}

type catalogNavItem struct {
	Slug  string
	Label string
}

type catalogsViewData struct {
	Catalogs       []catalogNavItem
	CurrentSlug    string
	CurrentMeta    catalogMeta
	Items          []models.CatalogItem
	RequiresWeight bool
}

type contentBlockTypesViewData struct {
	Items []models.ContentBlockType
}

type patientsViewData struct {
	Items         []models.Patient
	Organizations []models.Organization
	Sexes         []models.CatalogItem
}

type devicesViewData struct {
	Items         []models.Device
	Organizations []models.Organization
	DeviceTypes   []models.DeviceType
	Patients      []models.Patient
}

type signalStreamsViewData struct {
	Items       []models.SignalStream
	Patients    []models.Patient
	Devices     []models.Device
	SignalTypes []models.CatalogItem
}

type modelsViewData struct {
	Items []models.MLModel
}

type eventTypesViewData struct {
	Items  []models.EventType
	Levels []models.CatalogItem
}

type inferencesViewData struct {
	Items      []models.Inference
	Models     []models.MLModel
	Streams    []models.SignalStream
	EventTypes []models.EventType
}

type alertsViewData struct {
	Items         []models.Alert
	Patients      []models.Patient
	AlertTypes    []models.AlertType
	AlertStatuses []models.AlertStatus
	AlertLevels   []models.CatalogItem
	Models        []models.MLModel
	Inferences    []models.Inference
}

type apiKeysViewData struct {
	Keys         []models.APIKey
	Permissions  []models.Permission
	ShowInactive bool
}

type systemSettingsViewData struct {
	Settings *models.SystemSettings
}

type auditLogItem struct {
	Log         models.AuditLog
	ActionLabel string
}

type auditViewData struct {
	From    string
	To      string
	Action  string
	Logs    []auditLogItem
	Actions []catalogNavItem
}

func catalogNavItems() []catalogNavItem {
	slugs := make([]string, 0, len(allowedCatalogs))
	for slug := range allowedCatalogs {
		slugs = append(slugs, slug)
	}
	sort.Strings(slugs)
	items := make([]catalogNavItem, 0, len(slugs))
	for _, slug := range slugs {
		meta := allowedCatalogs[slug]
		items = append(items, catalogNavItem{Slug: slug, Label: meta.Label})
	}
	return items
}

func auditActionOptions() []catalogNavItem {
	codes := make([]string, 0, len(operationLabels))
	for code := range operationLabels {
		codes = append(codes, code)
	}
	sort.Strings(codes)
	options := make([]catalogNavItem, 0, len(codes))
	for _, code := range codes {
		options = append(options, catalogNavItem{Slug: code, Label: operationLabel(code)})
	}
	return options
}

func (h *Handlers) InvitationsIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	orgs, err := h.repo.ListOrganizations(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las organizaciones", http.StatusInternalServerError)
		return
	}

	var selected *string
	selectedID := strings.TrimSpace(r.URL.Query().Get("org_id"))
	if selectedID != "" {
		selected = &selectedID
	}

	invites, err := h.repo.ListInvitations(ctx, selected, 100, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las invitaciones", http.StatusInternalServerError)
		return
	}

	names := make(map[string]string, len(orgs))
	for _, org := range orgs {
		names[org.ID] = org.Name
	}
	data := invitationsViewData{
		Invitations:   invites,
		Organizations: orgs,
		OrgNames:      names,
		SelectedOrgID: selectedID,
	}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Invitaciones"}}
	h.render(w, r, "superadmin/invitations.html", "Invitaciones", data, crumbs)
}

func (h *Handlers) InvitationsCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	orgID := strings.TrimSpace(r.FormValue("org_id"))
	role := strings.TrimSpace(r.FormValue("org_role"))
	email := strings.TrimSpace(r.FormValue("email"))
	ttlStr := strings.TrimSpace(r.FormValue("ttl_hours"))
	if orgID == "" || role == "" || ttlStr == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Todos los campos obligatorios deben completarse"})
		http.Redirect(w, r, "/superadmin/invitations", http.StatusSeeOther)
		return
	}
	ttl, err := strconv.Atoi(ttlStr)
	if err != nil || ttl <= 0 || ttl > 720 {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "TTL inválido"})
		http.Redirect(w, r, "/superadmin/invitations", http.StatusSeeOther)
		return
	}
	var emailPtr *string
	if email != "" {
		emailPtr = &email
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	createdBy := middleware.UserIDFromContext(r.Context())
	var createdByPtr *string
	if createdBy != "" {
		createdByPtr = &createdBy
	}
	inv, err := h.repo.CreateInvitation(ctx, orgID, role, emailPtr, ttl, createdByPtr)
	if err != nil {
		msg := "No se pudo crear la invitación"
		if errors.Is(err, pgx.ErrNoRows) {
			msg = "Rol u organización inválidos"
		}
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23503" {
			msg = "El rol seleccionado no existe"
		}
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: msg})
		http.Redirect(w, r, "/superadmin/invitations", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "INVITE_CREATE", "org_invitation", &inv.ID, map[string]any{"org_id": orgID})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Invitación creada"})
	http.Redirect(w, r, "/superadmin/invitations", http.StatusSeeOther)
}

func (h *Handlers) InvitationCancel(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.CancelInvitation(ctx, id); err != nil {
		status := http.StatusInternalServerError
		msg := "No se pudo cancelar la invitación"
		if errors.Is(err, pgx.ErrNoRows) {
			status = http.StatusNotFound
			msg = "Invitación no encontrada o ya procesada"
		}
		http.Error(w, msg, status)
		return
	}
	h.writeAudit(ctx, r, "INVITE_CANCEL", "org_invitation", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Invitación cancelada"})
	http.Redirect(w, r, "/superadmin/invitations", http.StatusSeeOther)
}

func (h *Handlers) UsersIndex(w http.ResponseWriter, r *http.Request) {
	query := strings.TrimSpace(r.URL.Query().Get("q"))
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	users, err := h.repo.SearchUsers(ctx, query, 100, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los usuarios", http.StatusInternalServerError)
		return
	}
	roles, err := h.repo.ListRoles(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los roles", http.StatusInternalServerError)
		return
	}
	data := usersViewData{Users: users, Query: query, Status: userStatusOptions, Roles: roles}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Usuarios"}}
	h.render(w, r, "superadmin/users.html", "Usuarios", data, crumbs)
}

func (h *Handlers) UsersUpdateStatus(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	userID := chi.URLParam(r, "id")
	status := strings.TrimSpace(r.FormValue("status"))
	redirectURL := strings.TrimSpace(r.FormValue("redirect"))
	if redirectURL == "" || !strings.HasPrefix(redirectURL, "/") {
		redirectURL = "/superadmin/users"
	}
	if !userStatusAllowed[status] {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Estado inválido"})
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.UpdateUserStatus(ctx, userID, status); err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el estado"})
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "USER_STATUS_UPDATE", "user", &userID, map[string]any{"status": status})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Estado actualizado"})
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func (h *Handlers) RolesIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	roles, err := h.repo.ListRoles(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los roles", http.StatusInternalServerError)
		return
	}
	data := rolesViewData{Roles: roles}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Roles"}}
	h.render(w, r, "superadmin/roles.html", "Roles", data, crumbs)
}

func (h *Handlers) RolesCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	desc := strings.TrimSpace(r.FormValue("description"))

	redirect := "/superadmin/roles"

	if name == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El nombre es obligatorio"})
		http.Redirect(w, r, redirect, http.StatusSeeOther)
		return
	}
	if len(name) < 3 || len(name) > 50 {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El nombre debe tener entre 3 y 50 caracteres"})
		http.Redirect(w, r, redirect, http.StatusSeeOther)
		return
	}
	var descPtr *string
	if desc != "" {
		if len(desc) > 250 {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "La descripción no puede exceder 250 caracteres"})
			http.Redirect(w, r, redirect, http.StatusSeeOther)
			return
		}
		descPtr = &desc
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	role, err := h.repo.CreateRole(ctx, name, descPtr)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Ya existe un rol con ese nombre"})
		} else {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el rol"})
		}
		http.Redirect(w, r, redirect, http.StatusSeeOther)
		return
	}

	h.writeAudit(ctx, r, "ROLE_CREATE", "role", &role.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Rol creado"})
	http.Redirect(w, r, redirect, http.StatusSeeOther)
}

func (h *Handlers) RolesDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	if err := h.repo.DeleteRole(ctx, id); err != nil {
		status := http.StatusInternalServerError
		msg := "No se pudo eliminar el rol"
		if errors.Is(err, pgx.ErrNoRows) {
			status = http.StatusNotFound
			msg = "Rol no encontrado"
		}
		http.Error(w, msg, status)
		return
	}

	h.writeAudit(ctx, r, "ROLE_DELETE", "role", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Rol eliminado"})
	http.Redirect(w, r, "/superadmin/roles", http.StatusSeeOther)
}

func (h *Handlers) RolesUpdateUserAssignment(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	userID := chi.URLParam(r, "id")
	selected := strings.TrimSpace(r.FormValue("role_id"))
	redirect := strings.TrimSpace(r.FormValue("redirect"))
	if redirect == "" || !strings.HasPrefix(redirect, "/") {
		redirect = "/superadmin/roles"
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	current, err := h.repo.ListUserRoles(ctx, userID)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudieron recuperar los roles del usuario"})
		http.Redirect(w, r, redirect, http.StatusSeeOther)
		return
	}

	desired := selected != ""
	alreadyAssigned := false
	for _, role := range current {
		if desired && role.RoleID == selected {
			alreadyAssigned = true
			continue
		}
		if err := h.repo.RemoveRoleFromUser(ctx, userID, role.RoleID); err != nil && !errors.Is(err, pgx.ErrNoRows) {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el rol"})
			http.Redirect(w, r, redirect, http.StatusSeeOther)
			return
		}
		h.writeAudit(ctx, r, "USER_ROLE_REMOVE", "user", &userID, map[string]any{"role_id": role.RoleID})
	}

	if desired && !alreadyAssigned {
		if _, err := h.repo.AssignRoleToUser(ctx, userID, selected); err != nil {
			var msg string
			switch {
			case errors.Is(err, pgx.ErrNoRows):
				msg = "El rol seleccionado no existe"
			default:
				msg = "No se pudo asignar el rol"
			}
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: msg})
			http.Redirect(w, r, redirect, http.StatusSeeOther)
			return
		}
		h.writeAudit(ctx, r, "USER_ROLE_ASSIGN", "user", &userID, map[string]any{"role_id": selected})
	}

	flashMsg := "Se eliminó el rol asignado"
	if desired {
		flashMsg = "Rol actualizado"
	}
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: flashMsg})
	http.Redirect(w, r, redirect, http.StatusSeeOther)
}

func (h *Handlers) CatalogsIndex(w http.ResponseWriter, r *http.Request) {
	slug := chi.URLParam(r, "catalog")
	if slug == "" {
		slug = "user_statuses"
	}
	meta, ok := allowedCatalogs[slug]
	if !ok {
		http.NotFound(w, r)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	items, err := h.repo.ListCatalog(ctx, slug, 500, 0)
	if err != nil {
		http.Error(w, "No se pudo cargar el catálogo", http.StatusInternalServerError)
		return
	}
	data := catalogsViewData{
		Catalogs:       catalogNavItems(),
		CurrentSlug:    slug,
		CurrentMeta:    meta,
		Items:          items,
		RequiresWeight: meta.RequiresWeight,
	}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Catálogos", URL: "/superadmin/catalogs"}, {Label: meta.Label}}
	h.render(w, r, "superadmin/catalogs.html", "Catálogo", data, crumbs)
}

func (h *Handlers) CatalogsCreate(w http.ResponseWriter, r *http.Request) {
	slug := chi.URLParam(r, "catalog")
	meta, ok := allowedCatalogs[slug]
	if !ok {
		http.NotFound(w, r)
		return
	}
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	code := strings.TrimSpace(r.FormValue("code"))
	label := strings.TrimSpace(r.FormValue("label"))
	weightStr := strings.TrimSpace(r.FormValue("weight"))
	redirectURL := "/superadmin/catalogs/" + slug
	if code == "" || label == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Código y nombre son obligatorios"})
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}
	var weight *int
	if weightStr != "" {
		val, err := strconv.Atoi(weightStr)
		if err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Peso inválido"})
			http.Redirect(w, r, redirectURL, http.StatusSeeOther)
			return
		}
		weight = &val
	}
	if meta.RequiresWeight && weight == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Este catálogo requiere peso"})
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	item, err := h.repo.CreateCatalogItem(ctx, slug, code, label, weight)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) {
			switch pgErr.Code {
			case "23505":
				h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El código ya existe"})
			case "23503":
				h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Valor relacionado inválido"})
			default:
				h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el elemento"})
			}
		} else {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el elemento"})
		}
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "CATALOG_CREATE", "catalog_item", &item.ID, map[string]any{"catalog": slug})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Elemento creado"})
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func (h *Handlers) CatalogsUpdate(w http.ResponseWriter, r *http.Request) {
	slug := chi.URLParam(r, "catalog")
	if _, ok := allowedCatalogs[slug]; !ok {
		http.NotFound(w, r)
		return
	}
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	redirectURL := "/superadmin/catalogs/" + slug
	code := strings.TrimSpace(r.FormValue("code"))
	label := strings.TrimSpace(r.FormValue("label"))
	weightStr := strings.TrimSpace(r.FormValue("weight"))

	var codePtr *string
	if code != "" {
		codePtr = &code
	}
	var labelPtr *string
	if label != "" {
		labelPtr = &label
	}
	var weightPtr *int
	if weightStr != "" {
		val, err := strconv.Atoi(weightStr)
		if err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Peso inválido"})
			http.Redirect(w, r, redirectURL, http.StatusSeeOther)
			return
		}
		weightPtr = &val
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	item, err := h.repo.UpdateCatalogItem(ctx, slug, id, codePtr, labelPtr, weightPtr)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El código ya existe"})
		} else if errors.Is(err, pgx.ErrNoRows) {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Elemento no encontrado"})
		} else {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar"})
		}
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "CATALOG_UPDATE", "catalog_item", &item.ID, map[string]any{"catalog": slug})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Elemento actualizado"})
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func (h *Handlers) CatalogsDelete(w http.ResponseWriter, r *http.Request) {
	slug := chi.URLParam(r, "catalog")
	if _, ok := allowedCatalogs[slug]; !ok {
		http.NotFound(w, r)
		return
	}
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteCatalogItem(ctx, slug, id); err != nil {
		status := http.StatusInternalServerError
		msg := "No se pudo eliminar"
		if errors.Is(err, pgx.ErrNoRows) {
			status = http.StatusNotFound
			msg = "Elemento no encontrado"
		}
		http.Error(w, msg, status)
		return
	}
	h.writeAudit(ctx, r, "CATALOG_DELETE", "catalog_item", &id, map[string]any{"catalog": slug})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Elemento eliminado"})
	http.Redirect(w, r, "/superadmin/catalogs/"+slug, http.StatusSeeOther)
}

func (h *Handlers) ContentBlockTypesIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	items, err := h.repo.ListContentBlockTypes(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los tipos de bloque", http.StatusInternalServerError)
		return
	}

	data := contentBlockTypesViewData{Items: items}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Tipos de bloque"}}
	h.render(w, r, "superadmin/content_blocks.html", "Tipos de bloque", data, crumbs)
}

func (h *Handlers) ContentBlockTypesCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	code := strings.TrimSpace(r.FormValue("code"))
	label := strings.TrimSpace(r.FormValue("label"))
	descriptionRaw := strings.TrimSpace(r.FormValue("description"))
	redirectURL := "/superadmin/content-block-types"

	if code == "" || label == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Código y nombre son obligatorios"})
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}

	var description *string
	if descriptionRaw != "" {
		descCopy := descriptionRaw
		description = &descCopy
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	item, err := h.repo.CreateContentBlockType(ctx, code, label, description)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) {
			switch pgErr.Code {
			case "23505":
				h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El código ya existe"})
			case "23514":
				h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: pgErr.Message})
			default:
				h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el tipo de bloque"})
			}
		} else {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el tipo de bloque"})
		}
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}

	h.writeAudit(ctx, r, "CONTENT_BLOCK_TYPE_CREATE", "content_block_type", &item.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Tipo de bloque creado"})
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func (h *Handlers) ContentBlockTypesUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	redirectURL := "/superadmin/content-block-types"
	code := strings.TrimSpace(r.FormValue("code"))
	label := strings.TrimSpace(r.FormValue("label"))
	descriptionVal := strings.TrimSpace(r.FormValue("description"))

	if code == "" || label == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Código y nombre son obligatorios"})
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}

	codeCopy := code
	labelCopy := label
	descCopy := descriptionVal
	descPtr := &descCopy

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	item, err := h.repo.UpdateContentBlockType(ctx, id, &codeCopy, &labelCopy, descPtr)
	if err != nil {
		var pgErr *pgconn.PgError
		if errors.As(err, &pgErr) && pgErr.Code == "23505" {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El código ya existe"})
		} else if errors.Is(err, pgx.ErrNoRows) {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Tipo de bloque no encontrado"})
		} else {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el tipo de bloque"})
		}
		http.Redirect(w, r, redirectURL, http.StatusSeeOther)
		return
	}

	h.writeAudit(ctx, r, "CONTENT_BLOCK_TYPE_UPDATE", "content_block_type", &item.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Tipo de bloque actualizado"})
	http.Redirect(w, r, redirectURL, http.StatusSeeOther)
}

func (h *Handlers) ContentBlockTypesDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteContentBlockType(ctx, id); err != nil {
		status := http.StatusInternalServerError
		msg := "No se pudo eliminar"
		if errors.Is(err, pgx.ErrNoRows) {
			status = http.StatusNotFound
			msg = "Tipo de bloque no encontrado"
		}
		http.Error(w, msg, status)
		return
	}

	h.writeAudit(ctx, r, "CONTENT_BLOCK_TYPE_DELETE", "content_block_type", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Tipo de bloque eliminado"})
	http.Redirect(w, r, "/superadmin/content-block-types", http.StatusSeeOther)
}

// Patients

func (h *Handlers) PatientsIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	patients, err := h.repo.ListPatients(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los pacientes", http.StatusInternalServerError)
		return
	}
	orgs, err := h.repo.ListOrganizations(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las organizaciones", http.StatusInternalServerError)
		return
	}
	sexes, err := h.repo.ListCatalog(ctx, "sexes", 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los catálogos", http.StatusInternalServerError)
		return
	}

	data := patientsViewData{Items: patients, Organizations: orgs, Sexes: sexes}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Pacientes"}}
	h.render(w, r, "superadmin/patients.html", "Pacientes", data, crumbs)
}

func (h *Handlers) PatientsCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	if name == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Nombre es obligatorio"})
		http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
		return
	}
	orgIDRaw := strings.TrimSpace(r.FormValue("org_id"))
	var orgID *string
	if orgIDRaw != "" {
		orgID = &orgIDRaw
	}
	birthRaw := strings.TrimSpace(r.FormValue("birthdate"))
	var birth *time.Time
	if birthRaw != "" {
		parsed, err := time.Parse("2006-01-02", birthRaw)
		if err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de nacimiento inválida"})
			http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
			return
		}
		birth = &parsed
	}
	sexRaw := strings.TrimSpace(r.FormValue("sex_code"))
	var sexCode *string
	if sexRaw != "" {
		lower := strings.ToLower(sexRaw)
		sexCode = &lower
	}
	riskRaw := strings.TrimSpace(r.FormValue("risk_level"))
	var risk *string
	if riskRaw != "" {
		risk = &riskRaw
	}

	input := models.PatientInput{OrgID: orgID, Name: name, Birthdate: birth, SexCode: sexCode, RiskLevel: risk}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	patient, err := h.repo.CreatePatient(ctx, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el paciente"})
		http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "PATIENT_CREATE", "patient", &patient.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Paciente creado"})
	http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
}

func (h *Handlers) PatientsUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	if name == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Nombre es obligatorio"})
		http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
		return
	}
	orgIDRaw := strings.TrimSpace(r.FormValue("org_id"))
	var orgID *string
	if orgIDRaw != "" {
		orgID = &orgIDRaw
	}
	birthRaw := strings.TrimSpace(r.FormValue("birthdate"))
	var birth *time.Time
	if birthRaw != "" {
		parsed, err := time.Parse("2006-01-02", birthRaw)
		if err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de nacimiento inválida"})
			http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
			return
		}
		birth = &parsed
	}
	sexRaw := strings.TrimSpace(r.FormValue("sex_code"))
	var sexCode *string
	if sexRaw != "" {
		lower := strings.ToLower(sexRaw)
		sexCode = &lower
	}
	riskRaw := strings.TrimSpace(r.FormValue("risk_level"))
	var risk *string
	if riskRaw != "" {
		risk = &riskRaw
	}
	input := models.PatientInput{OrgID: orgID, Name: name, Birthdate: birth, SexCode: sexCode, RiskLevel: risk}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	patient, err := h.repo.UpdatePatient(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el paciente"})
		http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "PATIENT_UPDATE", "patient", &patient.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Paciente actualizado"})
	http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
}

func (h *Handlers) PatientsDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeletePatient(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "PATIENT_DELETE", "patient", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Paciente eliminado"})
	http.Redirect(w, r, "/superadmin/patients", http.StatusSeeOther)
}

// Devices

func (h *Handlers) DevicesIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	devices, err := h.repo.ListDevices(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los dispositivos", http.StatusInternalServerError)
		return
	}
	orgs, err := h.repo.ListOrganizations(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las organizaciones", http.StatusInternalServerError)
		return
	}
	deviceTypes, err := h.repo.ListDeviceTypes(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los tipos de dispositivo", http.StatusInternalServerError)
		return
	}
	patients, err := h.repo.ListPatients(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los pacientes", http.StatusInternalServerError)
		return
	}
	data := devicesViewData{Items: devices, Organizations: orgs, DeviceTypes: deviceTypes, Patients: patients}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Dispositivos"}}
	h.render(w, r, "superadmin/devices.html", "Dispositivos", data, crumbs)
}

func (h *Handlers) DevicesCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	serial := strings.TrimSpace(r.FormValue("serial"))
	if serial == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Serie obligatoria"})
		http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
		return
	}
	orgIDRaw := strings.TrimSpace(r.FormValue("org_id"))
	var orgID *string
	if orgIDRaw != "" {
		orgID = &orgIDRaw
	}
	brandRaw := strings.TrimSpace(r.FormValue("brand"))
	var brand *string
	if brandRaw != "" {
		brand = &brandRaw
	}
	modelRaw := strings.TrimSpace(r.FormValue("model"))
	var model *string
	if modelRaw != "" {
		model = &modelRaw
	}
	typeCode := strings.TrimSpace(r.FormValue("device_type"))
	if typeCode == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Tipo de dispositivo requerido"})
		http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
		return
	}
	ownerRaw := strings.TrimSpace(r.FormValue("owner_patient_id"))
	var owner *string
	if ownerRaw != "" {
		owner = &ownerRaw
	}
	activeVal := true
	if r.FormValue("active") == "" {
		activeVal = false
	}
	input := models.DeviceInput{OrgID: orgID, Serial: serial, Brand: brand, Model: model, DeviceTypeCode: typeCode, OwnerPatientID: owner, Active: &activeVal}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	device, err := h.repo.CreateDevice(ctx, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el dispositivo"})
		http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "DEVICE_CREATE", "device", &device.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Dispositivo creado"})
	http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
}

func (h *Handlers) DevicesUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	serial := strings.TrimSpace(r.FormValue("serial"))
	if serial == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Serie obligatoria"})
		http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
		return
	}
	orgIDRaw := strings.TrimSpace(r.FormValue("org_id"))
	var orgID *string
	if orgIDRaw != "" {
		orgID = &orgIDRaw
	}
	brandRaw := strings.TrimSpace(r.FormValue("brand"))
	var brand *string
	if brandRaw != "" {
		brand = &brandRaw
	}
	modelRaw := strings.TrimSpace(r.FormValue("model"))
	var model *string
	if modelRaw != "" {
		model = &modelRaw
	}
	typeCode := strings.TrimSpace(r.FormValue("device_type"))
	if typeCode == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Tipo de dispositivo requerido"})
		http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
		return
	}
	ownerRaw := strings.TrimSpace(r.FormValue("owner_patient_id"))
	var owner *string
	if ownerRaw != "" {
		owner = &ownerRaw
	}
	activeVal := false
	if r.FormValue("active") != "" {
		activeVal = true
	}
	input := models.DeviceInput{OrgID: orgID, Serial: serial, Brand: brand, Model: model, DeviceTypeCode: typeCode, OwnerPatientID: owner, Active: &activeVal}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	device, err := h.repo.UpdateDevice(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el dispositivo"})
		http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "DEVICE_UPDATE", "device", &device.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Dispositivo actualizado"})
	http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
}

func (h *Handlers) DevicesDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteDevice(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "DEVICE_DELETE", "device", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Dispositivo eliminado"})
	http.Redirect(w, r, "/superadmin/devices", http.StatusSeeOther)
}

// Signal streams

func (h *Handlers) SignalStreamsIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	streams, err := h.repo.ListSignalStreams(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los streams", http.StatusInternalServerError)
		return
	}
	patients, err := h.repo.ListPatients(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los pacientes", http.StatusInternalServerError)
		return
	}
	devices, err := h.repo.ListDevices(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los dispositivos", http.StatusInternalServerError)
		return
	}
	signalTypes, err := h.repo.ListCatalog(ctx, "signal_types", 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los tipos de señal", http.StatusInternalServerError)
		return
	}
	data := signalStreamsViewData{Items: streams, Patients: patients, Devices: devices, SignalTypes: signalTypes}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Streams de señal"}}
	h.render(w, r, "superadmin/signal_streams.html", "Streams de señal", data, crumbs)
}

func (h *Handlers) SignalStreamsCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	patientID := strings.TrimSpace(r.FormValue("patient_id"))
	deviceID := strings.TrimSpace(r.FormValue("device_id"))
	signalType := strings.TrimSpace(r.FormValue("signal_type"))
	startRaw := strings.TrimSpace(r.FormValue("started_at"))
	rateRaw := strings.TrimSpace(r.FormValue("sample_rate"))
	if patientID == "" || deviceID == "" || signalType == "" || startRaw == "" || rateRaw == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Todos los campos obligatorios"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	rate, err := strconv.ParseFloat(rateRaw, 64)
	if err != nil || rate <= 0 {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Frecuencia inválida"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	startedAtPtr, err := parseDateTimeLocal(startRaw)
	if err != nil || startedAtPtr == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de inicio inválida"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	endRaw := strings.TrimSpace(r.FormValue("ended_at"))
	var ended *time.Time
	if endRaw != "" {
		parsed, err := parseDateTimeLocal(endRaw)
		if err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de cierre inválida"})
			http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
			return
		}
		ended = parsed
	}
	input := models.SignalStreamInput{PatientID: patientID, DeviceID: deviceID, SignalType: signalType, SampleRateHz: rate, StartedAt: *startedAtPtr, EndedAt: ended}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	stream, err := h.repo.CreateSignalStream(ctx, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el stream"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "SIGNAL_STREAM_CREATE", "signal_stream", &stream.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Stream creado"})
	http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
}

func (h *Handlers) SignalStreamsUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	patientID := strings.TrimSpace(r.FormValue("patient_id"))
	deviceID := strings.TrimSpace(r.FormValue("device_id"))
	signalType := strings.TrimSpace(r.FormValue("signal_type"))
	startRaw := strings.TrimSpace(r.FormValue("started_at"))
	rateRaw := strings.TrimSpace(r.FormValue("sample_rate"))
	if patientID == "" || deviceID == "" || signalType == "" || startRaw == "" || rateRaw == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Todos los campos obligatorios"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	rate, err := strconv.ParseFloat(rateRaw, 64)
	if err != nil || rate <= 0 {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Frecuencia inválida"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	startedAtPtr, err := parseDateTimeLocal(startRaw)
	if err != nil || startedAtPtr == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de inicio inválida"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	endRaw := strings.TrimSpace(r.FormValue("ended_at"))
	var ended *time.Time
	if endRaw != "" {
		parsed, err := parseDateTimeLocal(endRaw)
		if err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de cierre inválida"})
			http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
			return
		}
		ended = parsed
	}
	input := models.SignalStreamInput{PatientID: patientID, DeviceID: deviceID, SignalType: signalType, SampleRateHz: rate, StartedAt: *startedAtPtr, EndedAt: ended}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	stream, err := h.repo.UpdateSignalStream(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el stream"})
		http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "SIGNAL_STREAM_UPDATE", "signal_stream", &stream.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Stream actualizado"})
	http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
}

func (h *Handlers) SignalStreamsDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteSignalStream(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "SIGNAL_STREAM_DELETE", "signal_stream", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Stream eliminado"})
	http.Redirect(w, r, "/superadmin/signal-streams", http.StatusSeeOther)
}

// Models

func (h *Handlers) ModelsIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	items, err := h.repo.ListModels(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los modelos", http.StatusInternalServerError)
		return
	}
	data := modelsViewData{Items: items}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Modelos ML"}}
	h.render(w, r, "superadmin/models.html", "Modelos ML", data, crumbs)
}

func (h *Handlers) ModelsCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	version := strings.TrimSpace(r.FormValue("version"))
	task := strings.TrimSpace(r.FormValue("task"))
	if name == "" || version == "" || task == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Nombre, versión y tarea son obligatorios"})
		http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
		return
	}
	trainingPtr := optionalString(r.FormValue("training_data_ref"))
	hyperPtr, err := optionalJSON(r.FormValue("hyperparams"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Hyperparámetros deben ser JSON válido"})
		http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
		return
	}
	input := models.MLModelInput{Name: name, Version: version, Task: task, TrainingDataRef: trainingPtr, Hyperparams: hyperPtr}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	model, err := h.repo.CreateModel(ctx, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el modelo"})
		http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "MODEL_CREATE", "ml_model", &model.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Modelo creado"})
	http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
}

func (h *Handlers) ModelsUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	name := strings.TrimSpace(r.FormValue("name"))
	version := strings.TrimSpace(r.FormValue("version"))
	task := strings.TrimSpace(r.FormValue("task"))
	if name == "" || version == "" || task == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Nombre, versión y tarea son obligatorios"})
		http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
		return
	}
	trainingPtr := optionalString(r.FormValue("training_data_ref"))
	hyperPtr, err := optionalJSON(r.FormValue("hyperparams"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Hyperparámetros deben ser JSON válido"})
		http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
		return
	}
	input := models.MLModelInput{Name: name, Version: version, Task: task, TrainingDataRef: trainingPtr, Hyperparams: hyperPtr}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	model, err := h.repo.UpdateModel(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el modelo"})
		http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "MODEL_UPDATE", "ml_model", &model.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Modelo actualizado"})
	http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
}

func (h *Handlers) ModelsDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteModel(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "MODEL_DELETE", "ml_model", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Modelo eliminado"})
	http.Redirect(w, r, "/superadmin/models", http.StatusSeeOther)
}

// Event types

func (h *Handlers) EventTypesIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	items, err := h.repo.ListEventTypes(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los tipos de evento", http.StatusInternalServerError)
		return
	}
	levels, err := h.repo.ListCatalog(ctx, "alert_levels", 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los niveles", http.StatusInternalServerError)
		return
	}
	data := eventTypesViewData{Items: items, Levels: levels}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Tipos de evento"}}
	h.render(w, r, "superadmin/event_types.html", "Tipos de evento", data, crumbs)
}

func (h *Handlers) EventTypesCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	code := strings.ToLower(strings.TrimSpace(r.FormValue("code")))
	severity := strings.TrimSpace(r.FormValue("severity_default"))
	if code == "" || severity == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Código y severidad son obligatorios"})
		http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
		return
	}
	desc := optionalString(r.FormValue("description"))
	input := models.EventTypeInput{Code: code, Description: desc, SeverityDefault: severity}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	etype, err := h.repo.CreateEventType(ctx, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear el tipo de evento"})
		http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "EVENT_TYPE_CREATE", "event_type", &etype.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Tipo de evento creado"})
	http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
}

func (h *Handlers) EventTypesUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	code := strings.ToLower(strings.TrimSpace(r.FormValue("code")))
	severity := strings.TrimSpace(r.FormValue("severity_default"))
	if code == "" || severity == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Código y severidad son obligatorios"})
		http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
		return
	}
	desc := optionalString(r.FormValue("description"))
	input := models.EventTypeInput{Code: code, Description: desc, SeverityDefault: severity}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	etype, err := h.repo.UpdateEventType(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar el tipo de evento"})
		http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "EVENT_TYPE_UPDATE", "event_type", &etype.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Tipo de evento actualizado"})
	http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
}

func (h *Handlers) EventTypesDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteEventType(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "EVENT_TYPE_DELETE", "event_type", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Tipo de evento eliminado"})
	http.Redirect(w, r, "/superadmin/event-types", http.StatusSeeOther)
}

// Inferences

func (h *Handlers) InferencesIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	items, err := h.repo.ListInferences(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las inferencias", http.StatusInternalServerError)
		return
	}
	modelsList, err := h.repo.ListModels(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los modelos", http.StatusInternalServerError)
		return
	}
	streams, err := h.repo.ListSignalStreams(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los streams", http.StatusInternalServerError)
		return
	}
	eventTypes, err := h.repo.ListEventTypes(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los tipos de evento", http.StatusInternalServerError)
		return
	}
	data := inferencesViewData{Items: items, Models: modelsList, Streams: streams, EventTypes: eventTypes}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Inferencias"}}
	h.render(w, r, "superadmin/inferences.html", "Inferencias", data, crumbs)
}

func (h *Handlers) InferencesCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	streamID := strings.TrimSpace(r.FormValue("stream_id"))
	eventCode := strings.TrimSpace(r.FormValue("event_code"))
	startRaw := strings.TrimSpace(r.FormValue("window_start"))
	endRaw := strings.TrimSpace(r.FormValue("window_end"))
	if streamID == "" || eventCode == "" || startRaw == "" || endRaw == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Stream, evento y ventanas son obligatorios"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	startPtr, err := parseDateTimeLocal(startRaw)
	if err != nil || startPtr == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha inicio inválida"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	endPtr, err := parseDateTimeLocal(endRaw)
	if err != nil || endPtr == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha fin inválida"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	if !endPtr.After(*startPtr) {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "La ventana debe tener fin posterior al inicio"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	modelID := optionalString(r.FormValue("model_id"))
	scorePtr, err := optionalFloat32(r.FormValue("score"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Score inválido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	thresholdPtr, err := optionalFloat32(r.FormValue("threshold"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Umbral inválido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	metadataPtr, err := optionalJSON(r.FormValue("metadata"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Metadata debe ser JSON válido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	featurePtr, err := optionalJSON(r.FormValue("feature_snapshot"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Snapshot debe ser JSON válido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	seriesPtr := optionalString(r.FormValue("series_ref"))
	input := models.InferenceInput{
		ModelID:         modelID,
		StreamID:        streamID,
		EventCode:       eventCode,
		WindowStart:     *startPtr,
		WindowEnd:       *endPtr,
		Score:           scorePtr,
		Threshold:       thresholdPtr,
		Metadata:        metadataPtr,
		SeriesRef:       seriesPtr,
		FeatureSnapshot: featurePtr,
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	inference, err := h.repo.CreateInference(ctx, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear la inferencia"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "INFERENCE_CREATE", "inference", &inference.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Inferencia creada"})
	http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
}

func (h *Handlers) InferencesUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	streamID := strings.TrimSpace(r.FormValue("stream_id"))
	eventCode := strings.TrimSpace(r.FormValue("event_code"))
	startRaw := strings.TrimSpace(r.FormValue("window_start"))
	endRaw := strings.TrimSpace(r.FormValue("window_end"))
	if streamID == "" || eventCode == "" || startRaw == "" || endRaw == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Stream, evento y ventanas son obligatorios"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	startPtr, err := parseDateTimeLocal(startRaw)
	if err != nil || startPtr == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha inicio inválida"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	endPtr, err := parseDateTimeLocal(endRaw)
	if err != nil || endPtr == nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha fin inválida"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	if !endPtr.After(*startPtr) {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "La ventana debe tener fin posterior al inicio"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	modelID := optionalString(r.FormValue("model_id"))
	scorePtr, err := optionalFloat32(r.FormValue("score"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Score inválido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	thresholdPtr, err := optionalFloat32(r.FormValue("threshold"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Umbral inválido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	metadataPtr, err := optionalJSON(r.FormValue("metadata"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Metadata debe ser JSON válido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	featurePtr, err := optionalJSON(r.FormValue("feature_snapshot"))
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Snapshot debe ser JSON válido"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	seriesPtr := optionalString(r.FormValue("series_ref"))
	input := models.InferenceInput{
		ModelID:         modelID,
		StreamID:        streamID,
		EventCode:       eventCode,
		WindowStart:     *startPtr,
		WindowEnd:       *endPtr,
		Score:           scorePtr,
		Threshold:       thresholdPtr,
		Metadata:        metadataPtr,
		SeriesRef:       seriesPtr,
		FeatureSnapshot: featurePtr,
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	inference, err := h.repo.UpdateInference(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar la inferencia"})
		http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "INFERENCE_UPDATE", "inference", &inference.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Inferencia actualizada"})
	http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
}

func (h *Handlers) InferencesDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteInference(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "INFERENCE_DELETE", "inference", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Inferencia eliminada"})
	http.Redirect(w, r, "/superadmin/inferences", http.StatusSeeOther)
}

// Alerts

func (h *Handlers) AlertsIndex(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()

	alerts, err := h.repo.ListAlerts(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las alertas", http.StatusInternalServerError)
		return
	}
	patients, err := h.repo.ListPatients(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los pacientes", http.StatusInternalServerError)
		return
	}
	alertTypes, err := h.repo.ListAlertTypes(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los tipos de alerta", http.StatusInternalServerError)
		return
	}
	statuses, err := h.repo.ListAlertStatuses(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los estatus", http.StatusInternalServerError)
		return
	}
	levels, err := h.repo.ListCatalog(ctx, "alert_levels", 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los niveles", http.StatusInternalServerError)
		return
	}
	modelsList, err := h.repo.ListModels(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar los modelos", http.StatusInternalServerError)
		return
	}
	inferences, err := h.repo.ListInferences(ctx, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las inferencias", http.StatusInternalServerError)
		return
	}
	data := alertsViewData{
		Items:         alerts,
		Patients:      patients,
		AlertTypes:    alertTypes,
		AlertStatuses: statuses,
		AlertLevels:   levels,
		Models:        modelsList,
		Inferences:    inferences,
	}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Alertas"}}
	h.render(w, r, "superadmin/alerts.html", "Alertas", data, crumbs)
}

func (h *Handlers) AlertsCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	patientID := strings.TrimSpace(r.FormValue("patient_id"))
	alertType := strings.TrimSpace(r.FormValue("alert_type"))
	alertLevel := strings.TrimSpace(r.FormValue("alert_level"))
	status := strings.TrimSpace(r.FormValue("status"))
	if patientID == "" || alertType == "" || alertLevel == "" || status == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Paciente, tipo, nivel y estatus son obligatorios"})
		http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
		return
	}
	modelID := optionalString(r.FormValue("model_id"))
	inferenceID := optionalString(r.FormValue("inference_id"))
	description := optionalString(r.FormValue("description"))
	location := optionalString(r.FormValue("location_wkt"))
	input := models.AlertInput{
		PatientID:   patientID,
		AlertType:   alertType,
		AlertLevel:  alertLevel,
		Status:      status,
		ModelID:     modelID,
		InferenceID: inferenceID,
		Description: description,
		LocationWKT: location,
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	alert, err := h.repo.CreateAlert(ctx, patientID, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear la alerta"})
		http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "ALERT_CREATE", "alert", &alert.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Alerta creada"})
	http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
}

func (h *Handlers) AlertsUpdate(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	alertType := strings.TrimSpace(r.FormValue("alert_type"))
	alertLevel := strings.TrimSpace(r.FormValue("alert_level"))
	status := strings.TrimSpace(r.FormValue("status"))
	if alertType == "" || alertLevel == "" || status == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Tipo, nivel y estatus son obligatorios"})
		http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
		return
	}
	modelID := optionalString(r.FormValue("model_id"))
	inferenceID := optionalString(r.FormValue("inference_id"))
	description := optionalString(r.FormValue("description"))
	location := optionalString(r.FormValue("location_wkt"))
	input := models.AlertInput{
		AlertType:   alertType,
		AlertLevel:  alertLevel,
		Status:      status,
		ModelID:     modelID,
		InferenceID: inferenceID,
		Description: description,
		LocationWKT: location,
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	alert, err := h.repo.UpdateAlert(ctx, id, input)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar la alerta"})
		http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "ALERT_UPDATE", "alert", &alert.ID, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Alerta actualizada"})
	http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
}

func (h *Handlers) AlertsDelete(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.DeleteAlert(ctx, id); err != nil {
		http.Error(w, "No se pudo eliminar", http.StatusInternalServerError)
		return
	}
	h.writeAudit(ctx, r, "ALERT_DELETE", "alert", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Alerta eliminada"})
	http.Redirect(w, r, "/superadmin/alerts", http.StatusSeeOther)
}

func (h *Handlers) APIKeysIndex(w http.ResponseWriter, r *http.Request) {
	showAll := strings.EqualFold(strings.TrimSpace(r.URL.Query().Get("show")), "all")
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	keys, err := h.repo.ListAPIKeys(ctx, !showAll, 200, 0)
	if err != nil {
		http.Error(w, "No se pudieron cargar las API Keys", http.StatusInternalServerError)
		return
	}
	perms, err := h.repo.ListPermissions(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar los permisos", http.StatusInternalServerError)
		return
	}
	data := apiKeysViewData{Keys: keys, Permissions: perms, ShowInactive: showAll}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "API Keys"}}
	h.render(w, r, "superadmin/api_keys.html", "API Keys", data, crumbs)
}

func (h *Handlers) APIKeysCreate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	label := strings.TrimSpace(r.FormValue("label"))
	if label == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "El nombre es obligatorio"})
		http.Redirect(w, r, "/superadmin/api-keys", http.StatusSeeOther)
		return
	}
	owner := strings.TrimSpace(r.FormValue("owner_user_id"))
	var ownerPtr *string
	if owner != "" {
		ownerPtr = &owner
	}
	expiresStr := strings.TrimSpace(r.FormValue("expires_at"))
	var expiresAt *time.Time
	if expiresStr != "" {
		if t, err := time.ParseInLocation("2006-01-02T15:04", expiresStr, time.Local); err == nil {
			utc := t.In(time.UTC)
			expiresAt = &utc
		} else {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Fecha de expiración inválida"})
			http.Redirect(w, r, "/superadmin/api-keys", http.StatusSeeOther)
			return
		}
	}
	secret, err := generateAPIKeySecret()
	if err != nil {
		http.Error(w, "No se pudo generar el secreto", http.StatusInternalServerError)
		return
	}
	hash := sha256.Sum256([]byte(secret))
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	id, err := h.repo.CreateAPIKey(ctx, label, expiresAt, hex.EncodeToString(hash[:]), ownerPtr)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo crear la API Key"})
		http.Redirect(w, r, "/superadmin/api-keys", http.StatusSeeOther)
		return
	}
	perms := r.Form["permissions"]
	if len(perms) > 0 {
		if err := h.repo.SetAPIKeyPermissions(ctx, id, perms); err != nil {
			h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "La API Key se creó, pero no se pudieron asignar los permisos"})
		}
	}
	h.writeAudit(ctx, r, "APIKEY_CREATE", "api_key", &id, map[string]any{"label": label})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "API Key creada. Guarda el secreto: " + secret})
	http.Redirect(w, r, "/superadmin/api-keys", http.StatusSeeOther)
}

func (h *Handlers) APIKeysUpdatePermissions(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	perms := r.Form["permissions"]
	redirect := strings.TrimSpace(r.FormValue("redirect"))
	if redirect == "" || !strings.HasPrefix(redirect, "/") {
		redirect = "/superadmin/api-keys"
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.SetAPIKeyPermissions(ctx, id, perms); err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudieron actualizar los permisos"})
		http.Redirect(w, r, redirect, http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "APIKEY_SET_PERMS", "api_key", &id, map[string]any{"count": len(perms)})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Permisos actualizados"})
	http.Redirect(w, r, redirect, http.StatusSeeOther)
}

func (h *Handlers) APIKeysRevoke(w http.ResponseWriter, r *http.Request) {
	id := chi.URLParam(r, "id")
	if err := r.ParseForm(); err != nil && err != http.ErrNotMultipart {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	redirect := strings.TrimSpace(r.FormValue("redirect"))
	if redirect == "" || !strings.HasPrefix(redirect, "/") {
		redirect = "/superadmin/api-keys"
	}
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	if err := h.repo.RevokeAPIKey(ctx, id); err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo revocar la API Key"})
		http.Redirect(w, r, redirect, http.StatusSeeOther)
		return
	}
	h.writeAudit(ctx, r, "APIKEY_REVOKE", "api_key", &id, nil)
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "API Key revocada"})
	http.Redirect(w, r, redirect, http.StatusSeeOther)
}

func (h *Handlers) SystemSettingsForm(w http.ResponseWriter, r *http.Request) {
	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	settings, err := h.repo.GetSystemSettings(ctx)
	if err != nil {
		http.Error(w, "No se pudieron cargar las configuraciones", http.StatusInternalServerError)
		return
	}
	if settings == nil {
		settings = &models.SystemSettings{}
	}
	data := systemSettingsViewData{Settings: settings}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Configuración"}}
	h.render(w, r, "superadmin/settings.html", "Configuración del sistema", data, crumbs)
}

func (h *Handlers) SystemSettingsUpdate(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		http.Error(w, "formulario inválido", http.StatusBadRequest)
		return
	}
	input := models.SystemSettingsInput{
		BrandName:       strings.TrimSpace(r.FormValue("brand_name")),
		SupportEmail:    strings.TrimSpace(r.FormValue("support_email")),
		PrimaryColor:    strings.TrimSpace(r.FormValue("primary_color")),
		DefaultLocale:   strings.TrimSpace(r.FormValue("default_locale")),
		DefaultTimezone: strings.TrimSpace(r.FormValue("default_timezone")),
		MaintenanceMode: r.FormValue("maintenance_mode") != "",
	}
	if input.BrandName == "" || input.SupportEmail == "" || input.PrimaryColor == "" || input.DefaultLocale == "" || input.DefaultTimezone == "" {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "Marca, correo, colores y zona horaria son obligatorios"})
		http.Redirect(w, r, "/superadmin/settings/system", http.StatusSeeOther)
		return
	}
	if sec := strings.TrimSpace(r.FormValue("secondary_color")); sec != "" {
		upper := strings.ToUpper(sec)
		input.SecondaryColor = &upper
	}
	if logo := strings.TrimSpace(r.FormValue("logo_url")); logo != "" {
		input.LogoURL = &logo
	}
	if phone := strings.TrimSpace(r.FormValue("contact_phone")); phone != "" {
		input.ContactPhone = &phone
	}
	if msg := strings.TrimSpace(r.FormValue("maintenance_message")); msg != "" {
		input.MaintenanceMessage = &msg
	}
	input.PrimaryColor = strings.ToUpper(input.PrimaryColor)

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	actor := middleware.UserIDFromContext(r.Context())
	var actorPtr *string
	if actor != "" {
		actorPtr = &actor
	}
	updated, err := h.repo.UpdateSystemSettings(ctx, input, actorPtr)
	if err != nil {
		h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "error", Message: "No se pudo actualizar la configuración"})
		http.Redirect(w, r, "/superadmin/settings/system", http.StatusSeeOther)
		return
	}
	entity := "system_settings"
	entityID := "singleton"
	h.writeAudit(ctx, r, "SYSTEM_SETTINGS_UPDATE", entity, &entityID, map[string]any{"brand_name": updated.BrandName, "maintenance_mode": updated.MaintenanceMode})
	h.sessions.PushFlash(r.Context(), middleware.SessionJTIFromContext(r.Context()), session.Flash{Type: "success", Message: "Configuración actualizada"})
	http.Redirect(w, r, "/superadmin/settings/system", http.StatusSeeOther)
}

func (h *Handlers) AuditIndex(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	fromStr := strings.TrimSpace(q.Get("from"))
	toStr := strings.TrimSpace(q.Get("to"))
	action := strings.TrimSpace(q.Get("action"))

	var fromTime *time.Time
	if fromStr != "" {
		if t, err := time.ParseInLocation("2006-01-02", fromStr, time.Local); err == nil {
			tt := t.In(time.UTC)
			fromTime = &tt
		}
	}
	var toTime *time.Time
	if toStr != "" {
		if t, err := time.ParseInLocation("2006-01-02", toStr, time.Local); err == nil {
			end := t.Add(24 * time.Hour).Add(-time.Nanosecond).In(time.UTC)
			toTime = &end
		}
	}
	var actionPtr *string
	if action != "" {
		actionPtr = &action
	}

	ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
	defer cancel()
	logs, err := h.repo.ListAudit(ctx, fromTime, toTime, actionPtr, 200, 0)
	if err != nil {
		http.Error(w, "No se pudo cargar la auditoría", http.StatusInternalServerError)
		return
	}
	items := make([]auditLogItem, 0, len(logs))
	for _, log := range logs {
		items = append(items, auditLogItem{Log: log, ActionLabel: operationLabel(log.Action)})
	}
	data := auditViewData{
		From:    fromStr,
		To:      toStr,
		Action:  action,
		Logs:    items,
		Actions: auditActionOptions(),
	}
	crumbs := []ui.Breadcrumb{{Label: "Panel", URL: "/superadmin/dashboard"}, {Label: "Auditoría"}}
	h.render(w, r, "superadmin/audit.html", "Auditoría", data, crumbs)
}
