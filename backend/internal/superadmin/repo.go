package superadmin

import (
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "strings"
    "time"

    "github.com/google/uuid"
    "github.com/jackc/pgx/v5"
    "github.com/jackc/pgx/v5/pgxpool"
    "heartguard-superadmin/internal/models"
)


type Repo struct{ pool *pgxpool.Pool }

func NewRepo(pool *pgxpool.Pool) *Repo { return &Repo{pool: pool} }

// Organizations
func (r *Repo) CreateOrganization(ctx context.Context, code, name string) (*models.Organization, error) {
	var m models.Organization
	err := r.pool.QueryRow(ctx,
		`INSERT INTO organizations (id, code, name, created_at)
		 VALUES (gen_random_uuid(), $1, $2, NOW())
		 RETURNING id, code, name, created_at`, code, name,
	).Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt)
	return &m, err
}

func (r *Repo) ListOrganizations(ctx context.Context, limit, offset int) ([]models.Organization, error) {
	rows, err := r.pool.Query(ctx,
		`SELECT id, code, name, created_at
		   FROM organizations
		  ORDER BY created_at DESC
		  LIMIT $1 OFFSET $2`, limit, offset,
	)
	if err != nil { return nil, err }
	defer rows.Close()
	var out []models.Organization
	for rows.Next() {
		var m models.Organization
		if err := rows.Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt); err != nil { return nil, err }
		out = append(out, m)
	}
	return out, rows.Err()
}

func (r *Repo) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	var m models.Organization
	err := r.pool.QueryRow(ctx,
		`SELECT id, code, name, created_at FROM organizations WHERE id=$1`, id,
	).Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt)
	return &m, err
}

func (r *Repo) UpdateOrganization(ctx context.Context, id string, code, name *string) (*models.Organization, error) {
	var m models.Organization
	err := r.pool.QueryRow(ctx,
		`UPDATE organizations SET
		   code = COALESCE($2, code),
		   name = COALESCE($3, name)
		  WHERE id=$1
		  RETURNING id, code, name, created_at`, id, code, name,
	).Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt)
	return &m, err
}

func (r *Repo) DeleteOrganization(ctx context.Context, id string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM organizations WHERE id=$1`, id)
	if err != nil { return err }
	if ct.RowsAffected() == 0 { return pgx.ErrNoRows }
	return nil
}

// Invitations
func (r *Repo) CreateInvitation(ctx context.Context, orgID, orgRoleID string, email *string, ttl time.Duration, createdBy *string) (*models.OrgInvitation, error) {
	token := uuid.NewString()
	var m models.OrgInvitation
	err := r.pool.QueryRow(ctx,
		`INSERT INTO org_invitations (id, org_id, email, org_role_id, token, expires_at, created_by, created_at)
		 VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW() + make_interval(secs => $5), $6, NOW())
		 RETURNING id, org_id, email, org_role_id, token, expires_at, used_at, created_by, created_at`,
		orgID, email, orgRoleID, token, int64(ttl.Seconds()), createdBy,
	).Scan(&m.ID, &m.OrgID, &m.Email, &m.OrgRoleID, &m.Token, &m.ExpiresAt, &m.UsedAt, &m.CreatedBy, &m.CreatedAt)
	return &m, err
}

func (r *Repo) ConsumeInvitation(ctx context.Context, token, userID string) error {
	return withTx(ctx, r.pool, func(tx pgx.Tx) error {
		var orgID, roleID string
		if err := tx.QueryRow(ctx,
			`SELECT org_id, org_role_id
			   FROM org_invitations
			  WHERE token=$1 AND used_at IS NULL AND expires_at > NOW()
			  FOR UPDATE`, token,
		).Scan(&orgID, &roleID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx,
			`INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
			 VALUES ($1, $2, $3, NOW())
			 ON CONFLICT (org_id, user_id) DO UPDATE SET org_role_id = EXCLUDED.org_role_id`,
			orgID, userID, roleID,
		); err != nil {
			return err
		}
		_, err := tx.Exec(ctx, `UPDATE org_invitations SET used_at = NOW() WHERE token=$1`, token)
		return err
	})
}

// Memberships
func (r *Repo) AddMember(ctx context.Context, orgID, userID, orgRoleID string) error {
	_, err := r.pool.Exec(ctx,
		`INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
		 VALUES ($1, $2, $3, NOW())
		 ON CONFLICT (org_id, user_id) DO UPDATE SET org_role_id = EXCLUDED.org_role_id`,
		orgID, userID, orgRoleID,
	)
	return err
}

func (r *Repo) RemoveMember(ctx context.Context, orgID, userID string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM user_org_membership WHERE org_id=$1 AND user_id=$2`, orgID, userID)
	if err != nil { return err }
	if ct.RowsAffected() == 0 { return pgx.ErrNoRows }
	return nil
}

// Users
func (r *Repo) SearchUsers(ctx context.Context, q string, limit, offset int) ([]models.User, error) {
	rows, err := r.pool.Query(ctx,
		`SELECT u.id, u.name, u.email, us.code AS status, u.created_at
		   FROM users u JOIN user_statuses us ON us.id = u.user_status_id
		  WHERE ($1 = '' OR u.email ILIKE '%'||$1||'%' OR u.name ILIKE '%'||$1||'%')
		  ORDER BY u.created_at DESC
		  LIMIT $2 OFFSET $3`, q, limit, offset,
	)
	if err != nil { return nil, err }
	defer rows.Close()
	var out []models.User
	for rows.Next() {
		var m models.User
		if err := rows.Scan(&m.ID, &m.Name, &m.Email, &m.Status, &m.CreatedAt); err != nil { return nil, err }
		out = append(out, m)
	}
	return out, rows.Err()
}

func (r *Repo) UpdateUserStatus(ctx context.Context, userID, userStatusCode string) error {
	_, err := r.pool.Exec(ctx,
		`UPDATE users SET user_status_id = (SELECT id FROM user_statuses WHERE code=$2)
		  WHERE id=$1`, userID, userStatusCode,
	)
	return err
}

func (r *Repo) CreateAPIKey(ctx context.Context, label string, expires *time.Time, hashHex string, ownerUserID *string) (string, error) {
	var id string
	err := r.pool.QueryRow(ctx,
		`INSERT INTO api_keys (id, key_hash, label, owner_user_id, created_at, expires_at)
		 VALUES (gen_random_uuid(), $1, $2, $3, NOW(), $4)
		 RETURNING id`,
		hashHex, label, ownerUserID, expires,
	).Scan(&id)
	return id, err
}

func (r *Repo) RevokeAPIKey(ctx context.Context, id string) error {
	uid, err := uuid.Parse(id)
	if err != nil {
		return err
	}
	cmd, err := r.pool.Exec(ctx, `
UPDATE api_keys
SET revoked_at = NOW()
WHERE id = $1 AND revoked_at IS NULL
`, uid)
	if err != nil {
		return err
	}
	if cmd.RowsAffected() == 0 {
		return errors.New("not_found_or_already_revoked")
	}
	return nil
}

func (r *Repo) SetAPIKeyPermissions(ctx context.Context, id string, permCodes []string) error {
	return withTx(ctx, r.pool, func(tx pgx.Tx) error {
		if _, err := tx.Exec(ctx, `DELETE FROM api_key_permission WHERE api_key_id=$1`, id); err != nil {
			return err
		}
		for _, code := range permCodes {
			if _, err := tx.Exec(ctx,
				`INSERT INTO api_key_permission (api_key_id, permission_id, granted_at)
				 SELECT $1, p.id, NOW()
				   FROM permissions p WHERE p.code=$2`, id, code,
			); err != nil {
				return err
			}
		}
		return nil
	})
}

func (r *Repo) ListAPIKeys(ctx context.Context, activeOnly bool, limit, offset int) ([]models.APIKey, error) {
	q := `
SELECT
  id,
  COALESCE(label, '') AS label,
  owner_user_id,
  COALESCE(scopes, ARRAY[]::text[]) AS scopes,
  expires_at,
  created_at,
  revoked_at,
  (revoked_at IS NOT NULL) AS revoked
FROM api_keys
`
	if activeOnly {
		q += "WHERE revoked_at IS NULL\n"
	}
	q += "ORDER BY COALESCE(revoked_at, created_at) DESC\nLIMIT $1 OFFSET $2"

	rows, err := r.pool.Query(ctx, q, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.APIKey, 0, 32)
	for rows.Next() {
		var item models.APIKey
		var owner *uuid.UUID
		var scopes []string
		if err := rows.Scan(
			&item.ID,
			&item.Label,
			&owner,
			&scopes,
			&item.ExpiresAt,
			&item.CreatedAt,
			&item.RevokedAt,
			&item.Revoked,
		); err != nil {
			return nil, err
		}
		if owner != nil {
			s := owner.String()
			item.OwnerUserID = &s
		}
		item.Scopes = scopes
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

// Audit
func (r *Repo) ListAudit(ctx context.Context, from, to *time.Time, action *string, limit, offset int) ([]models.AuditLog, error) {
    where := "WHERE 1=1\n"
    args := []any{}
    i := 1

    if from != nil {
        where += fmt.Sprintf("AND ts >= $%d\n", i)
        args = append(args, *from)
        i++
    }
    if to != nil {
        where += fmt.Sprintf("AND ts <= $%d\n", i)
        args = append(args, *to)
        i++
    }
    if action != nil && strings.TrimSpace(*action) != "" {
        where += fmt.Sprintf("AND action = $%d\n", i)
        args = append(args, strings.TrimSpace(*action))
        i++
    }

    query := fmt.Sprintf(`
SELECT
  id::text,
  action,
  ts,
  user_id,          -- uuid nullable
  entity,           -- text nullable
  entity_id,        -- uuid nullable
  details,          -- jsonb nullable
  ip::text          -- inet -> text
FROM audit_logs
%s
ORDER BY ts DESC
LIMIT $%d OFFSET $%d
`, where, i, i+1)

    args = append(args, limit, offset)

    rows, err := r.pool.Query(ctx, query, args...)
    if err != nil {
        return nil, err
    }
    defer rows.Close()

    out := make([]models.AuditLog, 0, limit)
    for rows.Next() {
        var (
            idText     string
            actionStr  string
            ts         time.Time
            userUUID   *uuid.UUID
            entity     *string
            entityUUID *uuid.UUID
            detailsRaw []byte
            ipText     *string
        )
        if err := rows.Scan(
            &idText,
            &actionStr,
            &ts,
            &userUUID,
            &entity,
            &entityUUID,
            &detailsRaw,
            &ipText,
        ); err != nil {
            return nil, err
        }

        var userID *string
        if userUUID != nil {
            s := userUUID.String()
            userID = &s
        }
        var entityID *string
        if entityUUID != nil {
            s := entityUUID.String()
            entityID = &s
        }

        var details map[string]any
        if len(detailsRaw) > 0 {
            _ = json.Unmarshal(detailsRaw, &details) // si falla, deja nil
        }

        out = append(out, models.AuditLog{
            ID:       idText,
            Action:   actionStr,
            TS:       ts,
            UserID:   userID,
            Entity:   entity,
            EntityID: entityID,
            Details:  details,
            IP:       ipText,
        })
    }
    if err := rows.Err(); err != nil {
        return nil, err
    }
    return out, nil
}

// util
func withTx(ctx context.Context, pool *pgxpool.Pool, fn func(pgx.Tx) error) error {
	tx, err := pool.Begin(ctx)
	if err != nil { return err }
	defer func() {
		if err != nil { _ = tx.Rollback(ctx) }
	}()
	if err = fn(tx); err != nil { return err }
	return tx.Commit(ctx)
}
