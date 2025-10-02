package superadmin

import (
	"context"
	"database/sql"
	"errors"
	"reflect"
	"testing"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"heartguard-superadmin/internal/models"
)

type fakeRows struct {
	data [][]any
	idx  int
	err  error
}

func (r *fakeRows) Close()                                       { r.idx = len(r.data) }
func (r *fakeRows) Err() error                                   { return r.err }
func (r *fakeRows) CommandTag() pgconn.CommandTag                { return pgconn.CommandTag{} }
func (r *fakeRows) FieldDescriptions() []pgconn.FieldDescription { return nil }
func (r *fakeRows) Next() bool {
	if r.idx >= len(r.data) {
		return false
	}
	r.idx++
	return true
}

func assignValue(dest reflect.Value, val any) {
	if dest.Kind() != reflect.Pointer {
		return
	}
	elem := dest.Elem()
	if !elem.CanSet() {
		return
	}
	if elem.Kind() == reflect.Pointer {
		if val == nil {
			elem.Set(reflect.Zero(elem.Type()))
			return
		}
		v := reflect.New(elem.Type().Elem())
		assignValue(v, val)
		elem.Set(v)
		return
	}
	if val == nil {
		elem.Set(reflect.Zero(elem.Type()))
		return
	}
	vv := reflect.ValueOf(val)
	if !vv.Type().AssignableTo(elem.Type()) {
		if vv.Type().ConvertibleTo(elem.Type()) {
			vv = vv.Convert(elem.Type())
		} else {
			panic("unsupported type assignment")
		}
	}
	elem.Set(vv)
}

func (r *fakeRows) Scan(dest ...any) error {
	if r.idx == 0 || r.idx > len(r.data) {
		return errors.New("invalid scan state")
	}
	row := r.data[r.idx-1]
	for i, d := range dest {
		if d == nil {
			continue
		}
		assignValue(reflect.ValueOf(d), row[i])
	}
	return nil
}

func (r *fakeRows) Values() ([]any, error) { return nil, nil }
func (r *fakeRows) RawValues() [][]byte    { return nil }
func (r *fakeRows) Conn() *pgx.Conn        { return nil }

type fakeRow struct {
	values []any
	err    error
}

func (r *fakeRow) Scan(dest ...any) error {
	if r.err != nil {
		return r.err
	}
	for i, d := range dest {
		if d == nil {
			continue
		}
		if i < len(r.values) {
			assignValue(reflect.ValueOf(d), r.values[i])
		}
	}
	return nil
}

type stubPool struct {
	rows      pgx.Rows
	queryErr  error
	execErr   error
	execTag   pgconn.CommandTag
	execArgs  []any
	queryArgs []any
	rowValues []any
	rowErr    error
}

func (s *stubPool) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	s.queryArgs = args
	return s.rows, s.queryErr
}

func (s *stubPool) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	s.queryArgs = args
	return &fakeRow{values: s.rowValues, err: s.rowErr}
}

func (s *stubPool) Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error) {
	s.execArgs = args
	return s.execTag, s.execErr
}

func (s *stubPool) Begin(ctx context.Context) (pgx.Tx, error) {
	return nil, errors.New("not implemented")
}
func (s *stubPool) Ping(ctx context.Context) error { return nil }

func TestListInvitations(t *testing.T) {
	fixed := time.Date(2024, 5, 15, 10, 0, 0, 0, time.UTC)
	origNow := nowFn
	nowFn = func() time.Time { return fixed }
	t.Cleanup(func() { nowFn = origNow })

	rows := &fakeRows{data: [][]any{
		{"inv-1", "org-1", "demo@heartguard.com", "role-1", "org_admin", "tok1", fixed.Add(2 * time.Hour), nil, nil, nil, fixed.Add(-time.Hour)},
		{"inv-2", "org-1", nil, "role-1", "org_admin", "tok2", fixed.Add(-time.Hour), fixed.Add(-30 * time.Minute), nil, nil, fixed.Add(-2 * time.Hour)},
		{"inv-3", "org-1", "user@example.com", "role-1", "org_admin", "tok3", fixed.Add(2 * time.Hour), nil, fixed.Add(-10 * time.Minute), nil, fixed.Add(-3 * time.Hour)},
	}}
	stub := &stubPool{rows: rows}
	repo := NewRepoWithPool(stub)

	orgID := "org-1"
	res, err := repo.ListInvitations(context.Background(), &orgID, nil, 25, 0)
	if err != nil {
		t.Fatalf("ListInvitations: %v", err)
	}
	if len(res) != 3 {
		t.Fatalf("expected 3 rows, got %d", len(res))
	}
	if res[0].Status != "pending" || res[1].Status != "used" || res[2].Status != "revoked" {
		t.Fatalf("unexpected statuses: %+v", res)
	}
}

func TestCancelInvitation(t *testing.T) {
	stub := &stubPool{rowValues: []any{true}}
	repo := NewRepoWithPool(stub)
	if err := repo.CancelInvitation(context.Background(), "inv-ok"); err != nil {
		t.Fatalf("cancel ok: %v", err)
	}
	if len(stub.queryArgs) != 1 || stub.queryArgs[0] != "inv-ok" {
		t.Fatalf("unexpected query args: %+v", stub.queryArgs)
	}

	stubFail := &stubPool{rowValues: []any{false}}
	repoFail := NewRepoWithPool(stubFail)
	if err := repoFail.CancelInvitation(context.Background(), "inv-missing"); err == nil {
		t.Fatalf("expected error for missing invitation")
	}
}

func TestListMembers(t *testing.T) {
	joined := time.Date(2024, 5, 15, 9, 0, 0, 0, time.UTC)
	rows := &fakeRows{data: [][]any{{"org-1", "user-1", "demo@heartguard.com", "Demo User", "role-1", "org_admin", "Org Admin", joined}}}
	stub := &stubPool{rows: rows}
	repo := NewRepoWithPool(stub)

	res, err := repo.ListMembers(context.Background(), "org-1", 10, 0)
	if err != nil {
		t.Fatalf("ListMembers: %v", err)
	}
	if len(res) != 1 {
		t.Fatalf("expected 1 member, got %d", len(res))
	}
	if res[0].UserID != "user-1" || res[0].OrgRoleCode != "org_admin" {
		t.Fatalf("unexpected payload: %+v", res[0])
	}
}

func TestCatalogDefinitions(t *testing.T) {
	repo := NewRepoWithPool(&stubPool{})
	defs := repo.CatalogDefinitions()
	if len(defs) == 0 {
		t.Fatalf("expected catalog definitions")
	}
	found := false
	for _, d := range defs {
		if d.Slug == "alert_levels" && d.HasWeight {
			found = true
		}
	}
	if !found {
		t.Fatalf("expected alert_levels definition in %+v", defs)
	}
}

func TestMetricsOverview(t *testing.T) {
	jsonOps := []byte(`[{"action":"ORG_CREATE","count":2}]`)
	stub := &stubPool{rowValues: []any{sql.NullFloat64{Float64: 42.5, Valid: true}, jsonOps, 5, 3, 2, 20, 7}}
	repo := NewRepoWithPool(stub)

	overview, err := repo.MetricsOverview(context.Background(), 60)
	if err != nil {
		t.Fatalf("MetricsOverview: %v", err)
	}
	if overview.AverageResponseMS != 42.5 {
		t.Fatalf("unexpected avg response: %v", overview.AverageResponseMS)
	}
	if len(overview.OperationCounts) != 1 || overview.OperationCounts[0].Action != "ORG_CREATE" {
		t.Fatalf("unexpected operation counts: %+v", overview.OperationCounts)
	}
	if overview.ActiveUsers != 5 || overview.PendingInvitations != 2 {
		t.Fatalf("unexpected counters: %+v", overview)
	}
}

func TestRecentActivity(t *testing.T) {
	uid := uuid.New()
	rows := &fakeRows{data: [][]any{{time.Unix(100, 0), "ACTION", "entity", uid}}}
	stub := &stubPool{rows: rows}
	repo := NewRepoWithPool(stub)

	res, err := repo.RecentActivity(context.Background(), 5)
	if err != nil {
		t.Fatalf("RecentActivity: %v", err)
	}
	if len(res) != 1 {
		t.Fatalf("expected 1 entry")
	}
	if res[0].UserID == nil || *res[0].UserID != uid.String() {
		t.Fatalf("unexpected user id: %+v", res[0])
	}
}

func TestInvitationStatusHelper(t *testing.T) {
	now := time.Unix(1000, 0)
	inv := &models.OrgInvitation{ExpiresAt: now.Add(time.Hour)}
	if s := invitationStatus(inv, now); s != "pending" {
		t.Fatalf("expected pending, got %s", s)
	}
	inv.UsedAt = &now
	if s := invitationStatus(inv, now); s != "used" {
		t.Fatalf("expected used, got %s", s)
	}
	inv.UsedAt = nil
	inv.RevokedAt = &now
	if s := invitationStatus(inv, now); s != "revoked" {
		t.Fatalf("expected revoked, got %s", s)
	}
}
