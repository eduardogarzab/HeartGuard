package superadmin

import (
	"context"
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
	_, err := r.pool.Exec(ctx, `UPDATE api_keys SET revoked_at = NOW() WHERE id=$1`, id)
	return err
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

func (r *Repo) ListAPIKeys(ctx context.Context, limit, offset int) ([]models.APIKey, error) {
	rows, err := r.pool.Query(ctx,
		`SELECT id, label, created_at, expires_at, revoked_at
		   FROM api_keys
		  ORDER BY created_at DESC
		  LIMIT $1 OFFSET $2`, limit, offset,
	)
	if err != nil { return nil, err }
	defer rows.Close()
	var out []models.APIKey
	for rows.Next() {
		var m models.APIKey
		if err := rows.Scan(&m.ID, &m.Label, &m.CreatedAt, &m.ExpiresAt, &m.RevokedAt); err != nil { return nil, err }
		out = append(out, m)
	}
	return out, rows.Err()
}

// Audit
func (r *Repo) ListAudit(ctx context.Context, from, to *time.Time, action *string, limit, offset int) ([]models.AuditLog, error) {
	rows, err := r.pool.Query(ctx,
		`SELECT id, action, ts
		FROM audit_logs
		WHERE ($1::timestamptz IS NULL OR ts >= $1::timestamptz)
			AND ($2::timestamptz IS NULL OR ts <= $2::timestamptz)
			AND ($3::text IS NULL OR action = $3::text)
		ORDER BY ts DESC
		LIMIT $4 OFFSET $5`,
		from, to, action, limit, offset,
	)
	if err != nil { return nil, err }
	defer rows.Close()
	var out []models.AuditLog
	for rows.Next() {
		var a models.AuditLog
		if err := rows.Scan(&a.ID, &a.Action, &a.When); err != nil { return nil, err }
		out = append(out, a)
	}
	return out, rows.Err()
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
