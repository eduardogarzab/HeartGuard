package superadmin

import (
	"context"
	"errors"
	"fmt"
	"testing"
	"time"

	"heartguard-superadmin/internal/models"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

type stubPool struct {
	queryRow func(ctx context.Context, sql string, args ...any) pgx.Row
	query    func(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

func (s *stubPool) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	if s.query != nil {
		return s.query(ctx, sql, args...)
	}
	return nil, errors.New("unexpected query call")
}

func (s *stubPool) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	if s.queryRow != nil {
		return s.queryRow(ctx, sql, args...)
	}
	return mockRow{err: errors.New("unexpected queryrow call")}
}

func (s *stubPool) Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error) {
	return pgconn.CommandTag{}, errors.New("unexpected exec call")
}

func (s *stubPool) Begin(ctx context.Context) (pgx.Tx, error) {
	return nil, errors.New("unexpected begin call")
}

func (s *stubPool) Ping(ctx context.Context) error { return nil }

type mockRow struct {
	values []any
	err    error
}

func (r mockRow) Scan(dest ...any) error {
	if r.err != nil {
		return r.err
	}
	if len(dest) != len(r.values) {
		return fmt.Errorf("unexpected dest count: %d", len(dest))
	}
	for i := range dest {
		switch d := dest[i].(type) {
		case *string:
			if v, ok := r.values[i].(string); ok {
				*d = v
				continue
			}
			return fmt.Errorf("expected string at %d", i)
		case *time.Time:
			if v, ok := r.values[i].(time.Time); ok {
				*d = v
				continue
			}
			return fmt.Errorf("expected time at %d", i)
		case *bool:
			if v, ok := r.values[i].(bool); ok {
				*d = v
				continue
			}
			return fmt.Errorf("expected bool at %d", i)
		default:
			return fmt.Errorf("unsupported dest type %T", dest[i])
		}
	}
	return nil
}

type mockRows struct {
	data [][]any
	idx  int
	err  error
}

func (m *mockRows) Next() bool {
	if m.idx < len(m.data) {
		m.idx++
		return true
	}
	return false
}

func (m *mockRows) Scan(dest ...any) error {
	if m.idx == 0 || m.idx > len(m.data) {
		return errors.New("no row")
	}
	row := mockRow{values: m.data[m.idx-1]}
	return row.Scan(dest...)
}

func (m *mockRows) Err() error { return m.err }

func (m *mockRows) Close() {}

func (m *mockRows) FieldDescriptions() []pgconn.FieldDescription { return nil }

func (m *mockRows) Values() ([]any, error) { return nil, errors.New("not implemented") }

func (m *mockRows) RawValues() [][]byte { return nil }

func (m *mockRows) CommandTag() pgconn.CommandTag { return pgconn.CommandTag{} }

func (m *mockRows) Conn() *pgx.Conn { return nil }

func TestRepoCreatePushDevice(t *testing.T) {
	active := true
	now := time.Now()
	pool := &stubPool{}
	pool.queryRow = func(ctx context.Context, sql string, args ...any) pgx.Row {
		return mockRow{values: []any{"pd-1", "user-1", "Alice", "alice@example.com", "ios", "iOS", "tok-123", now, true}}
	}
	repo := NewRepoWithPool(pool, nil)
	input := models.PushDeviceInput{UserID: "user-1", PlatformCode: "ios", PushToken: "tok-123", LastSeenAt: &now, Active: &active}
	device, err := repo.CreatePushDevice(context.Background(), input)
	if err != nil {
		t.Fatalf("CreatePushDevice: %v", err)
	}
	if device.PlatformLabel != "iOS" || device.UserEmail != "alice@example.com" {
		t.Fatalf("unexpected device: %#v", device)
	}
}

func TestRepoCreatePushDeviceInvalidPlatform(t *testing.T) {
	active := true
	now := time.Now()
	calls := 0
	pool := &stubPool{}
	pool.queryRow = func(ctx context.Context, sql string, args ...any) pgx.Row {
		calls++
		if calls == 1 {
			return mockRow{err: pgx.ErrNoRows}
		}
		return mockRow{values: []any{false}}
	}
	repo := NewRepoWithPool(pool, nil)
	input := models.PushDeviceInput{UserID: "user-1", PlatformCode: "bad", PushToken: "tok-123", LastSeenAt: &now, Active: &active}
	if _, err := repo.CreatePushDevice(context.Background(), input); !errors.Is(err, errInvalidPlatform) {
		t.Fatalf("expected errInvalidPlatform, got %v", err)
	}
	if calls != 2 {
		t.Fatalf("expected 2 QueryRow calls, got %d", calls)
	}
}

func TestRepoUpdatePushDeviceInvalidPlatform(t *testing.T) {
	active := false
	now := time.Now()
	calls := 0
	pool := &stubPool{}
	pool.queryRow = func(ctx context.Context, sql string, args ...any) pgx.Row {
		calls++
		if calls == 1 {
			return mockRow{err: pgx.ErrNoRows}
		}
		return mockRow{values: []any{false}}
	}
	repo := NewRepoWithPool(pool, nil)
	input := models.PushDeviceInput{UserID: "user-1", PlatformCode: "bad", PushToken: "tok-456", LastSeenAt: &now, Active: &active}
	if _, err := repo.UpdatePushDevice(context.Background(), "pd-1", input); !errors.Is(err, errInvalidPlatform) {
		t.Fatalf("expected errInvalidPlatform, got %v", err)
	}
	if calls != 2 {
		t.Fatalf("expected 2 QueryRow calls, got %d", calls)
	}
}

func TestRepoListPushDevices(t *testing.T) {
	now := time.Now()
	pool := &stubPool{}
	pool.query = func(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
		expected := []any{"user-1", "ios", 10, 0}
		if len(args) != len(expected) {
			t.Fatalf("unexpected args len %d", len(args))
		}
		for i := range expected {
			if args[i] != expected[i] {
				t.Fatalf("unexpected arg %d: %v", i, args[i])
			}
		}
		rows := &mockRows{data: [][]any{{"pd-1", "user-1", "Alice", "alice@example.com", "ios", "iOS", "tok-123", now, true}}}
		return rows, nil
	}
	repo := NewRepoWithPool(pool, nil)
	userID := "user-1"
	platform := "ios"
	devices, err := repo.ListPushDevices(context.Background(), &userID, &platform, 10, 0)
	if err != nil {
		t.Fatalf("ListPushDevices: %v", err)
	}
	if len(devices) != 1 || devices[0].ID != "pd-1" {
		t.Fatalf("unexpected devices: %#v", devices)
	}
}
