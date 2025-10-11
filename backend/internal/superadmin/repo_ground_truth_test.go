package superadmin

import (
	"context"
	"database/sql"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"

	"heartguard-superadmin/internal/models"
)

func TestRepo_ListGroundTruthByPatient(t *testing.T) {
	ctx := context.Background()
	onset := time.Date(2024, 5, 1, 10, 0, 0, 0, time.UTC)
	offset := onset.Add(30 * time.Minute)

	rows := &fakeRows{records: [][]any{{
		"lbl-1",
		"pat-1",
		"Paciente Uno",
		"evt-1",
		"EVT",
		nullableString("Arritmia"),
		onset,
		nullableTime(offset),
		nullableString("user-1"),
		nullableString("Ana"),
		nullableString("manual"),
		nullableString("Observación"),
	}, {
		"lbl-2",
		"pat-1",
		"Paciente Uno",
		"evt-2",
		"ALT",
		sqlNullString{},
		onset.Add(-2 * time.Hour),
		sqlNullTime{},
		sqlNullString{},
		sqlNullString{},
		sqlNullString{},
		sqlNullString{},
	}}}

	stub := &stubPool{queryRows: rows}
	repo := NewRepoWithPool(stub, nil)

	got, err := repo.ListGroundTruthByPatient(ctx, "pat-1", 20, 0)
	if err != nil {
		t.Fatalf("ListGroundTruthByPatient: %v", err)
	}
	if len(got) != 2 {
		t.Fatalf("expected 2 labels, got %d", len(got))
	}
	if got[0].ID != "lbl-1" || got[0].EventTypeLabel != "Arritmia" {
		t.Fatalf("unexpected first label: %+v", got[0])
	}
	if got[0].OffsetAt == nil || !got[0].OffsetAt.Equal(offset) {
		t.Fatalf("expected offset %v, got %+v", offset, got[0].OffsetAt)
	}
	if got[1].EventTypeLabel != "ALT" {
		t.Fatalf("expected fallback label ALT, got %q", got[1].EventTypeLabel)
	}
	if !strings.Contains(stub.querySQL, "FROM heartguard.ground_truth_labels") {
		t.Fatalf("unexpected query: %s", stub.querySQL)
	}
}

func TestRepo_CreateGroundTruthLabel(t *testing.T) {
	ctx := context.Background()
	onset := time.Date(2024, 6, 10, 15, 0, 0, 0, time.UTC)
	offset := onset.Add(45 * time.Minute)
	source := "Manual"
	note := "Revisión clínica"
	annotated := "user-9"

	row := &fakeRow{record: []any{
		"lbl-new",
		"pat-7",
		"Paciente",
		"evt-3",
		"EV3",
		nullableString("Evento"),
		onset,
		nullableTime(offset),
		nullableString(annotated),
		nullableString("Dra. Pérez"),
		nullableString(source),
		nullableString(note),
	}}
	stub := &stubPool{queryRowRow: row}
	repo := NewRepoWithPool(stub, nil)

	input := models.GroundTruthLabelCreateInput{
		EventTypeID:       "evt-3",
		Onset:             onset,
		OffsetAt:          &offset,
		AnnotatedByUserID: &annotated,
		Source:            &source,
		Note:              &note,
	}
	label, err := repo.CreateGroundTruthLabel(ctx, "pat-7", input)
	if err != nil {
		t.Fatalf("CreateGroundTruthLabel: %v", err)
	}
	if label.ID != "lbl-new" || label.PatientName != "Paciente" {
		t.Fatalf("unexpected label: %+v", label)
	}
	if label.AnnotatedByName == nil || *label.AnnotatedByName != "Dra. Pérez" {
		t.Fatalf("expected annotator name, got %+v", label.AnnotatedByName)
	}
	if !strings.Contains(stub.queryRowSQL, "INSERT INTO heartguard.ground_truth_labels") {
		t.Fatalf("unexpected SQL: %s", stub.queryRowSQL)
	}
	if len(stub.queryRowArgs) != 7 {
		t.Fatalf("unexpected arg count: %d", len(stub.queryRowArgs))
	}
}

func TestRepo_UpdateGroundTruthLabel(t *testing.T) {
	ctx := context.Background()
	onset := time.Date(2024, 7, 3, 9, 0, 0, 0, time.UTC)
	offset := onset.Add(90 * time.Minute)
	source := "Sensor"
	note := "Actualización"
	row := &fakeRow{record: []any{
		"lbl-77",
		"pat-1",
		"Paciente",
		"evt-9",
		"EV9",
		nullableString("Evento crónico"),
		onset,
		nullableTime(offset),
		sqlNullString{},
		sqlNullString{},
		nullableString(source),
		nullableString(note),
	}}
	stub := &stubPool{queryRowRow: row}
	repo := NewRepoWithPool(stub, nil)

	eventType := "evt-9"
	input := models.GroundTruthLabelUpdateInput{
		EventTypeID:          &eventType,
		Onset:                &onset,
		OffsetAt:             &offset,
		OffsetAtSet:          true,
		AnnotatedByUserID:    nil,
		AnnotatedByUserIDSet: true,
		Source:               &source,
		SourceSet:            true,
		Note:                 &note,
		NoteSet:              true,
	}
	label, err := repo.UpdateGroundTruthLabel(ctx, "lbl-77", input)
	if err != nil {
		t.Fatalf("UpdateGroundTruthLabel: %v", err)
	}
	if label.EventTypeID != "evt-9" || label.Source == nil || *label.Source != "Sensor" {
		t.Fatalf("unexpected label after update: %+v", label)
	}
	if !strings.Contains(stub.queryRowSQL, "UPDATE heartguard.ground_truth_labels") {
		t.Fatalf("unexpected SQL: %s", stub.queryRowSQL)
	}
}

func TestRepo_DeleteGroundTruthLabel(t *testing.T) {
	ctx := context.Background()
	stub := &stubPool{execTag: pgconn.NewCommandTag("DELETE 1")}
	repo := NewRepoWithPool(stub, nil)

	if err := repo.DeleteGroundTruthLabel(ctx, "lbl-10"); err != nil {
		t.Fatalf("DeleteGroundTruthLabel: %v", err)
	}

	stub.execTag = pgconn.NewCommandTag("DELETE 0")
	if err := repo.DeleteGroundTruthLabel(ctx, "missing"); err == nil || !errors.Is(err, pgx.ErrNoRows) {
		t.Fatalf("expected pgx.ErrNoRows, got %v", err)
	}
	if !strings.Contains(stub.execSQL, "DELETE FROM heartguard.ground_truth_labels") {
		t.Fatalf("unexpected delete SQL: %s", stub.execSQL)
	}
}

// --- test helpers ---

type stubPool struct {
	querySQL     string
	queryArgs    []any
	queryRows    pgx.Rows
	queryErr     error
	queryRowSQL  string
	queryRowArgs []any
	queryRowRow  pgx.Row
	execSQL      string
	execArgs     []any
	execTag      pgconn.CommandTag
	execErr      error
}

func (s *stubPool) Query(ctx context.Context, sql string, args ...any) (pgx.Rows, error) {
	s.querySQL = sql
	s.queryArgs = args
	return s.queryRows, s.queryErr
}

func (s *stubPool) QueryRow(ctx context.Context, sql string, args ...any) pgx.Row {
	s.queryRowSQL = sql
	s.queryRowArgs = args
	if s.queryRowRow == nil {
		return &fakeRow{err: errors.New("no row")}
	}
	return s.queryRowRow
}

func (s *stubPool) Exec(ctx context.Context, sql string, args ...any) (pgconn.CommandTag, error) {
	s.execSQL = sql
	s.execArgs = args
	return s.execTag, s.execErr
}

func (s *stubPool) Begin(context.Context) (pgx.Tx, error) { return nil, errors.New("not implemented") }
func (s *stubPool) Ping(context.Context) error            { return nil }

type fakeRow struct {
	record []any
	err    error
}

func (r *fakeRow) Scan(dest ...any) error {
	if r.err != nil {
		return r.err
	}
	for i := range dest {
		assignValue(dest[i], r.record[i])
	}
	return nil
}

type fakeRows struct {
	records [][]any
	idx     int
	err     error
}

func (r *fakeRows) Close() {}

func (r *fakeRows) Err() error { return r.err }

func (r *fakeRows) CommandTag() pgconn.CommandTag { return pgconn.CommandTag{} }

func (r *fakeRows) FieldDescriptions() []pgconn.FieldDescription { return nil }

func (r *fakeRows) Next() bool {
	if r.idx >= len(r.records) {
		return false
	}
	r.idx++
	return true
}

func (r *fakeRows) Scan(dest ...any) error {
	if r.idx == 0 || r.idx > len(r.records) {
		return errors.New("scan called without next")
	}
	row := r.records[r.idx-1]
	for i := range dest {
		assignValue(dest[i], row[i])
	}
	return nil
}

func (r *fakeRows) Values() ([]any, error) { return nil, nil }
func (r *fakeRows) RawValues() [][]byte    { return nil }
func (r *fakeRows) Conn() *pgx.Conn        { return nil }

type sqlNullString = sql.NullString
type sqlNullTime = sql.NullTime

func nullableString(s string) sqlNullString { return sqlNullString{String: s, Valid: true} }
func nullableTime(t time.Time) sqlNullTime  { return sqlNullTime{Time: t, Valid: true} }

func assignValue(dest any, value any) {
	switch d := dest.(type) {
	case *string:
		*d = value.(string)
	case *time.Time:
		*d = value.(time.Time)
	case *sqlNullString:
		*d = value.(sqlNullString)
	case *sqlNullTime:
		*d = value.(sqlNullTime)
	default:
		switch v := value.(type) {
		case nil:
			// leave zero
		default:
			if setter, ok := d.(interface{ Scan(any) error }); ok {
				_ = setter.Scan(v)
			}
		}
	}
}
