package superadmin

import (
	"context"
	"errors"
	"reflect"
	"testing"
	"time"

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

type stubPool struct {
	rows      pgx.Rows
	queryErr  error
	execErr   error
	execTag   pgconn.CommandTag
	execArgs  []any
	queryArgs []any
}

func (s *stubPool) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	s.queryArgs = args
	return s.rows, s.queryErr
}

func (s *stubPool) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	s.queryArgs = args
	return nil
}

func (s *stubPool) Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error) {
	s.execArgs = args
	return s.execTag, s.execErr
}

func (s *stubPool) Begin(ctx context.Context) (pgx.Tx, error) {
	return nil, errors.New("not implemented")
}
func (s *stubPool) Ping(ctx context.Context) error { return nil }

func TestListOrgInvitations(t *testing.T) {
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

	res, err := repo.ListOrgInvitations(context.Background(), "org-1", 25, 0)
	if err != nil {
		t.Fatalf("ListOrgInvitations: %v", err)
	}
	if len(res) != 3 {
		t.Fatalf("expected 3 rows, got %d", len(res))
	}
	if res[0].Status != "pending" || res[1].Status != "used" || res[2].Status != "revoked" {
		t.Fatalf("unexpected statuses: %+v", res)
	}
}

func TestCancelInvitation(t *testing.T) {
	stub := &stubPool{execTag: pgconn.CommandTag("UPDATE 1")}
	repo := NewRepoWithPool(stub)
	if err := repo.CancelInvitation(context.Background(), "inv-ok"); err != nil {
		t.Fatalf("cancel ok: %v", err)
	}
	if len(stub.execArgs) != 1 || stub.execArgs[0] != "inv-ok" {
		t.Fatalf("unexpected exec args: %+v", stub.execArgs)
	}

	stubFail := &stubPool{execTag: pgconn.CommandTag("UPDATE 0")}
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
