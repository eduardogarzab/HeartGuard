package superadmin

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"go.uber.org/zap"
	"heartguard-superadmin/internal/models"
)

type handlersStubRepo struct {
	catalogDefs []models.CatalogDefinition
	catalogItem *models.CatalogItem
	catalogErr  error
	overview    *models.MetricsOverview
	recent      []models.ActivityEntry
	metricsErr  error
	recentErr   error
}

func (s *handlersStubRepo) AuditPool() *pgxpool.Pool   { return nil }
func (s *handlersStubRepo) Ping(context.Context) error { return nil }
func (s *handlersStubRepo) CreateOrganization(context.Context, string, string) (*models.Organization, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) ListOrganizations(context.Context, int, int) ([]models.Organization, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) GetOrganization(context.Context, string) (*models.Organization, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) UpdateOrganization(context.Context, string, *string, *string) (*models.Organization, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) DeleteOrganization(context.Context, string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) CreateInvitation(context.Context, string, string, *string, time.Duration, *string) (*models.OrgInvitation, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) ListInvitations(context.Context, *string, *string, int, int) ([]models.OrgInvitation, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) ConsumeInvitation(context.Context, string, string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) CancelInvitation(context.Context, string) error { panic("not implemented") }
func (s *handlersStubRepo) AddMember(context.Context, string, string, string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) RemoveMember(context.Context, string, string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) ListMembers(context.Context, string, int, int) ([]models.Membership, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) CatalogDefinitions() []models.CatalogDefinition { return s.catalogDefs }
func (s *handlersStubRepo) GetCatalogDefinition(slug string) (models.CatalogDefinition, bool) {
	for _, d := range s.catalogDefs {
		if d.Slug == slug {
			return d, true
		}
	}
	return models.CatalogDefinition{}, false
}
func (s *handlersStubRepo) ListCatalogItems(context.Context, string, int, int) ([]models.CatalogItem, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) CreateCatalogItem(ctx context.Context, slug, code, label string, weight *int) (*models.CatalogItem, error) {
	if s.catalogErr != nil {
		return nil, s.catalogErr
	}
	s.catalogItem = &models.CatalogItem{ID: "item-1", Code: code, Label: label, Weight: weight}
	return s.catalogItem, nil
}
func (s *handlersStubRepo) UpdateCatalogItem(ctx context.Context, slug, id string, code, label *string, weight *int) (*models.CatalogItem, error) {
	if s.catalogErr != nil {
		return nil, s.catalogErr
	}
	return &models.CatalogItem{ID: id, Code: getOrDefault(code, "updated"), Label: getOrDefault(label, "label"), Weight: weight}, nil
}
func (s *handlersStubRepo) DeleteCatalogItem(context.Context, string, string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) MetricsOverview(context.Context, int) (*models.MetricsOverview, error) {
	if s.metricsErr != nil {
		return nil, s.metricsErr
	}
	return s.overview, nil
}
func (s *handlersStubRepo) RecentActivity(context.Context, int) ([]models.ActivityEntry, error) {
	if s.recentErr != nil {
		return nil, s.recentErr
	}
	return s.recent, nil
}
func (s *handlersStubRepo) SearchUsers(context.Context, string, int, int) ([]models.User, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) UpdateUserStatus(context.Context, string, string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) CreateAPIKey(context.Context, string, *time.Time, string, *string) (string, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) SetAPIKeyPermissions(context.Context, string, []string) error {
	panic("not implemented")
}
func (s *handlersStubRepo) RevokeAPIKey(context.Context, string) error { panic("not implemented") }
func (s *handlersStubRepo) ListAPIKeys(context.Context, bool, int, int) ([]models.APIKey, error) {
	panic("not implemented")
}
func (s *handlersStubRepo) ListAudit(context.Context, *time.Time, *time.Time, *string, int, int) ([]models.AuditLog, error) {
	panic("not implemented")
}

func getOrDefault(v *string, def string) string {
	if v != nil {
		return *v
	}
	return def
}

func newHandlerWithRepo(repo Repository) *Handlers {
	return NewHandlers(repo, zap.NewNop())
}

func TestCreateCatalogItemRequiresWeight(t *testing.T) {
	repo := &handlersStubRepo{catalogDefs: []models.CatalogDefinition{{Slug: "alert_levels", Label: "Alert Levels", HasWeight: true}}}
	h := newHandlerWithRepo(repo)

	body := bytes.NewBufferString(`{"code":"HIGH","label":"High"}`)
	req := httptest.NewRequest(http.MethodPost, "/v1/superadmin/catalogs/alert_levels", body)
	rr := httptest.NewRecorder()

	h.CreateCatalogItem(rr, req)

	if rr.Code != http.StatusUnprocessableEntity {
		t.Fatalf("expected 422, got %d", rr.Code)
	}
}

func TestCreateCatalogItemSuccess(t *testing.T) {
	repo := &handlersStubRepo{catalogDefs: []models.CatalogDefinition{{Slug: "alert_levels", Label: "Alert Levels", HasWeight: true}}}
	h := newHandlerWithRepo(repo)

	body := bytes.NewBufferString(`{"code":"LOW","label":"Low","weight":1}`)
	req := httptest.NewRequest(http.MethodPost, "/v1/superadmin/catalogs/alert_levels", body)
	rr := httptest.NewRecorder()

	h.CreateCatalogItem(rr, req)

	if rr.Code != http.StatusCreated {
		t.Fatalf("expected 201, got %d", rr.Code)
	}

	var item models.CatalogItem
	if err := json.NewDecoder(rr.Body).Decode(&item); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if item.Code != "LOW" || item.Weight == nil || *item.Weight != 1 {
		t.Fatalf("unexpected payload: %+v", item)
	}
}

func TestMetricsOverviewHandler(t *testing.T) {
	repo := &handlersStubRepo{
		overview: &models.MetricsOverview{AverageResponseMS: 12.5, OperationCounts: []models.OperationCount{{Action: "ORG_CREATE", Count: 2}}, ActiveUsers: 3, ActiveOrganizations: 1},
		recent:   []models.ActivityEntry{{Action: "ORG_CREATE", TS: time.Unix(100, 0)}},
	}
	h := newHandlerWithRepo(repo)

	req := httptest.NewRequest(http.MethodGet, "/v1/superadmin/metrics/overview?window_minutes=60&recent_limit=5", nil)
	rr := httptest.NewRecorder()

	h.MetricsOverview(rr, req)

	if rr.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d", rr.Code)
	}

	var resp models.MetricsOverview
	if err := json.NewDecoder(rr.Body).Decode(&resp); err != nil {
		t.Fatalf("decode response: %v", err)
	}
	if len(resp.RecentActivity) != 1 || resp.OperationCounts[0].Action != "ORG_CREATE" {
		t.Fatalf("unexpected response: %+v", resp)
	}
}
