package superadmin

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"sort"
	"strings"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
	"heartguard-superadmin/internal/models"
)

type pgPool interface {
	Query(context.Context, string, ...any) (pgx.Rows, error)
	QueryRow(context.Context, string, ...any) pgx.Row
	Exec(context.Context, string, ...any) (pgconn.CommandTag, error)
	Begin(context.Context) (pgx.Tx, error)
	Ping(context.Context) error
}

type Repo struct {
	pool      pgPool
	auditPool *pgxpool.Pool
}

func NewRepo(pool *pgxpool.Pool) *Repo {
	return &Repo{pool: pool, auditPool: pool}
}

// NewRepoWithPool allows injecting a custom pgx pool implementation (tests).
func NewRepoWithPool(pool pgPool) *Repo { return &Repo{pool: pool} }

func (r *Repo) AuditPool() *pgxpool.Pool { return r.auditPool }

func (r *Repo) Ping(ctx context.Context) error {
	if r.pool == nil {
		return errors.New("nil pool")
	}
	return r.pool.Ping(ctx)
}

var nowFn = time.Now

type catalogSpec struct {
	table       string
	label       string
	description string
	hasWeight   bool
}

var catalogs = map[string]catalogSpec{
	"user_statuses":         {table: "user_statuses", label: "Estados de usuario", description: "Estados disponibles para cuentas", hasWeight: false},
	"signal_types":          {table: "signal_types", label: "Tipos de señal", description: "Identificadores de señales clínicas", hasWeight: false},
	"alert_channels":        {table: "alert_channels", label: "Canales de alerta", description: "Canales de entrega disponibles", hasWeight: false},
	"alert_levels":          {table: "alert_levels", label: "Niveles de alerta", description: "Niveles con ponderación", hasWeight: true},
	"sexes":                 {table: "sexes", label: "Sexos", description: "Clasificación biológica", hasWeight: false},
	"platforms":             {table: "platforms", label: "Plataformas", description: "Plataformas soportadas", hasWeight: false},
	"service_statuses":      {table: "service_statuses", label: "Estados de servicio", description: "Estado operativo de servicios", hasWeight: false},
	"delivery_statuses":     {table: "delivery_statuses", label: "Estados de entrega", description: "Seguimiento de entregas", hasWeight: false},
	"batch_export_statuses": {table: "batch_export_statuses", label: "Estados de exportación", description: "Estados de lotes de export", hasWeight: false},
}

func invitationStatus(inv *models.OrgInvitation, now time.Time) string {
	if inv == nil {
		return ""
	}
	if inv.RevokedAt != nil {
		return "revoked"
	}
	if inv.UsedAt != nil {
		return "used"
	}
	if now.After(inv.ExpiresAt) {
		return "expired"
	}
	return "pending"
}

// ------------------------------
// Organizations
// ------------------------------
func (r *Repo) CreateOrganization(ctx context.Context, code, name string) (*models.Organization, error) {
	var m models.Organization
	err := r.pool.QueryRow(ctx, `
INSERT INTO organizations (id, code, name, created_at)
VALUES (gen_random_uuid(), $1, $2, NOW())
RETURNING id, code, name, created_at
`, code, name).Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt)
	return &m, err
}

func (r *Repo) ListOrganizations(ctx context.Context, limit, offset int) ([]models.Organization, error) {
	rows, err := r.pool.Query(ctx, `
SELECT id, code, name, created_at
FROM organizations
ORDER BY created_at DESC
LIMIT $1 OFFSET $2
`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.Organization
	for rows.Next() {
		var m models.Organization
		if err := rows.Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

func (r *Repo) GetOrganization(ctx context.Context, id string) (*models.Organization, error) {
	var m models.Organization
	err := r.pool.QueryRow(ctx, `
SELECT id, code, name, created_at
FROM organizations
WHERE id = $1
`, id).Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt)
	return &m, err
}

func (r *Repo) UpdateOrganization(ctx context.Context, id string, code, name *string) (*models.Organization, error) {
	var m models.Organization
	err := r.pool.QueryRow(ctx, `
UPDATE organizations SET
  code = COALESCE($2, code),
  name = COALESCE($3, name)
WHERE id = $1
RETURNING id, code, name, created_at
`, id, code, name).Scan(&m.ID, &m.Code, &m.Name, &m.CreatedAt)
	return &m, err
}

func (r *Repo) DeleteOrganization(ctx context.Context, id string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM organizations WHERE id=$1`, id)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Invitations
// ------------------------------
func (r *Repo) CreateInvitation(ctx context.Context, orgID, orgRoleID string, email *string, ttl time.Duration, createdBy *string) (*models.OrgInvitation, error) {
	seconds := int64(ttl.Seconds())
	if seconds <= 0 {
		seconds = int64((48 * time.Hour).Seconds())
	}
	var createdByUUID *uuid.UUID
	if createdBy != nil && *createdBy != "" {
		if parsed, err := uuid.Parse(*createdBy); err == nil {
			createdByUUID = &parsed
		}
	}
	var (
		item         models.OrgInvitation
		createdByOut *uuid.UUID
	)
	err := r.pool.QueryRow(ctx, `
SELECT id::text,
org_id::text,
email,
org_role_id::text,
org_role_code,
token,
expires_at,
used_at,
revoked_at,
created_by,
created_at
FROM heartguard.fn_invitation_create($1, $2, $3, $4, $5)
`, orgID, email, orgRoleID, seconds, createdByUUID).
		Scan(&item.ID, &item.OrgID, &item.Email, &item.OrgRoleID, &item.OrgRoleCode, &item.Token, &item.ExpiresAt, &item.UsedAt, &item.RevokedAt, &createdByOut, &item.CreatedAt)
	if err != nil {
		return nil, err
	}
	if createdByOut != nil {
		val := createdByOut.String()
		item.CreatedBy = &val
	}
	item.Status = invitationStatus(&item, nowFn())
	return &item, nil
}

func (r *Repo) ConsumeInvitation(ctx context.Context, token, userID string) error {
	return withTx(ctx, r.pool, func(tx pgx.Tx) error {
		var orgID, roleID string
		if err := tx.QueryRow(ctx, `
SELECT org_id, org_role_id
FROM org_invitations
WHERE token=$1 AND used_at IS NULL AND expires_at > NOW() AND revoked_at IS NULL
FOR UPDATE
`, token).Scan(&orgID, &roleID); err != nil {
			return err
		}
		if _, err := tx.Exec(ctx, `
INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
VALUES ($1, $2, $3, NOW())
ON CONFLICT (org_id, user_id) DO UPDATE SET org_role_id = EXCLUDED.org_role_id
`, orgID, userID, roleID); err != nil {
			return err
		}
		_, err := tx.Exec(ctx, `UPDATE org_invitations SET used_at = NOW() WHERE token=$1`, token)
		return err
	})
}

func (r *Repo) ListInvitations(ctx context.Context, orgID *string, status *string, limit, offset int) ([]models.OrgInvitation, error) {
	var orgParam any
	if orgID != nil && *orgID != "" {
		orgParam = *orgID
	}
	var statusParam any
	if status != nil && *status != "" {
		statusParam = strings.ToLower(*status)
	}
	rows, err := r.pool.Query(ctx, `
SELECT id::text,
org_id::text,
email,
org_role_id::text,
org_role_code,
token,
expires_at,
used_at,
revoked_at,
created_by,
created_at
FROM heartguard.fn_invitation_list($1, $2, $3, $4)
`, orgParam, statusParam, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.OrgInvitation, 0, limit)
	now := nowFn()
	for rows.Next() {
		var (
			createdBy *uuid.UUID
			item      models.OrgInvitation
		)
		if err := rows.Scan(
			&item.ID,
			&item.OrgID,
			&item.Email,
			&item.OrgRoleID,
			&item.OrgRoleCode,
			&item.Token,
			&item.ExpiresAt,
			&item.UsedAt,
			&item.RevokedAt,
			&createdBy,
			&item.CreatedAt,
		); err != nil {
			return nil, err
		}
		if createdBy != nil {
			s := createdBy.String()
			item.CreatedBy = &s
		}
		item.Status = invitationStatus(&item, now)
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) CancelInvitation(ctx context.Context, invitationID string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.fn_invitation_cancel($1)`, invitationID).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Memberships
// ------------------------------
func (r *Repo) AddMember(ctx context.Context, orgID, userID, orgRoleID string) error {
	_, err := r.pool.Exec(ctx, `
INSERT INTO user_org_membership (org_id, user_id, org_role_id, joined_at)
VALUES ($1, $2, $3, NOW())
ON CONFLICT (org_id, user_id) DO UPDATE SET org_role_id = EXCLUDED.org_role_id
`, orgID, userID, orgRoleID)
	return err
}

func (r *Repo) RemoveMember(ctx context.Context, orgID, userID string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM user_org_membership WHERE org_id=$1 AND user_id=$2`, orgID, userID)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListMembers(ctx context.Context, orgID string, limit, offset int) ([]models.Membership, error) {
	rows, err := r.pool.Query(ctx, `
SELECT
        m.org_id::text,
        m.user_id::text,
        u.email,
        u.name,
        m.org_role_id::text,
        COALESCE(oroles.code, '') AS role_code,
        COALESCE(oroles.label, '') AS role_label,
        m.joined_at
FROM user_org_membership m
JOIN users u ON u.id = m.user_id
LEFT JOIN org_roles oroles ON oroles.id = m.org_role_id
WHERE m.org_id = $1
ORDER BY m.joined_at DESC
LIMIT $2 OFFSET $3
`, orgID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Membership, 0, limit)
	for rows.Next() {
		var item models.Membership
		if err := rows.Scan(
			&item.OrgID,
			&item.UserID,
			&item.Email,
			&item.Name,
			&item.OrgRoleID,
			&item.OrgRoleCode,
			&item.OrgRoleLabel,
			&item.JoinedAt,
		); err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

// ------------------------------
// Catalogs
// ------------------------------

func (r *Repo) CatalogDefinitions() []models.CatalogDefinition {
	defs := make([]models.CatalogDefinition, 0, len(catalogs))
	for slug, spec := range catalogs {
		defs = append(defs, models.CatalogDefinition{
			Slug:        slug,
			Label:       spec.label,
			Description: spec.description,
			HasWeight:   spec.hasWeight,
		})
	}
	sort.Slice(defs, func(i, j int) bool { return defs[i].Label < defs[j].Label })
	return defs
}

func (r *Repo) GetCatalogDefinition(slug string) (models.CatalogDefinition, bool) {
	spec, ok := catalogs[slug]
	if !ok {
		return models.CatalogDefinition{}, false
	}
	return models.CatalogDefinition{
		Slug:        slug,
		Label:       spec.label,
		Description: spec.description,
		HasWeight:   spec.hasWeight,
	}, true
}

func (r *Repo) ListCatalogItems(ctx context.Context, slug string, limit, offset int) ([]models.CatalogItem, error) {
	rows, err := r.pool.Query(ctx, `SELECT id::text, code, label, weight FROM heartguard.fn_catalog_list($1, $2, $3)`, slug, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	items := make([]models.CatalogItem, 0, limit)
	for rows.Next() {
		var (
			item   models.CatalogItem
			weight sql.NullInt32
		)
		if err := rows.Scan(&item.ID, &item.Code, &item.Label, &weight); err != nil {
			return nil, err
		}
		if weight.Valid {
			w := int(weight.Int32)
			item.Weight = &w
		}
		items = append(items, item)
	}
	return items, rows.Err()
}

func (r *Repo) CreateCatalogItem(ctx context.Context, slug, code, label string, weight *int) (*models.CatalogItem, error) {
	var weightArg any
	if weight != nil {
		weightArg = *weight
	}
	var (
		item   models.CatalogItem
		wField sql.NullInt32
	)
	err := r.pool.QueryRow(ctx, `SELECT id::text, code, label, weight FROM heartguard.fn_catalog_create($1, $2, $3, $4)`, slug, code, label, weightArg).
		Scan(&item.ID, &item.Code, &item.Label, &wField)
	if err != nil {
		return nil, err
	}
	if wField.Valid {
		w := int(wField.Int32)
		item.Weight = &w
	}
	return &item, nil
}

func (r *Repo) UpdateCatalogItem(ctx context.Context, slug, id string, code, label *string, weight *int) (*models.CatalogItem, error) {
	var weightArg any
	if weight != nil {
		weightArg = *weight
	}
	var (
		item   models.CatalogItem
		wField sql.NullInt32
	)
	err := r.pool.QueryRow(ctx, `SELECT id::text, code, label, weight FROM heartguard.fn_catalog_update($1, $2, $3, $4, $5)`, slug, id, code, label, weightArg).
		Scan(&item.ID, &item.Code, &item.Label, &wField)
	if err != nil {
		return nil, err
	}
	if wField.Valid {
		w := int(wField.Int32)
		item.Weight = &w
	}
	return &item, nil
}

func (r *Repo) DeleteCatalogItem(ctx context.Context, slug, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.fn_catalog_delete($1, $2)`, slug, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Users
// ------------------------------
func (r *Repo) SearchUsers(ctx context.Context, q string, limit, offset int) ([]models.User, error) {
	rows, err := r.pool.Query(ctx, `
SELECT u.id, u.name, u.email, us.code AS status, u.created_at
FROM users u
JOIN user_statuses us ON us.id = u.user_status_id
WHERE ($1 = '' OR u.email ILIKE '%'||$1||'%' OR u.name ILIKE '%'||$1||'%')
ORDER BY u.created_at DESC
LIMIT $2 OFFSET $3
`, q, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.User
	for rows.Next() {
		var m models.User
		if err := rows.Scan(&m.ID, &m.Name, &m.Email, &m.Status, &m.CreatedAt); err != nil {
			return nil, err
		}
		out = append(out, m)
	}
	return out, rows.Err()
}

func (r *Repo) UpdateUserStatus(ctx context.Context, userID, userStatusCode string) error {
	_, err := r.pool.Exec(ctx, `
UPDATE users
SET user_status_id = (SELECT id FROM user_statuses WHERE code=$2)
WHERE id=$1
`, userID, userStatusCode)
	return err
}

// ------------------------------
// API Keys
// ------------------------------
func (r *Repo) CreateAPIKey(ctx context.Context, label string, expires *time.Time, hashHex string, ownerUserID *string) (string, error) {
	var id string
	err := r.pool.QueryRow(ctx, `
INSERT INTO api_keys (id, key_hash, label, owner_user_id, created_at, expires_at)
VALUES (gen_random_uuid(), $1, $2, $3, NOW(), $4)
RETURNING id
`, hashHex, label, ownerUserID, expires).Scan(&id)
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
			if _, err := tx.Exec(ctx, `
INSERT INTO api_key_permission (api_key_id, permission_id, granted_at)
SELECT $1, p.id, NOW()
FROM permissions p WHERE p.code=$2
`, id, code); err != nil {
				return err
			}
		}
		return nil
	})
}

func (r *Repo) ListAPIKeys(ctx context.Context, activeOnly bool, limit, offset int) ([]models.APIKey, error) {
	// Construimos scopes desde permisos relacionados
	where := ""
	if activeOnly {
		where = "WHERE k.revoked_at IS NULL"
	}
	q := fmt.Sprintf(`
SELECT
  k.id,
  COALESCE(k.label,'')                           AS label,
  k.owner_user_id,
  COALESCE(
    array_agg(DISTINCT p.code) FILTER (WHERE p.code IS NOT NULL),
    ARRAY[]::text[]
  )                                              AS scopes,
  k.expires_at,
  k.created_at,
  k.revoked_at,
  (k.revoked_at IS NOT NULL)                     AS revoked
FROM api_keys k
LEFT JOIN api_key_permission akp ON akp.api_key_id = k.id
LEFT JOIN permissions p          ON p.id = akp.permission_id
%s
GROUP BY k.id
ORDER BY COALESCE(k.revoked_at, k.created_at) DESC
LIMIT $1 OFFSET $2
`, where)

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

// ------------------------------
// Audit
// ------------------------------
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
  user_id,
  entity,
  entity_id,
  details,
  ip::text
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
			_ = json.Unmarshal(detailsRaw, &details)
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

// ------------------------------
// Metrics
// ------------------------------

func (r *Repo) MetricsOverview(ctx context.Context, minutes int) (*models.MetricsOverview, error) {
	if minutes <= 0 {
		minutes = 1440
	}
	var (
		avgResp                                                    sql.NullFloat64
		opJSON                                                     []byte
		activeUsers, activeOrgs, pendingInv, totalUsers, totalOrgs int
	)
	if err := r.pool.QueryRow(ctx, `
SELECT avg_response_ms, operation_counts, active_users, active_orgs, pending_invitations, total_users, total_orgs
FROM heartguard.fn_metrics_overview($1)
`, minutes).Scan(&avgResp, &opJSON, &activeUsers, &activeOrgs, &pendingInv, &totalUsers, &totalOrgs); err != nil {
		return nil, err
	}
	var operations []models.OperationCount
	if len(opJSON) > 0 {
		_ = json.Unmarshal(opJSON, &operations)
	}
	res := &models.MetricsOverview{
		AverageResponseMS:   avgResp.Float64,
		OperationCounts:     operations,
		ActiveUsers:         activeUsers,
		ActiveOrganizations: activeOrgs,
		TotalUsers:          totalUsers,
		TotalOrganizations:  totalOrgs,
		PendingInvitations:  pendingInv,
	}
	return res, nil
}

func (r *Repo) RecentActivity(ctx context.Context, limit int) ([]models.ActivityEntry, error) {
	if limit <= 0 || limit > 200 {
		limit = 20
	}
	rows, err := r.pool.Query(ctx, `SELECT ts, action, entity, user_id FROM heartguard.fn_metrics_recent_activity($1)`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	entries := make([]models.ActivityEntry, 0, limit)
	for rows.Next() {
		var (
			entry  models.ActivityEntry
			entity *string
			userID *uuid.UUID
		)
		if err := rows.Scan(&entry.TS, &entry.Action, &entity, &userID); err != nil {
			return nil, err
		}
		entry.Entity = entity
		if userID != nil {
			s := userID.String()
			entry.UserID = &s
		}
		entries = append(entries, entry)
	}
	return entries, rows.Err()
}

// ------------------------------
// Auth helpers (refresh tokens)
// ------------------------------
func (r *Repo) GetUserByEmail(ctx context.Context, email string) (*models.User, string, error) {
	row := r.pool.QueryRow(ctx, `
SELECT u.id::text, u.name, u.email, us.code AS status, u.created_at, u.password_hash
FROM users u
JOIN user_statuses us ON us.id = u.user_status_id
WHERE lower(u.email) = lower($1) AND us.code <> 'blocked'
`, email)
	var u models.User
	var hash string
	if err := row.Scan(&u.ID, &u.Name, &u.Email, &u.Status, &u.CreatedAt, &hash); err != nil {
		return nil, "", err
	}
	return &u, hash, nil
}

func (r *Repo) IsSuperadmin(ctx context.Context, userID string) (bool, error) {
	var ok bool
	err := r.pool.QueryRow(ctx, `
SELECT EXISTS (
  SELECT 1
  FROM user_role ur
  JOIN roles r ON r.id = ur.role_id
  WHERE ur.user_id = $1 AND r.name = 'superadmin'
)
`, userID).Scan(&ok)
	return ok, err
}

func (r *Repo) IssueRefreshToken(ctx context.Context, userID, tokenHash string, ttl time.Duration) error {
	_, err := r.pool.Exec(ctx, `
INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at)
VALUES ($1, $2, NOW(), NOW() + make_interval(secs => $3))
ON CONFLICT (user_id, token_hash) DO NOTHING
`, userID, tokenHash, int64(ttl.Seconds()))
	return err
}

func (r *Repo) ValidateRefreshToken(ctx context.Context, raw string) (string, error) {
	sum := sha256.Sum256([]byte(raw))
	hash := hex.EncodeToString(sum[:])
	var uid string
	err := r.pool.QueryRow(ctx, `
SELECT user_id::text
FROM refresh_tokens
WHERE token_hash = $1 AND revoked_at IS NULL AND expires_at > NOW()
`, hash).Scan(&uid)
	return uid, err
}

func (r *Repo) RevokeRefreshToken(ctx context.Context, raw string) error {
	sum := sha256.Sum256([]byte(raw))
	hash := hex.EncodeToString(sum[:])
	_, err := r.pool.Exec(ctx, `
UPDATE refresh_tokens
SET revoked_at = NOW()
WHERE token_hash = $1 AND revoked_at IS NULL
`, hash)
	return err
}

// ------------------------------
// Tx helper
// ------------------------------
func withTx(ctx context.Context, pool pgPool, fn func(pgx.Tx) error) (err error) {
	tx, err := pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer func() {
		if err != nil {
			_ = tx.Rollback(ctx)
		}
	}()
	if err = fn(tx); err != nil {
		return err
	}
	return tx.Commit(ctx)
}
