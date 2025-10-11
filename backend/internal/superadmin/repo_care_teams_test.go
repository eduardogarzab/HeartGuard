package superadmin

import (
	"context"
	"testing"
	"time"

	"heartguard-superadmin/internal/models"

	"github.com/jackc/pgx/v5"
)

func TestRepoUpdateCareTeamParams(t *testing.T) {
	pool := &stubPool{}
	now := time.Now()
	pool.queryRow = func(ctx context.Context, sql string, args ...any) pgx.Row {
		if len(args) != 4 {
			t.Fatalf("expected 4 args, got %d", len(args))
		}
		if args[0] != "team-1" {
			t.Fatalf("unexpected id arg: %v", args[0])
		}
		if args[1] != "org-1" {
			t.Fatalf("unexpected org arg: %v", args[1])
		}
		if flag, ok := args[2].(bool); !ok || flag {
			t.Fatalf("expected clearOrg false, got %v", args[2])
		}
		if name, ok := args[3].(*string); !ok || *name != "Equipo" {
			t.Fatalf("unexpected name arg: %v", args[3])
		}
		return mockRow{values: []any{"team-1", "org-1", "Org", "Equipo", now}}
	}
	repo := NewRepoWithPool(pool, nil)
	name := "Equipo"
	org := "org-1"
	team, err := repo.UpdateCareTeam(context.Background(), "team-1", models.CareTeamUpdateInput{OrgID: &org, Name: &name})
	if err != nil {
		t.Fatalf("UpdateCareTeam: %v", err)
	}
	if team.OrgName == nil || *team.OrgName != "Org" {
		t.Fatalf("expected org name 'Org', got %#v", team.OrgName)
	}
}

func TestRepoUpdateCareTeamClearOrg(t *testing.T) {
	pool := &stubPool{}
	now := time.Now()
	pool.queryRow = func(ctx context.Context, sql string, args ...any) pgx.Row {
		if len(args) != 4 {
			t.Fatalf("expected 4 args, got %d", len(args))
		}
		if flag, ok := args[2].(bool); !ok || !flag {
			t.Fatalf("expected clearOrg true, got %v", args[2])
		}
		if args[1] != nil {
			t.Fatalf("expected nil org param, got %v", args[1])
		}
		return mockRow{values: []any{"team-1", nil, nil, "Equipo", now}}
	}
	repo := NewRepoWithPool(pool, nil)
	empty := ""
	name := "Equipo"
	team, err := repo.UpdateCareTeam(context.Background(), "team-1", models.CareTeamUpdateInput{OrgID: &empty, Name: &name})
	if err != nil {
		t.Fatalf("UpdateCareTeam: %v", err)
	}
	if team.OrgID != nil {
		t.Fatalf("expected nil org id, got %#v", team.OrgID)
	}
}

func TestRepoUpdateCaregiverAssignmentParams(t *testing.T) {
	pool := &stubPool{}
	now := time.Now()
	pool.queryRow = func(ctx context.Context, sql string, args ...any) pgx.Row {
		if len(args) != 12 {
			t.Fatalf("expected 12 args, got %d", len(args))
		}
		if args[0] != "patient-1" || args[1] != "caregiver-1" {
			t.Fatalf("unexpected ids: %v %v", args[0], args[1])
		}
		if setRel, ok := args[2].(bool); !ok || !setRel {
			t.Fatalf("expected setRel true, got %v", args[2])
		}
		if clearRel, ok := args[3].(bool); !ok || clearRel {
			t.Fatalf("expected clearRel false, got %v", args[3])
		}
		if relVal, ok := args[4].(string); !ok || relVal != "rel-1" {
			t.Fatalf("unexpected rel value: %v", args[4])
		}
		if _, ok := args[6].(*time.Time); !ok {
			t.Fatalf("expected started_at pointer, got %T", args[6])
		}
		if clearEnded, ok := args[7].(bool); !ok || !clearEnded {
			t.Fatalf("expected clear ended true, got %v", args[7])
		}
		if args[8] != nil {
			t.Fatalf("expected nil ended_at when clearing, got %v", args[8])
		}
		if setNote, ok := args[9].(bool); !ok || !setNote {
			t.Fatalf("expected setNote true, got %v", args[9])
		}
		if clearNote, ok := args[10].(bool); !ok || !clearNote {
			t.Fatalf("expected clearNote true, got %v", args[10])
		}
		if args[11] != nil {
			t.Fatalf("expected nil note param, got %v", args[11])
		}
		return mockRow{values: []any{"patient-1", "caregiver-1", nil, true, now, nil, nil}}
	}
	repo := NewRepoWithPool(pool, nil)
	started := time.Now()
	rel := "rel-1"
	note := ""
	input := models.CaregiverAssignmentUpdateInput{
		RelationshipTypeID: &rel,
		IsPrimary:          nil,
		StartedAt:          &started,
		ClearEndedAt:       true,
		Note:               &note,
	}
	if _, err := repo.UpdateCaregiverAssignment(context.Background(), "patient-1", "caregiver-1", input); err != nil {
		t.Fatalf("UpdateCaregiverAssignment: %v", err)
	}
}
