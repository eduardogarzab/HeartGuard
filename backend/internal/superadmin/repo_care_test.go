package superadmin

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
)

type fakePool struct {
	queryFn func(ctx context.Context, sql string, args ...any) (pgx.Rows, error)
}

func (f *fakePool) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	if f.queryFn == nil {
		return nil, errors.New("query not implemented")
	}
	return f.queryFn(ctx, sql, args...)
}

func (f *fakePool) QueryRow(context.Context, string, ...any) pgx.Row {
	panic("unexpected QueryRow call")
}

func (f *fakePool) Exec(context.Context, string, ...any) (pgconn.CommandTag, error) {
	return pgconn.CommandTag{}, errors.New("unexpected Exec call")
}

func (f *fakePool) Begin(context.Context) (pgx.Tx, error) {
	return nil, errors.New("unexpected Begin call")
}

func (f *fakePool) Ping(context.Context) error { return nil }

type fakeRows struct {
	data [][]any
	idx  int
}

func (f *fakeRows) Close() {}

func (f *fakeRows) Err() error { return nil }

func (f *fakeRows) CommandTag() pgconn.CommandTag { return pgconn.CommandTag{} }

func (f *fakeRows) FieldDescriptions() []pgconn.FieldDescription { return nil }

func (f *fakeRows) Next() bool {
	if f.idx >= len(f.data) {
		return false
	}
	f.idx++
	return true
}

func (f *fakeRows) Scan(dest ...any) error {
	if f.idx == 0 || f.idx > len(f.data) {
		return errors.New("scan called without row")
	}
	row := f.data[f.idx-1]
	if len(row) < len(dest) {
		return fmt.Errorf("row has %d values, want %d", len(row), len(dest))
	}
	for i, d := range dest {
		switch v := d.(type) {
		case *string:
			if row[i] == nil {
				*v = ""
			} else {
				*v = row[i].(string)
			}
		case *sql.NullString:
			if row[i] == nil {
				v.Valid = false
				v.String = ""
			} else {
				v.Valid = true
				v.String = row[i].(string)
			}
		case *time.Time:
			if row[i] == nil {
				*v = time.Time{}
			} else {
				*v = row[i].(time.Time)
			}
		case *bool:
			if row[i] == nil {
				*v = false
			} else {
				*v = row[i].(bool)
			}
		case *sql.NullTime:
			if row[i] == nil {
				v.Valid = false
				v.Time = time.Time{}
			} else {
				v.Valid = true
				v.Time = row[i].(time.Time)
			}
		default:
			return fmt.Errorf("unsupported dest type %T", d)
		}
	}
	return nil
}

func (f *fakeRows) Values() ([]any, error) {
	if f.idx == 0 || f.idx > len(f.data) {
		return nil, errors.New("no current row")
	}
	return f.data[f.idx-1], nil
}

func (f *fakeRows) RawValues() [][]byte { return nil }

func (f *fakeRows) Conn() *pgx.Conn { return nil }

func TestListCareTeams(t *testing.T) {
	createdAt := time.Now().UTC()
	pool := &fakePool{
		queryFn: func(ctx context.Context, query string, args ...any) (pgx.Rows, error) {
			if !strings.Contains(query, "FROM care_teams") {
				t.Fatalf("unexpected query: %s", query)
			}
			if len(args) != 2 || args[0] != 10 || args[1] != 0 {
				t.Fatalf("unexpected args: %#v", args)
			}
			rows := [][]any{{"team-1", "org-1", "Org Uno", "Equipo Azul", createdAt}}
			return &fakeRows{data: rows}, nil
		},
	}
	repo := NewRepoWithPool(pool, nil)

	teams, err := repo.ListCareTeams(context.Background(), 10, 0)
	if err != nil {
		t.Fatalf("ListCareTeams error: %v", err)
	}
	if len(teams) != 1 {
		t.Fatalf("expected 1 team, got %d", len(teams))
	}
	got := teams[0]
	if got.ID != "team-1" || got.Name != "Equipo Azul" {
		t.Fatalf("unexpected team %+v", got)
	}
	if got.OrgID == nil || *got.OrgID != "org-1" {
		t.Fatalf("unexpected org id: %v", got.OrgID)
	}
	if got.OrgName == nil || *got.OrgName != "Org Uno" {
		t.Fatalf("unexpected org name: %v", got.OrgName)
	}
	if diff := got.CreatedAt.Sub(createdAt); diff > time.Second || diff < -time.Second {
		t.Fatalf("createdAt mismatch: got %v want %v", got.CreatedAt, createdAt)
	}
}

func TestListCaregiverRelations(t *testing.T) {
	started := time.Now().Add(-24 * time.Hour)
	ended := started.Add(12 * time.Hour)
	pool := &fakePool{
		queryFn: func(ctx context.Context, query string, args ...any) (pgx.Rows, error) {
			if !strings.Contains(query, "FROM caregiver_patient") {
				t.Fatalf("unexpected query: %s", query)
			}
			if len(args) != 2 || args[0] != 20 || args[1] != 0 {
				t.Fatalf("unexpected args: %#v", args)
			}
			rows := [][]any{{
				"patient-1",
				"Juan",
				"user-9",
				"María",
				"maria@example.com",
				"rel-1",
				"parent",
				"Padre/Madre",
				true,
				started,
				ended,
				"Contacto principal",
			}}
			return &fakeRows{data: rows}, nil
		},
	}
	repo := NewRepoWithPool(pool, nil)

	relations, err := repo.ListCaregiverRelations(context.Background(), 20, 0)
	if err != nil {
		t.Fatalf("ListCaregiverRelations error: %v", err)
	}
	if len(relations) != 1 {
		t.Fatalf("expected 1 relation, got %d", len(relations))
	}
	rel := relations[0]
	if rel.PatientID != "patient-1" || rel.CaregiverID != "user-9" {
		t.Fatalf("unexpected relation IDs: %+v", rel)
	}
	if rel.PatientName != "Juan" || rel.CaregiverName != "María" {
		t.Fatalf("unexpected names: %+v", rel)
	}
	if rel.RelationTypeID == nil || *rel.RelationTypeID != "rel-1" {
		t.Fatalf("unexpected relation type: %v", rel.RelationTypeID)
	}
	if !rel.IsPrimary {
		t.Fatalf("expected relation to be primary")
	}
	if rel.Note == nil || *rel.Note != "Contacto principal" {
		t.Fatalf("unexpected note: %v", rel.Note)
	}
	if diff := rel.StartedAt.Sub(started); diff > time.Second || diff < -time.Second {
		t.Fatalf("unexpected startedAt: %v", rel.StartedAt)
	}
	if rel.EndedAt == nil {
		t.Fatalf("expected endedAt")
	}
	if diff := rel.EndedAt.Sub(ended); diff > time.Second || diff < -time.Second {
		t.Fatalf("unexpected endedAt: %v", *rel.EndedAt)
	}
}
