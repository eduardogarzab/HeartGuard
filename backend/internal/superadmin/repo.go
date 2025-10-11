package superadmin

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"strings"
	"time"

	"heartguard-superadmin/internal/models"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgconn"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/redis/go-redis/v9"
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
	redis     *redis.Client
}

func NewRepo(pool *pgxpool.Pool, redis *redis.Client) *Repo {
	return &Repo{pool: pool, auditPool: pool, redis: redis}
}

// NewRepoWithPool allows injecting a custom pgx pool implementation (tests).
func NewRepoWithPool(pool pgPool, redis *redis.Client) *Repo { return &Repo{pool: pool, redis: redis} }

func (r *Repo) AuditPool() *pgxpool.Pool { return r.auditPool }

func (r *Repo) Ping(ctx context.Context) error {
	if r.pool == nil {
		return errors.New("nil pool")
	}
	return r.pool.Ping(ctx)
}

var nowFn = time.Now

var errInvalidPlatform = errors.New("invalid platform")

func stringParam(ptr *string, trim bool) any {
	if ptr == nil {
		return nil
	}
	if trim {
		v := strings.TrimSpace(*ptr)
		if v == "" {
			return nil
		}
		return v
	}
	return *ptr
}

func timeParam(ptr *time.Time) any {
	if ptr == nil {
		return nil
	}
	return *ptr
}

func boolParam(ptr *bool) any {
	if ptr == nil {
		return nil
	}
	return *ptr
}

func float32Param(ptr *float32) any {
	if ptr == nil {
		return nil
	}
	return *ptr
}

type scanTarget interface {
	Scan(dest ...any) error
}

func scanTimeseriesBinding(scanner scanTarget) (*models.TimeseriesBinding, error) {
	var (
		binding   models.TimeseriesBinding
		influxOrg sql.NullString
		retention sql.NullString
	)
	if err := scanner.Scan(&binding.ID, &binding.StreamID, &influxOrg, &binding.InfluxBucket, &binding.Measurement, &retention, &binding.CreatedAt); err != nil {
		return nil, err
	}
	if influxOrg.Valid {
		v := influxOrg.String
		binding.InfluxOrg = &v
	}
	if retention.Valid {
		v := retention.String
		binding.RetentionHint = &v
	}
	return &binding, nil
}

func jsonParam(ptr *string) any {
	if ptr == nil {
		return nil
	}
	v := strings.TrimSpace(*ptr)
	if v == "" {
		return nil
	}
	return []byte(v)
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
func (r *Repo) CreateInvitation(ctx context.Context, orgID, orgRoleID string, email *string, ttlHours int, createdBy *string) (*models.OrgInvitation, error) {
	var (
		m          models.OrgInvitation
		emailVal   sql.NullString
		roleCode   sql.NullString
		usedAt     sql.NullTime
		revokedAt  sql.NullTime
		createdByU sql.NullString
	)
	roleID := orgRoleID
	if _, err := uuid.Parse(orgRoleID); err != nil {
		var resolved uuid.UUID
		if err := r.pool.QueryRow(ctx, `SELECT id FROM heartguard.org_roles WHERE code=$1`, orgRoleID).Scan(&resolved); err != nil {
			return nil, fmt.Errorf("org role not found: %w", err)
		}
		roleID = resolved.String()
	}
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_org_invitation_create($1, $2, $3, $4, $5)`,
		orgID, roleID, email, ttlHours, createdBy).
		Scan(&m.ID, &m.OrgID, &emailVal, &m.OrgRoleID, &roleCode, &m.Token, &m.ExpiresAt, &usedAt, &revokedAt, &createdByU, &m.CreatedAt, &m.Status)
	if err != nil {
		return nil, err
	}
	if emailVal.Valid {
		m.Email = &emailVal.String
	}
	if roleCode.Valid {
		m.OrgRoleCode = roleCode.String
	}
	if usedAt.Valid {
		t := usedAt.Time
		m.UsedAt = &t
	}
	if revokedAt.Valid {
		t := revokedAt.Time
		m.RevokedAt = &t
	}
	if createdByU.Valid {
		s := createdByU.String
		m.CreatedBy = &s
	}
	return &m, nil
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

func (r *Repo) ListInvitations(ctx context.Context, orgID *string, limit, offset int) ([]models.OrgInvitation, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_org_invitations_list($1, $2, $3)`, orgID, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.OrgInvitation, 0, limit)
	for rows.Next() {
		var (
			item       models.OrgInvitation
			emailVal   sql.NullString
			roleCode   sql.NullString
			usedAt     sql.NullTime
			revokedAt  sql.NullTime
			createdByU sql.NullString
		)
		if err := rows.Scan(
			&item.ID,
			&item.OrgID,
			&emailVal,
			&item.OrgRoleID,
			&roleCode,
			&item.Token,
			&item.ExpiresAt,
			&usedAt,
			&revokedAt,
			&createdByU,
			&item.CreatedAt,
			&item.Status,
		); err != nil {
			return nil, err
		}
		if emailVal.Valid {
			item.Email = &emailVal.String
		}
		if roleCode.Valid {
			item.OrgRoleCode = roleCode.String
		}
		if usedAt.Valid {
			t := usedAt.Time
			item.UsedAt = &t
		}
		if revokedAt.Valid {
			t := revokedAt.Time
			item.RevokedAt = &t
		}
		if createdByU.Valid {
			s := createdByU.String
			item.CreatedBy = &s
		}
		if item.Status == "" {
			item.Status = invitationStatus(&item, nowFn())
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) CancelInvitation(ctx context.Context, invitationID string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_org_invitation_cancel($1)`, invitationID).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Catalogs
// ------------------------------

func (r *Repo) ListCatalog(ctx context.Context, catalog string, limit, offset int) ([]models.CatalogItem, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_catalog_list($1, $2, $3)`, catalog, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.CatalogItem, 0, limit)
	for rows.Next() {
		var (
			item   models.CatalogItem
			label  sql.NullString
			weight sql.NullInt32
		)
		if err := rows.Scan(&item.ID, &item.Code, &label, &weight); err != nil {
			return nil, err
		}
		if label.Valid {
			item.Label = label.String
		}
		if weight.Valid {
			w := int(weight.Int32)
			item.Weight = &w
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) CreateCatalogItem(ctx context.Context, catalog, code, label string, weight *int) (*models.CatalogItem, error) {
	var (
		item models.CatalogItem
		lbl  sql.NullString
		wval sql.NullInt32
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_catalog_create($1, $2, $3, $4)`, catalog, code, label, weight).
		Scan(&item.ID, &item.Code, &lbl, &wval)
	if err != nil {
		return nil, err
	}
	if lbl.Valid {
		item.Label = lbl.String
	}
	if wval.Valid {
		v := int(wval.Int32)
		item.Weight = &v
	}
	return &item, nil
}

func (r *Repo) UpdateCatalogItem(ctx context.Context, catalog, id string, code, label *string, weight *int) (*models.CatalogItem, error) {
	var (
		item models.CatalogItem
		lbl  sql.NullString
		wval sql.NullInt32
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_catalog_update($1, $2, $3, $4, $5)`, catalog, id, code, label, weight).
		Scan(&item.ID, &item.Code, &lbl, &wval)
	if err != nil {
		return nil, err
	}
	if lbl.Valid {
		item.Label = lbl.String
	}
	if wval.Valid {
		v := int(wval.Int32)
		item.Weight = &v
	}
	return &item, nil
}

func (r *Repo) DeleteCatalogItem(ctx context.Context, catalog, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_catalog_delete($1, $2)`, catalog, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Patients
// ------------------------------

func (r *Repo) ListPatients(ctx context.Context, limit, offset int) ([]models.Patient, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_patients_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Patient, 0, limit)
	for rows.Next() {
		var (
			patient  models.Patient
			orgID    sql.NullString
			org      sql.NullString
			birth    sql.NullTime
			sexCode  sql.NullString
			sexLabel sql.NullString
			risk     sql.NullString
		)
		if err := rows.Scan(&patient.ID, &orgID, &org, &patient.Name, &birth, &sexCode, &sexLabel, &risk, &patient.CreatedAt); err != nil {
			return nil, err
		}
		if orgID.Valid {
			v := orgID.String
			patient.OrgID = &v
		}
		if org.Valid {
			v := org.String
			patient.OrgName = &v
		}
		if birth.Valid {
			bt := birth.Time
			patient.Birthdate = &bt
		}
		if sexCode.Valid {
			v := sexCode.String
			patient.SexCode = &v
		}
		if sexLabel.Valid {
			v := sexLabel.String
			patient.SexLabel = &v
		}
		if risk.Valid {
			v := risk.String
			patient.RiskLevel = &v
		}
		out = append(out, patient)
	}
	return out, rows.Err()
}

func (r *Repo) CreatePatient(ctx context.Context, input models.PatientInput) (*models.Patient, error) {
	var (
		patient  models.Patient
		orgID    sql.NullString
		org      sql.NullString
		birth    sql.NullTime
		sexCode  sql.NullString
		sexLabel sql.NullString
		risk     sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_patient_create($1, $2, $3, $4, $5)`, stringParam(input.OrgID, true), input.Name, timeParam(input.Birthdate), stringParam(input.SexCode, true), stringParam(input.RiskLevel, true)).
		Scan(&patient.ID, &orgID, &org, &patient.Name, &birth, &sexCode, &sexLabel, &risk, &patient.CreatedAt)
	if err != nil {
		return nil, err
	}
	if orgID.Valid {
		v := orgID.String
		patient.OrgID = &v
	}
	if org.Valid {
		v := org.String
		patient.OrgName = &v
	}
	if birth.Valid {
		bt := birth.Time
		patient.Birthdate = &bt
	}
	if sexCode.Valid {
		v := sexCode.String
		patient.SexCode = &v
	}
	if sexLabel.Valid {
		v := sexLabel.String
		patient.SexLabel = &v
	}
	if risk.Valid {
		v := risk.String
		patient.RiskLevel = &v
	}
	return &patient, nil
}

func (r *Repo) UpdatePatient(ctx context.Context, id string, input models.PatientInput) (*models.Patient, error) {
	var (
		patient  models.Patient
		orgID    sql.NullString
		org      sql.NullString
		birth    sql.NullTime
		sexCode  sql.NullString
		sexLabel sql.NullString
		risk     sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_patient_update($1, $2, $3, $4, $5, $6)`, id, stringParam(input.OrgID, true), input.Name, timeParam(input.Birthdate), stringParam(input.SexCode, true), stringParam(input.RiskLevel, true)).
		Scan(&patient.ID, &orgID, &org, &patient.Name, &birth, &sexCode, &sexLabel, &risk, &patient.CreatedAt)
	if err != nil {
		return nil, err
	}
	if orgID.Valid {
		v := orgID.String
		patient.OrgID = &v
	}
	if org.Valid {
		v := org.String
		patient.OrgName = &v
	}
	if birth.Valid {
		bt := birth.Time
		patient.Birthdate = &bt
	}
	if sexCode.Valid {
		v := sexCode.String
		patient.SexCode = &v
	}
	if sexLabel.Valid {
		v := sexLabel.String
		patient.SexLabel = &v
	}
	if risk.Valid {
		v := risk.String
		patient.RiskLevel = &v
	}
	return &patient, nil
}

func (r *Repo) DeletePatient(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_patient_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Push devices
// ------------------------------

func (r *Repo) ListPushDevices(ctx context.Context, userID, platformCode *string, limit, offset int) ([]models.PushDevice, error) {
	where := "WHERE 1=1"
	args := make([]any, 0, 4)
	idx := 1

	if userID != nil {
		if v := strings.TrimSpace(*userID); v != "" {
			where += fmt.Sprintf(" AND pd.user_id = $%d", idx)
			args = append(args, v)
			idx++
		}
	}
	if platformCode != nil {
		if v := strings.TrimSpace(*platformCode); v != "" {
			where += fmt.Sprintf(" AND p.code = $%d", idx)
			args = append(args, v)
			idx++
		}
	}

	query := fmt.Sprintf(`
SELECT
  pd.id::text,
  pd.user_id::text,
  u.name,
  u.email,
  p.code,
  p.label,
  pd.push_token,
  pd.last_seen_at,
  pd.active
FROM push_devices pd
JOIN users u ON u.id = pd.user_id
JOIN platforms p ON p.id = pd.platform_id
%s
ORDER BY pd.last_seen_at DESC
LIMIT $%d OFFSET $%d
`, where, idx, idx+1)

	args = append(args, limit, offset)

	rows, err := r.pool.Query(ctx, query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.PushDevice, 0, limit)
	for rows.Next() {
		var item models.PushDevice
		if err := rows.Scan(
			&item.ID,
			&item.UserID,
			&item.UserName,
			&item.UserEmail,
			&item.PlatformCode,
			&item.PlatformLabel,
			&item.PushToken,
			&item.LastSeenAt,
			&item.Active,
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

func (r *Repo) CreatePushDevice(ctx context.Context, input models.PushDeviceInput) (*models.PushDevice, error) {
	userID := strings.TrimSpace(input.UserID)
	platformCode := strings.TrimSpace(input.PlatformCode)
	token := strings.TrimSpace(input.PushToken)

	var item models.PushDevice
	err := r.pool.QueryRow(ctx, `
WITH platform AS (
  SELECT id, code, label
  FROM platforms
  WHERE code = $2
), inserted AS (
  INSERT INTO push_devices (user_id, platform_id, push_token, last_seen_at, active)
  SELECT $1::uuid, platform.id, $3, COALESCE($4, NOW()), COALESCE($5::bool, TRUE)
  FROM platform
  RETURNING id, user_id, platform_id, push_token, last_seen_at, active
)
SELECT
  ins.id::text,
  ins.user_id::text,
  u.name,
  u.email,
  p.code,
  p.label,
  ins.push_token,
  ins.last_seen_at,
  ins.active
FROM inserted ins
JOIN users u ON u.id = ins.user_id
JOIN platforms p ON p.id = ins.platform_id
`, userID, platformCode, token, timeParam(input.LastSeenAt), boolParam(input.Active)).Scan(
		&item.ID,
		&item.UserID,
		&item.UserName,
		&item.UserEmail,
		&item.PlatformCode,
		&item.PlatformLabel,
		&item.PushToken,
		&item.LastSeenAt,
		&item.Active,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			var exists bool
			if checkErr := r.pool.QueryRow(ctx, `SELECT EXISTS (SELECT 1 FROM platforms WHERE code = $1)`, platformCode).Scan(&exists); checkErr != nil {
				return nil, checkErr
			}
			if !exists {
				return nil, errInvalidPlatform
			}
		}
		return nil, err
	}
	return &item, nil
}

func (r *Repo) UpdatePushDevice(ctx context.Context, id string, input models.PushDeviceInput) (*models.PushDevice, error) {
	userID := strings.TrimSpace(input.UserID)
	platformCode := strings.TrimSpace(input.PlatformCode)
	token := strings.TrimSpace(input.PushToken)

	var item models.PushDevice
	err := r.pool.QueryRow(ctx, `
WITH platform AS (
  SELECT id
  FROM platforms
  WHERE code = $2
), updated AS (
  UPDATE push_devices pd
  SET
    user_id = $1::uuid,
    platform_id = platform.id,
    push_token = $3,
    last_seen_at = COALESCE($4, pd.last_seen_at),
    active = COALESCE($5::bool, pd.active)
  FROM platform
  WHERE pd.id = $6::uuid
  RETURNING pd.id, pd.user_id, pd.platform_id, pd.push_token, pd.last_seen_at, pd.active
)
SELECT
  upd.id::text,
  upd.user_id::text,
  u.name,
  u.email,
  p.code,
  p.label,
  upd.push_token,
  upd.last_seen_at,
  upd.active
FROM updated upd
JOIN users u ON u.id = upd.user_id
JOIN platforms p ON p.id = upd.platform_id
`, userID, platformCode, token, timeParam(input.LastSeenAt), boolParam(input.Active), id).Scan(
		&item.ID,
		&item.UserID,
		&item.UserName,
		&item.UserEmail,
		&item.PlatformCode,
		&item.PlatformLabel,
		&item.PushToken,
		&item.LastSeenAt,
		&item.Active,
	)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			var exists bool
			if checkErr := r.pool.QueryRow(ctx, `SELECT EXISTS (SELECT 1 FROM platforms WHERE code = $1)`, platformCode).Scan(&exists); checkErr != nil {
				return nil, checkErr
			}
			if !exists {
				return nil, errInvalidPlatform
			}
		}
		return nil, err
	}
	return &item, nil
}

func (r *Repo) DeletePushDevice(ctx context.Context, id string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM push_devices WHERE id = $1`, id)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Devices
// ------------------------------

func (r *Repo) ListDevices(ctx context.Context, limit, offset int) ([]models.Device, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_devices_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Device, 0, limit)
	for rows.Next() {
		var (
			device    models.Device
			orgID     sql.NullString
			orgName   sql.NullString
			brand     sql.NullString
			model     sql.NullString
			ownerID   sql.NullString
			ownerName sql.NullString
		)
		if err := rows.Scan(&device.ID, &orgID, &orgName, &device.Serial, &brand, &model, &device.DeviceTypeCode, &device.DeviceTypeLabel, &ownerID, &ownerName, &device.RegisteredAt, &device.Active); err != nil {
			return nil, err
		}
		if orgID.Valid {
			v := orgID.String
			device.OrgID = &v
		}
		if orgName.Valid {
			v := orgName.String
			device.OrgName = &v
		}
		if brand.Valid {
			v := brand.String
			device.Brand = &v
		}
		if model.Valid {
			v := model.String
			device.Model = &v
		}
		if ownerID.Valid {
			v := ownerID.String
			device.OwnerPatientID = &v
		}
		if ownerName.Valid {
			v := ownerName.String
			device.OwnerPatientName = &v
		}
		out = append(out, device)
	}
	return out, rows.Err()
}

func (r *Repo) CreateDevice(ctx context.Context, input models.DeviceInput) (*models.Device, error) {
	var (
		device    models.Device
		orgID     sql.NullString
		orgName   sql.NullString
		brand     sql.NullString
		model     sql.NullString
		ownerID   sql.NullString
		ownerName sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_device_create($1, $2, $3, $4, $5, $6, $7)`, stringParam(input.OrgID, true), input.Serial, stringParam(input.Brand, true), stringParam(input.Model, true), input.DeviceTypeCode, stringParam(input.OwnerPatientID, true), boolParam(input.Active)).
		Scan(&device.ID, &orgID, &orgName, &device.Serial, &brand, &model, &device.DeviceTypeCode, &device.DeviceTypeLabel, &ownerID, &ownerName, &device.RegisteredAt, &device.Active)
	if err != nil {
		return nil, err
	}
	if orgID.Valid {
		v := orgID.String
		device.OrgID = &v
	}
	if orgName.Valid {
		v := orgName.String
		device.OrgName = &v
	}
	if brand.Valid {
		v := brand.String
		device.Brand = &v
	}
	if model.Valid {
		v := model.String
		device.Model = &v
	}
	if ownerID.Valid {
		v := ownerID.String
		device.OwnerPatientID = &v
	}
	if ownerName.Valid {
		v := ownerName.String
		device.OwnerPatientName = &v
	}
	return &device, nil
}

func (r *Repo) UpdateDevice(ctx context.Context, id string, input models.DeviceInput) (*models.Device, error) {
	var (
		device    models.Device
		orgID     sql.NullString
		orgName   sql.NullString
		brand     sql.NullString
		model     sql.NullString
		ownerID   sql.NullString
		ownerName sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_device_update($1, $2, $3, $4, $5, $6, $7, $8)`, id, stringParam(input.OrgID, true), input.Serial, stringParam(input.Brand, true), stringParam(input.Model, true), input.DeviceTypeCode, stringParam(input.OwnerPatientID, true), boolParam(input.Active)).
		Scan(&device.ID, &orgID, &orgName, &device.Serial, &brand, &model, &device.DeviceTypeCode, &device.DeviceTypeLabel, &ownerID, &ownerName, &device.RegisteredAt, &device.Active)
	if err != nil {
		return nil, err
	}
	if orgID.Valid {
		v := orgID.String
		device.OrgID = &v
	}
	if orgName.Valid {
		v := orgName.String
		device.OrgName = &v
	}
	if brand.Valid {
		v := brand.String
		device.Brand = &v
	}
	if model.Valid {
		v := model.String
		device.Model = &v
	}
	if ownerID.Valid {
		v := ownerID.String
		device.OwnerPatientID = &v
	}
	if ownerName.Valid {
		v := ownerName.String
		device.OwnerPatientName = &v
	}
	return &device, nil
}

func (r *Repo) DeleteDevice(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_device_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListDeviceTypes(ctx context.Context) ([]models.DeviceType, error) {
	rows, err := r.pool.Query(ctx, `SELECT id::text, code, description FROM heartguard.device_types ORDER BY code`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []models.DeviceType
	for rows.Next() {
		var (
			d    models.DeviceType
			desc sql.NullString
		)
		if err := rows.Scan(&d.ID, &d.Code, &desc); err != nil {
			return nil, err
		}
		if desc.Valid {
			v := desc.String
			d.Description = &v
		}
		out = append(out, d)
	}
	return out, rows.Err()
}

// ------------------------------
// Signal streams
// ------------------------------

func (r *Repo) ListSignalStreams(ctx context.Context, limit, offset int) ([]models.SignalStream, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_signal_streams_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.SignalStream, 0, limit)
	for rows.Next() {
		var (
			stream models.SignalStream
			ended  sql.NullTime
		)
		if err := rows.Scan(&stream.ID, &stream.PatientID, &stream.PatientName, &stream.DeviceID, &stream.DeviceSerial, &stream.SignalType, &stream.SignalLabel, &stream.SampleRateHz, &stream.StartedAt, &ended); err != nil {
			return nil, err
		}
		if ended.Valid {
			et := ended.Time
			stream.EndedAt = &et
		}
		out = append(out, stream)
	}
	return out, rows.Err()
}

func (r *Repo) CreateSignalStream(ctx context.Context, input models.SignalStreamInput) (*models.SignalStream, error) {
	var (
		stream models.SignalStream
		ended  sql.NullTime
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_signal_stream_create($1, $2, $3, $4, $5, $6)`, input.PatientID, input.DeviceID, input.SignalType, input.SampleRateHz, input.StartedAt, timeParam(input.EndedAt)).
		Scan(&stream.ID, &stream.PatientID, &stream.PatientName, &stream.DeviceID, &stream.DeviceSerial, &stream.SignalType, &stream.SignalLabel, &stream.SampleRateHz, &stream.StartedAt, &ended)
	if err != nil {
		return nil, err
	}
	if ended.Valid {
		et := ended.Time
		stream.EndedAt = &et
	}
	return &stream, nil
}

func (r *Repo) UpdateSignalStream(ctx context.Context, id string, input models.SignalStreamInput) (*models.SignalStream, error) {
	var (
		stream models.SignalStream
		ended  sql.NullTime
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_signal_stream_update($1, $2, $3, $4, $5, $6, $7)`, id, input.PatientID, input.DeviceID, input.SignalType, input.SampleRateHz, input.StartedAt, timeParam(input.EndedAt)).
		Scan(&stream.ID, &stream.PatientID, &stream.PatientName, &stream.DeviceID, &stream.DeviceSerial, &stream.SignalType, &stream.SignalLabel, &stream.SampleRateHz, &stream.StartedAt, &ended)
	if err != nil {
		return nil, err
	}
	if ended.Valid {
		et := ended.Time
		stream.EndedAt = &et
	}
	return &stream, nil
}

func (r *Repo) DeleteSignalStream(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_signal_stream_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListTimeseriesBindings(ctx context.Context, streamID string) ([]models.TimeseriesBinding, error) {
	rows, err := r.pool.Query(ctx, `
SELECT id, stream_id, influx_org, influx_bucket, measurement, retention_hint, created_at
FROM timeseries_binding
WHERE stream_id = $1
ORDER BY created_at DESC
`, streamID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.TimeseriesBinding
	for rows.Next() {
		binding, err := scanTimeseriesBinding(rows)
		if err != nil {
			return nil, err
		}
		tags, err := r.ListTimeseriesBindingTags(ctx, binding.ID)
		if err != nil {
			return nil, err
		}
		binding.Tags = tags
		out = append(out, *binding)
	}
	return out, rows.Err()
}

func (r *Repo) CreateTimeseriesBinding(ctx context.Context, streamID string, input models.TimeseriesBindingInput) (*models.TimeseriesBinding, error) {
	row := r.pool.QueryRow(ctx, `
INSERT INTO timeseries_binding (stream_id, influx_org, influx_bucket, measurement, retention_hint)
VALUES ($1, $2, $3, $4, $5)
RETURNING id, stream_id, influx_org, influx_bucket, measurement, retention_hint, created_at
`, streamID, stringParam(input.InfluxOrg, true), input.InfluxBucket, input.Measurement, stringParam(input.RetentionHint, true))
	binding, err := scanTimeseriesBinding(row)
	if err != nil {
		return nil, err
	}
	binding.Tags = []models.TimeseriesBindingTag{}
	return binding, nil
}

func (r *Repo) UpdateTimeseriesBinding(ctx context.Context, id string, input models.TimeseriesBindingUpdateInput) (*models.TimeseriesBinding, error) {
	row := r.pool.QueryRow(ctx, `
UPDATE timeseries_binding SET
  influx_org = COALESCE($2, influx_org),
  influx_bucket = COALESCE($3, influx_bucket),
  measurement = COALESCE($4, measurement),
  retention_hint = COALESCE($5, retention_hint)
WHERE id = $1
RETURNING id, stream_id, influx_org, influx_bucket, measurement, retention_hint, created_at
`, id, stringParam(input.InfluxOrg, true), stringParam(input.InfluxBucket, true), stringParam(input.Measurement, true), stringParam(input.RetentionHint, true))
	binding, err := scanTimeseriesBinding(row)
	if err != nil {
		return nil, err
	}
	tags, err := r.ListTimeseriesBindingTags(ctx, binding.ID)
	if err != nil {
		return nil, err
	}
	binding.Tags = tags
	return binding, nil
}

func (r *Repo) DeleteTimeseriesBinding(ctx context.Context, id string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM timeseries_binding WHERE id = $1`, id)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListTimeseriesBindingTags(ctx context.Context, bindingID string) ([]models.TimeseriesBindingTag, error) {
	rows, err := r.pool.Query(ctx, `
SELECT id, binding_id, tag_key, tag_value
FROM timeseries_binding_tag
WHERE binding_id = $1
ORDER BY tag_key ASC
`, bindingID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.TimeseriesBindingTag
	for rows.Next() {
		var tag models.TimeseriesBindingTag
		if err := rows.Scan(&tag.ID, &tag.BindingID, &tag.TagKey, &tag.TagValue); err != nil {
			return nil, err
		}
		out = append(out, tag)
	}
	return out, rows.Err()
}

func (r *Repo) CreateTimeseriesBindingTag(ctx context.Context, bindingID string, input models.TimeseriesBindingTagInput) (*models.TimeseriesBindingTag, error) {
	var tag models.TimeseriesBindingTag
	err := r.pool.QueryRow(ctx, `
INSERT INTO timeseries_binding_tag (binding_id, tag_key, tag_value)
VALUES ($1, $2, $3)
RETURNING id, binding_id, tag_key, tag_value
`, bindingID, input.TagKey, input.TagValue).Scan(&tag.ID, &tag.BindingID, &tag.TagKey, &tag.TagValue)
	if err != nil {
		return nil, err
	}
	return &tag, nil
}

func (r *Repo) UpdateTimeseriesBindingTag(ctx context.Context, id string, input models.TimeseriesBindingTagUpdateInput) (*models.TimeseriesBindingTag, error) {
	var tag models.TimeseriesBindingTag
	err := r.pool.QueryRow(ctx, `
UPDATE timeseries_binding_tag SET
  tag_key = COALESCE($2, tag_key),
  tag_value = COALESCE($3, tag_value)
WHERE id = $1
RETURNING id, binding_id, tag_key, tag_value
`, id, stringParam(input.TagKey, true), stringParam(input.TagValue, true)).Scan(&tag.ID, &tag.BindingID, &tag.TagKey, &tag.TagValue)
	if err != nil {
		return nil, err
	}
	return &tag, nil
}

func (r *Repo) DeleteTimeseriesBindingTag(ctx context.Context, id string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM timeseries_binding_tag WHERE id = $1`, id)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// ML Models
// ------------------------------

func (r *Repo) ListModels(ctx context.Context, limit, offset int) ([]models.MLModel, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_models_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.MLModel, 0, limit)
	for rows.Next() {
		var (
			model    models.MLModel
			training sql.NullString
			hparams  sql.NullString
		)
		if err := rows.Scan(&model.ID, &model.Name, &model.Version, &model.Task, &training, &hparams, &model.CreatedAt); err != nil {
			return nil, err
		}
		if training.Valid {
			v := training.String
			model.TrainingDataRef = &v
		}
		if hparams.Valid {
			v := hparams.String
			model.Hyperparams = &v
		}
		out = append(out, model)
	}
	return out, rows.Err()
}

func (r *Repo) CreateModel(ctx context.Context, input models.MLModelInput) (*models.MLModel, error) {
	var (
		model    models.MLModel
		training sql.NullString
		hparams  sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_model_create($1, $2, $3, $4, $5)`, input.Name, input.Version, input.Task, stringParam(input.TrainingDataRef, true), jsonParam(input.Hyperparams)).
		Scan(&model.ID, &model.Name, &model.Version, &model.Task, &training, &hparams, &model.CreatedAt)
	if err != nil {
		return nil, err
	}
	if training.Valid {
		v := training.String
		model.TrainingDataRef = &v
	}
	if hparams.Valid {
		v := hparams.String
		model.Hyperparams = &v
	}
	return &model, nil
}

func (r *Repo) UpdateModel(ctx context.Context, id string, input models.MLModelInput) (*models.MLModel, error) {
	var (
		model    models.MLModel
		training sql.NullString
		hparams  sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_model_update($1, $2, $3, $4, $5, $6)`, id, input.Name, input.Version, input.Task, stringParam(input.TrainingDataRef, true), jsonParam(input.Hyperparams)).
		Scan(&model.ID, &model.Name, &model.Version, &model.Task, &training, &hparams, &model.CreatedAt)
	if err != nil {
		return nil, err
	}
	if training.Valid {
		v := training.String
		model.TrainingDataRef = &v
	}
	if hparams.Valid {
		v := hparams.String
		model.Hyperparams = &v
	}
	return &model, nil
}

func (r *Repo) DeleteModel(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_model_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Event types
// ------------------------------

func (r *Repo) ListEventTypes(ctx context.Context, limit, offset int) ([]models.EventType, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_event_types_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.EventType, 0, limit)
	for rows.Next() {
		var (
			et       models.EventType
			desc     sql.NullString
			sevLabel sql.NullString
		)
		if err := rows.Scan(&et.ID, &et.Code, &desc, &et.SeverityDefault, &sevLabel); err != nil {
			return nil, err
		}
		if desc.Valid {
			v := desc.String
			et.Description = &v
		}
		if sevLabel.Valid {
			et.SeverityDefaultLabel = sevLabel.String
		}
		out = append(out, et)
	}
	return out, rows.Err()
}

func (r *Repo) CreateEventType(ctx context.Context, input models.EventTypeInput) (*models.EventType, error) {
	var (
		et       models.EventType
		desc     sql.NullString
		sevLabel sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_event_type_create($1, $2, $3)`, input.Code, stringParam(input.Description, true), input.SeverityDefault).
		Scan(&et.ID, &et.Code, &desc, &et.SeverityDefault, &sevLabel)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		v := desc.String
		et.Description = &v
	}
	if sevLabel.Valid {
		et.SeverityDefaultLabel = sevLabel.String
	}
	return &et, nil
}

func (r *Repo) UpdateEventType(ctx context.Context, id string, input models.EventTypeInput) (*models.EventType, error) {
	var (
		et       models.EventType
		desc     sql.NullString
		sevLabel sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_event_type_update($1, $2, $3, $4)`, id, input.Code, stringParam(input.Description, true), input.SeverityDefault).
		Scan(&et.ID, &et.Code, &desc, &et.SeverityDefault, &sevLabel)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		v := desc.String
		et.Description = &v
	}
	if sevLabel.Valid {
		et.SeverityDefaultLabel = sevLabel.String
	}
	return &et, nil
}

func (r *Repo) DeleteEventType(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_event_type_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Inferences
// ------------------------------

func (r *Repo) ListInferences(ctx context.Context, limit, offset int) ([]models.Inference, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_inferences_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Inference, 0, limit)
	for rows.Next() {
		var (
			inf          models.Inference
			modelName    sql.NullString
			patName      sql.NullString
			deviceSerial sql.NullString
			score        sql.NullFloat64
			threshold    sql.NullFloat64
			seriesRef    sql.NullString
		)
		if err := rows.Scan(&inf.ID, &inf.ModelID, &modelName, &inf.StreamID, &patName, &deviceSerial, &inf.EventCode, &inf.EventLabel, &inf.WindowStart, &inf.WindowEnd, &score, &threshold, &inf.CreatedAt, &seriesRef); err != nil {
			return nil, err
		}
		if modelName.Valid {
			v := modelName.String
			inf.ModelName = &v
		}
		if patName.Valid {
			inf.PatientName = patName.String
		}
		if deviceSerial.Valid {
			inf.DeviceSerial = deviceSerial.String
		}
		if score.Valid {
			v := float32(score.Float64)
			inf.Score = &v
		}
		if threshold.Valid {
			v := float32(threshold.Float64)
			inf.Threshold = &v
		}
		if seriesRef.Valid {
			v := seriesRef.String
			inf.SeriesRef = &v
		}
		labelParts := strings.TrimSpace(inf.PatientName)
		if labelParts != "" {
			inf.StreamLabel = labelParts
		}
		if inf.DeviceSerial != "" {
			if inf.StreamLabel != "" {
				inf.StreamLabel = fmt.Sprintf("%s · %s", inf.StreamLabel, inf.DeviceSerial)
			} else {
				inf.StreamLabel = inf.DeviceSerial
			}
		}
		if inf.StreamLabel == "" {
			inf.StreamLabel = inf.StreamID
		}
		out = append(out, inf)
	}
	return out, rows.Err()
}

func (r *Repo) CreateInference(ctx context.Context, input models.InferenceInput) (*models.Inference, error) {
	var (
		inf          models.Inference
		modelName    sql.NullString
		patName      sql.NullString
		deviceSerial sql.NullString
		score        sql.NullFloat64
		threshold    sql.NullFloat64
		seriesRef    sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_inference_create($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)`, stringParam(input.ModelID, true), input.StreamID, input.WindowStart, input.WindowEnd, input.EventCode, float32Param(input.Score), float32Param(input.Threshold), jsonParam(input.Metadata), stringParam(input.SeriesRef, true), jsonParam(input.FeatureSnapshot)).
		Scan(&inf.ID, &inf.ModelID, &modelName, &inf.StreamID, &patName, &deviceSerial, &inf.EventCode, &inf.EventLabel, &inf.WindowStart, &inf.WindowEnd, &score, &threshold, &inf.CreatedAt, &seriesRef)
	if err != nil {
		return nil, err
	}
	if modelName.Valid {
		v := modelName.String
		inf.ModelName = &v
	}
	if patName.Valid {
		inf.PatientName = patName.String
	}
	if deviceSerial.Valid {
		inf.DeviceSerial = deviceSerial.String
	}
	if score.Valid {
		v := float32(score.Float64)
		inf.Score = &v
	}
	if threshold.Valid {
		v := float32(threshold.Float64)
		inf.Threshold = &v
	}
	if seriesRef.Valid {
		v := seriesRef.String
		inf.SeriesRef = &v
	}
	if inf.PatientName != "" && inf.DeviceSerial != "" {
		inf.StreamLabel = fmt.Sprintf("%s · %s", inf.PatientName, inf.DeviceSerial)
	} else if inf.PatientName != "" {
		inf.StreamLabel = inf.PatientName
	} else if inf.DeviceSerial != "" {
		inf.StreamLabel = inf.DeviceSerial
	} else {
		inf.StreamLabel = inf.StreamID
	}
	return &inf, nil
}

func (r *Repo) UpdateInference(ctx context.Context, id string, input models.InferenceInput) (*models.Inference, error) {
	var (
		inf          models.Inference
		modelName    sql.NullString
		patName      sql.NullString
		deviceSerial sql.NullString
		score        sql.NullFloat64
		threshold    sql.NullFloat64
		seriesRef    sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_inference_update($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)`, id, stringParam(input.ModelID, true), input.StreamID, input.WindowStart, input.WindowEnd, input.EventCode, float32Param(input.Score), float32Param(input.Threshold), jsonParam(input.Metadata), stringParam(input.SeriesRef, true), jsonParam(input.FeatureSnapshot)).
		Scan(&inf.ID, &inf.ModelID, &modelName, &inf.StreamID, &patName, &deviceSerial, &inf.EventCode, &inf.EventLabel, &inf.WindowStart, &inf.WindowEnd, &score, &threshold, &inf.CreatedAt, &seriesRef)
	if err != nil {
		return nil, err
	}
	if modelName.Valid {
		v := modelName.String
		inf.ModelName = &v
	}
	if patName.Valid {
		inf.PatientName = patName.String
	}
	if deviceSerial.Valid {
		inf.DeviceSerial = deviceSerial.String
	}
	if score.Valid {
		v := float32(score.Float64)
		inf.Score = &v
	}
	if threshold.Valid {
		v := float32(threshold.Float64)
		inf.Threshold = &v
	}
	if seriesRef.Valid {
		v := seriesRef.String
		inf.SeriesRef = &v
	}
	if inf.PatientName != "" && inf.DeviceSerial != "" {
		inf.StreamLabel = fmt.Sprintf("%s · %s", inf.PatientName, inf.DeviceSerial)
	} else if inf.PatientName != "" {
		inf.StreamLabel = inf.PatientName
	} else if inf.DeviceSerial != "" {
		inf.StreamLabel = inf.DeviceSerial
	} else {
		inf.StreamLabel = inf.StreamID
	}
	return &inf, nil
}

func (r *Repo) DeleteInference(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_inference_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Alerts
// ------------------------------

func (r *Repo) ListAlerts(ctx context.Context, limit, offset int) ([]models.Alert, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_alerts_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Alert, 0, limit)
	for rows.Next() {
		var (
			alert   models.Alert
			orgID   sql.NullString
			orgName sql.NullString
			desc    sql.NullString
		)
		if err := rows.Scan(&alert.ID, &orgID, &orgName, &alert.PatientID, &alert.PatientName, &alert.AlertTypeCode, &alert.AlertTypeLabel, &alert.LevelCode, &alert.LevelLabel, &alert.StatusCode, &alert.StatusLabel, &alert.CreatedAt, &desc); err != nil {
			return nil, err
		}
		if orgID.Valid {
			v := orgID.String
			alert.OrgID = &v
		}
		if orgName.Valid {
			v := orgName.String
			alert.OrgName = &v
		}
		if desc.Valid {
			v := desc.String
			alert.Description = &v
		}
		out = append(out, alert)
	}
	return out, rows.Err()
}

func (r *Repo) CreateAlert(ctx context.Context, patientID string, input models.AlertInput) (*models.Alert, error) {
	var (
		alert   models.Alert
		orgID   sql.NullString
		orgName sql.NullString
		desc    sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_alert_create($1, $2, $3, $4, $5, $6, $7, $8)`, patientID, input.AlertType, input.AlertLevel, input.Status, stringParam(input.ModelID, true), stringParam(input.InferenceID, true), stringParam(input.Description, true), stringParam(input.LocationWKT, true)).
		Scan(&alert.ID, &orgID, &orgName, &alert.PatientID, &alert.PatientName, &alert.AlertTypeCode, &alert.AlertTypeLabel, &alert.LevelCode, &alert.LevelLabel, &alert.StatusCode, &alert.StatusLabel, &alert.CreatedAt, &desc)
	if err != nil {
		return nil, err
	}
	if orgID.Valid {
		v := orgID.String
		alert.OrgID = &v
	}
	if orgName.Valid {
		v := orgName.String
		alert.OrgName = &v
	}
	if desc.Valid {
		v := desc.String
		alert.Description = &v
	}
	return &alert, nil
}

func (r *Repo) UpdateAlert(ctx context.Context, id string, input models.AlertInput) (*models.Alert, error) {
	var (
		alert   models.Alert
		orgID   sql.NullString
		orgName sql.NullString
		desc    sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_alert_update($1, $2, $3, $4, $5, $6, $7, $8)`, id, input.AlertType, input.AlertLevel, input.Status, stringParam(input.ModelID, true), stringParam(input.InferenceID, true), stringParam(input.Description, true), stringParam(input.LocationWKT, true)).
		Scan(&alert.ID, &orgID, &orgName, &alert.PatientID, &alert.PatientName, &alert.AlertTypeCode, &alert.AlertTypeLabel, &alert.LevelCode, &alert.LevelLabel, &alert.StatusCode, &alert.StatusLabel, &alert.CreatedAt, &desc)
	if err != nil {
		return nil, err
	}
	if orgID.Valid {
		v := orgID.String
		alert.OrgID = &v
	}
	if orgName.Valid {
		v := orgName.String
		alert.OrgName = &v
	}
	if desc.Valid {
		v := desc.String
		alert.Description = &v
	}
	return &alert, nil
}

func (r *Repo) DeleteAlert(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_alert_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListAlertTypes(ctx context.Context) ([]models.AlertType, error) {
	rows, err := r.pool.Query(ctx, `SELECT id::text, code, description FROM heartguard.alert_types ORDER BY code`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []models.AlertType
	for rows.Next() {
		var (
			at   models.AlertType
			desc sql.NullString
		)
		if err := rows.Scan(&at.ID, &at.Code, &desc); err != nil {
			return nil, err
		}
		if desc.Valid {
			v := desc.String
			at.Description = &v
		}
		out = append(out, at)
	}
	return out, rows.Err()
}

func (r *Repo) ListAlertStatuses(ctx context.Context) ([]models.AlertStatus, error) {
	rows, err := r.pool.Query(ctx, `SELECT id::text, code, description, step_order FROM heartguard.alert_status ORDER BY step_order, code`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var out []models.AlertStatus
	for rows.Next() {
		var status models.AlertStatus
		if err := rows.Scan(&status.ID, &status.Code, &status.Description, &status.StepOrder); err != nil {
			return nil, err
		}
		out = append(out, status)
	}
	return out, rows.Err()
}

func (r *Repo) ListAlertAssignments(ctx context.Context, alertID string) ([]models.AlertAssignment, error) {
	rows, err := r.pool.Query(ctx, `
SELECT aa.alert_id::text,
       aa.assignee_user_id::text,
       assignee.name,
       aa.assigned_by_user_id::text,
       assigned_by.name,
       aa.assigned_at
FROM heartguard.alert_assignment aa
LEFT JOIN heartguard.users assignee ON assignee.id = aa.assignee_user_id
LEFT JOIN heartguard.users assigned_by ON assigned_by.id = aa.assigned_by_user_id
WHERE aa.alert_id = $1
ORDER BY aa.assigned_at DESC
`, alertID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.AlertAssignment
	for rows.Next() {
		var (
			assignment     models.AlertAssignment
			assigneeName   sql.NullString
			assignedByID   sql.NullString
			assignedByName sql.NullString
		)
		if err := rows.Scan(&assignment.AlertID, &assignment.AssigneeUserID, &assigneeName, &assignedByID, &assignedByName, &assignment.AssignedAt); err != nil {
			return nil, err
		}
		if assigneeName.Valid {
			name := assigneeName.String
			assignment.AssigneeName = &name
		}
		if assignedByID.Valid {
			id := assignedByID.String
			assignment.AssignedByUserID = &id
		}
		if assignedByName.Valid {
			name := assignedByName.String
			assignment.AssignedByName = &name
		}
		out = append(out, assignment)
	}
	return out, rows.Err()
}

func (r *Repo) CreateAlertAssignment(ctx context.Context, alertID, assigneeUserID string, assignedBy *string) (*models.AlertAssignment, error) {
	var (
		assignment     models.AlertAssignment
		assigneeName   sql.NullString
		assignedByID   sql.NullString
		assignedByName sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
INSERT INTO heartguard.alert_assignment (alert_id, assignee_user_id, assigned_by_user_id)
VALUES ($1, $2, $3)
RETURNING alert_id::text,
          assignee_user_id::text,
          (SELECT name FROM heartguard.users WHERE id = assignee_user_id),
          assigned_by_user_id::text,
          (SELECT name FROM heartguard.users WHERE id = assigned_by_user_id),
          assigned_at
`, alertID, assigneeUserID, stringParam(assignedBy, true)).
		Scan(&assignment.AlertID, &assignment.AssigneeUserID, &assigneeName, &assignedByID, &assignedByName, &assignment.AssignedAt)
	if err != nil {
		return nil, err
	}
	if assigneeName.Valid {
		name := assigneeName.String
		assignment.AssigneeName = &name
	}
	if assignedByID.Valid {
		id := assignedByID.String
		assignment.AssignedByUserID = &id
	}
	if assignedByName.Valid {
		name := assignedByName.String
		assignment.AssignedByName = &name
	}
	return &assignment, nil
}

func (r *Repo) ListAlertAcks(ctx context.Context, alertID string) ([]models.AlertAck, error) {
	rows, err := r.pool.Query(ctx, `
SELECT aa.id::text,
       aa.alert_id::text,
       aa.ack_by_user_id::text,
       ack_user.name,
       aa.ack_at,
       aa.note
FROM heartguard.alert_ack aa
LEFT JOIN heartguard.users ack_user ON ack_user.id = aa.ack_by_user_id
WHERE aa.alert_id = $1
ORDER BY aa.ack_at DESC
`, alertID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.AlertAck
	for rows.Next() {
		var (
			ack        models.AlertAck
			ackByID    sql.NullString
			ackByName  sql.NullString
			noteString sql.NullString
		)
		if err := rows.Scan(&ack.ID, &ack.AlertID, &ackByID, &ackByName, &ack.AckAt, &noteString); err != nil {
			return nil, err
		}
		if ackByID.Valid {
			id := ackByID.String
			ack.AckByUserID = &id
		}
		if ackByName.Valid {
			name := ackByName.String
			ack.AckByName = &name
		}
		if noteString.Valid {
			note := noteString.String
			ack.Note = &note
		}
		out = append(out, ack)
	}
	return out, rows.Err()
}

func (r *Repo) CreateAlertAck(ctx context.Context, alertID string, ackBy *string, note *string) (*models.AlertAck, error) {
	var (
		ack        models.AlertAck
		ackByID    sql.NullString
		ackByName  sql.NullString
		noteString sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
INSERT INTO heartguard.alert_ack (alert_id, ack_by_user_id, note)
VALUES ($1, $2, $3)
RETURNING id::text,
          alert_id::text,
          ack_by_user_id::text,
          (SELECT name FROM heartguard.users WHERE id = ack_by_user_id),
          ack_at,
          note
`, alertID, stringParam(ackBy, true), stringParam(note, true)).
		Scan(&ack.ID, &ack.AlertID, &ackByID, &ackByName, &ack.AckAt, &noteString)
	if err != nil {
		return nil, err
	}
	if ackByID.Valid {
		id := ackByID.String
		ack.AckByUserID = &id
	}
	if ackByName.Valid {
		name := ackByName.String
		ack.AckByName = &name
	}
	if noteString.Valid {
		noteVal := noteString.String
		ack.Note = &noteVal
	}
	return &ack, nil
}

func (r *Repo) ListAlertResolutions(ctx context.Context, alertID string) ([]models.AlertResolution, error) {
	rows, err := r.pool.Query(ctx, `
SELECT ar.id::text,
       ar.alert_id::text,
       ar.resolved_by_user_id::text,
       resolver.name,
       ar.resolved_at,
       ar.outcome,
       ar.note
FROM heartguard.alert_resolution ar
LEFT JOIN heartguard.users resolver ON resolver.id = ar.resolved_by_user_id
WHERE ar.alert_id = $1
ORDER BY ar.resolved_at DESC
`, alertID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.AlertResolution
	for rows.Next() {
		var (
			res          models.AlertResolution
			resolvedID   sql.NullString
			resolvedName sql.NullString
			outcomeStr   sql.NullString
			noteStr      sql.NullString
		)
		if err := rows.Scan(&res.ID, &res.AlertID, &resolvedID, &resolvedName, &res.ResolvedAt, &outcomeStr, &noteStr); err != nil {
			return nil, err
		}
		if resolvedID.Valid {
			id := resolvedID.String
			res.ResolvedByUserID = &id
		}
		if resolvedName.Valid {
			name := resolvedName.String
			res.ResolvedByName = &name
		}
		if outcomeStr.Valid {
			outcome := outcomeStr.String
			res.Outcome = &outcome
		}
		if noteStr.Valid {
			note := noteStr.String
			res.Note = &note
		}
		out = append(out, res)
	}
	return out, rows.Err()
}

func (r *Repo) CreateAlertResolution(ctx context.Context, alertID string, resolvedBy *string, outcome, note *string) (*models.AlertResolution, error) {
	var (
		res          models.AlertResolution
		resolvedID   sql.NullString
		resolvedName sql.NullString
		outcomeStr   sql.NullString
		noteStr      sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
INSERT INTO heartguard.alert_resolution (alert_id, resolved_by_user_id, outcome, note)
VALUES ($1, $2, $3, $4)
RETURNING id::text,
          alert_id::text,
          resolved_by_user_id::text,
          (SELECT name FROM heartguard.users WHERE id = resolved_by_user_id),
          resolved_at,
          outcome,
          note
`, alertID, stringParam(resolvedBy, true), stringParam(outcome, true), stringParam(note, true)).
		Scan(&res.ID, &res.AlertID, &resolvedID, &resolvedName, &res.ResolvedAt, &outcomeStr, &noteStr)
	if err != nil {
		return nil, err
	}
	if resolvedID.Valid {
		id := resolvedID.String
		res.ResolvedByUserID = &id
	}
	if resolvedName.Valid {
		name := resolvedName.String
		res.ResolvedByName = &name
	}
	if outcomeStr.Valid {
		outcomeVal := outcomeStr.String
		res.Outcome = &outcomeVal
	}
	if noteStr.Valid {
		noteVal := noteStr.String
		res.Note = &noteVal
	}
	return &res, nil
}

func (r *Repo) ListAlertDeliveries(ctx context.Context, alertID string) ([]models.AlertDelivery, error) {
	rows, err := r.pool.Query(ctx, `
SELECT ad.id::text,
       ad.alert_id::text,
       ad.channel_id::text,
       ac.code,
       ac.label,
       ad.target,
       ad.sent_at,
       ad.delivery_status_id::text,
       ds.code,
       ds.label,
       ad.response_payload::text
FROM heartguard.alert_delivery ad
JOIN heartguard.alert_channels ac ON ac.id = ad.channel_id
JOIN heartguard.delivery_statuses ds ON ds.id = ad.delivery_status_id
WHERE ad.alert_id = $1
ORDER BY ad.sent_at DESC
`, alertID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.AlertDelivery
	for rows.Next() {
		var (
			delivery        models.AlertDelivery
			responsePayload sql.NullString
		)
		if err := rows.Scan(
			&delivery.ID,
			&delivery.AlertID,
			&delivery.ChannelID,
			&delivery.ChannelCode,
			&delivery.ChannelLabel,
			&delivery.Target,
			&delivery.SentAt,
			&delivery.DeliveryStatusID,
			&delivery.DeliveryStatusCode,
			&delivery.DeliveryStatusLabel,
			&responsePayload,
		); err != nil {
			return nil, err
		}
		if responsePayload.Valid {
			payload := responsePayload.String
			delivery.ResponsePayload = &payload
		}
		out = append(out, delivery)
	}
	return out, rows.Err()
}

func (r *Repo) CreateAlertDelivery(ctx context.Context, alertID, channelID, target, deliveryStatusID string, responsePayload *string) (*models.AlertDelivery, error) {
	var (
		delivery   models.AlertDelivery
		payloadStr sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
INSERT INTO heartguard.alert_delivery (alert_id, channel_id, target, delivery_status_id, response_payload)
VALUES ($1, $2, $3, $4, $5)
RETURNING id::text,
          alert_id::text,
          channel_id::text,
          (SELECT code FROM heartguard.alert_channels WHERE id = channel_id),
          (SELECT label FROM heartguard.alert_channels WHERE id = channel_id),
          target,
          sent_at,
          delivery_status_id::text,
          (SELECT code FROM heartguard.delivery_statuses WHERE id = delivery_status_id),
          (SELECT label FROM heartguard.delivery_statuses WHERE id = delivery_status_id),
          response_payload::text
`, alertID, channelID, target, deliveryStatusID, jsonParam(responsePayload)).
		Scan(
			&delivery.ID,
			&delivery.AlertID,
			&delivery.ChannelID,
			&delivery.ChannelCode,
			&delivery.ChannelLabel,
			&delivery.Target,
			&delivery.SentAt,
			&delivery.DeliveryStatusID,
			&delivery.DeliveryStatusCode,
			&delivery.DeliveryStatusLabel,
			&payloadStr,
		)
	if err != nil {
		return nil, err
	}
	if payloadStr.Valid {
		payload := payloadStr.String
		delivery.ResponsePayload = &payload
	}
	return &delivery, nil
}

func (r *Repo) ListContentBlockTypes(ctx context.Context, limit, offset int) ([]models.ContentBlockType, error) {
	if limit <= 0 {
		limit = 100
	} else if limit > 200 {
		limit = 200
	}
	if offset < 0 {
		offset = 0
	}

	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_content_block_types_list($1, $2)`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.ContentBlockType, 0, limit)
	for rows.Next() {
		var (
			bt   models.ContentBlockType
			desc sql.NullString
		)
		if err := rows.Scan(&bt.ID, &bt.Code, &bt.Label, &desc); err != nil {
			return nil, err
		}
		if desc.Valid {
			d := desc.String
			bt.Description = &d
		}
		out = append(out, bt)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) CreateContentBlockType(ctx context.Context, code, label string, description *string) (*models.ContentBlockType, error) {
	var (
		bt   models.ContentBlockType
		desc sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_content_block_type_create($1, $2, $3)`, code, label, description).
		Scan(&bt.ID, &bt.Code, &bt.Label, &desc)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		d := desc.String
		bt.Description = &d
	}
	return &bt, nil
}

func (r *Repo) UpdateContentBlockType(ctx context.Context, id string, code, label, description *string) (*models.ContentBlockType, error) {
	var (
		bt   models.ContentBlockType
		desc sql.NullString
	)
	err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_content_block_type_update($1, $2, $3, $4)`, id, code, label, description).
		Scan(&bt.ID, &bt.Code, &bt.Label, &desc)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		d := desc.String
		bt.Description = &d
	}
	return &bt, nil
}

func (r *Repo) DeleteContentBlockType(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_content_block_type_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// Content
// ------------------------------

func (r *Repo) ListContent(ctx context.Context, filters models.ContentFilters) ([]models.ContentItem, error) {
	limit := filters.Limit
	if limit <= 0 {
		limit = 50
	} else if limit > 200 {
		limit = 200
	}
	offset := filters.Offset
	if offset < 0 {
		offset = 0
	}

	var typeCode any
	if filters.TypeCode != nil {
		if trimmed := strings.TrimSpace(*filters.TypeCode); trimmed != "" {
			typeCode = strings.ToLower(trimmed)
		}
	}
	var statusCode any
	if filters.StatusCode != nil {
		if trimmed := strings.TrimSpace(*filters.StatusCode); trimmed != "" {
			statusCode = strings.ToLower(trimmed)
		}
	}
	var categoryCode any
	if filters.CategoryCode != nil {
		if trimmed := strings.TrimSpace(*filters.CategoryCode); trimmed != "" {
			categoryCode = strings.ToLower(trimmed)
		}
	}
	var search any
	if filters.Search != nil {
		if trimmed := strings.TrimSpace(*filters.Search); trimmed != "" {
			search = trimmed
		}
	}

	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_content_list($1, $2, $3, $4, $5, $6)`,
		typeCode, statusCode, categoryCode, search, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.ContentItem, 0, limit)
	for rows.Next() {
		var (
			item            models.ContentItem
			statusCodeVal   string
			statusLabel     string
			statusWeight    int32
			categoryCodeVal string
			categoryLabel   string
			typeCodeVal     string
			typeLabel       string
			authorName      sql.NullString
			authorEmail     sql.NullString
			publishedAt     sql.NullTime
		)
		if err := rows.Scan(
			&item.ID,
			&item.Title,
			&statusCodeVal,
			&statusLabel,
			&statusWeight,
			&categoryCodeVal,
			&categoryLabel,
			&typeCodeVal,
			&typeLabel,
			&authorName,
			&authorEmail,
			&item.UpdatedAt,
			&publishedAt,
			&item.CreatedAt,
		); err != nil {
			return nil, err
		}
		item.StatusCode = strings.ToLower(statusCodeVal)
		item.StatusLabel = statusLabel
		item.StatusWeight = int(statusWeight)
		item.CategoryCode = strings.ToLower(categoryCodeVal)
		item.CategoryLabel = categoryLabel
		item.TypeCode = strings.ToLower(typeCodeVal)
		item.TypeLabel = typeLabel
		if authorName.Valid {
			name := authorName.String
			item.AuthorName = &name
		}
		if authorEmail.Valid {
			email := authorEmail.String
			item.AuthorEmail = &email
		}
		if publishedAt.Valid {
			t := publishedAt.Time
			item.PublishedAt = &t
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) GetContent(ctx context.Context, id string) (*models.ContentDetail, error) {
	row := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_content_detail($1)`, id)
	return scanContentDetail(row)
}

func (r *Repo) CreateContent(ctx context.Context, input models.ContentCreateInput, actorID *string) (*models.ContentDetail, error) {
	blocksJSON, err := contentBlocksToJSON(input.Blocks)
	if err != nil {
		return nil, err
	}
	var summaryParam any
	if input.Summary != nil {
		if trimmed := strings.TrimSpace(*input.Summary); trimmed != "" {
			summaryParam = trimmed
		}
	}
	var slugParam any
	if input.Slug != nil {
		if trimmed := strings.TrimSpace(*input.Slug); trimmed != "" {
			slugParam = trimmed
		}
	}
	var localeParam any
	if input.Locale != nil {
		if trimmed := strings.TrimSpace(*input.Locale); trimmed != "" {
			localeParam = trimmed
		}
	}
	var authorParam any
	if input.AuthorEmail != nil {
		if trimmed := strings.TrimSpace(*input.AuthorEmail); trimmed != "" {
			authorParam = trimmed
		}
	}
	var noteParam any
	if input.Note != nil {
		if trimmed := strings.TrimSpace(*input.Note); trimmed != "" {
			noteParam = trimmed
		}
	}
	var publishedAtParam any
	if input.PublishedAt != nil {
		publishedAtParam = *input.PublishedAt
	}
	var actorParam any
	if actorID != nil {
		if trimmed := strings.TrimSpace(*actorID); trimmed != "" {
			actorParam = trimmed
		}
	}

	row := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_content_create($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)`,
		input.Title,
		strings.ToLower(strings.TrimSpace(input.StatusCode)),
		strings.ToLower(strings.TrimSpace(input.CategoryCode)),
		strings.ToLower(strings.TrimSpace(input.TypeCode)),
		summaryParam,
		slugParam,
		localeParam,
		authorParam,
		input.Body,
		blocksJSON,
		actorParam,
		noteParam,
		publishedAtParam,
	)
	return scanContentDetail(row)
}

func (r *Repo) UpdateContent(ctx context.Context, id string, input models.ContentUpdateInput, actorID *string) (*models.ContentDetail, error) {
	blocksJSON, err := contentBlocksToJSON(input.Blocks)
	if err != nil {
		return nil, err
	}
	var titleParam any
	if input.Title != nil {
		if trimmed := strings.TrimSpace(*input.Title); trimmed != "" {
			titleParam = trimmed
		} else {
			titleParam = ""
		}
	}
	var summaryParam any
	if input.Summary != nil {
		summaryParam = strings.TrimSpace(*input.Summary)
	}
	var slugParam any
	if input.Slug != nil {
		slugParam = strings.TrimSpace(*input.Slug)
	}
	var localeParam any
	if input.Locale != nil {
		if trimmed := strings.TrimSpace(*input.Locale); trimmed != "" {
			localeParam = trimmed
		} else {
			localeParam = ""
		}
	}
	var statusParam any
	if input.StatusCode != nil {
		if trimmed := strings.TrimSpace(*input.StatusCode); trimmed != "" {
			statusParam = strings.ToLower(trimmed)
		}
	}
	var categoryParam any
	if input.CategoryCode != nil {
		if trimmed := strings.TrimSpace(*input.CategoryCode); trimmed != "" {
			categoryParam = strings.ToLower(trimmed)
		}
	}
	var typeParam any
	if input.TypeCode != nil {
		if trimmed := strings.TrimSpace(*input.TypeCode); trimmed != "" {
			typeParam = strings.ToLower(trimmed)
		}
	}
	var authorParam any
	if input.AuthorEmail != nil {
		trimmed := strings.TrimSpace(*input.AuthorEmail)
		authorParam = trimmed
		if trimmed == "" {
			authorParam = ""
		}
	}
	var bodyParam any
	if input.Body != nil {
		bodyParam = *input.Body
	}
	var noteParam any
	if input.Note != nil {
		if trimmed := strings.TrimSpace(*input.Note); trimmed != "" {
			noteParam = trimmed
		}
	}
	var publishedAtParam any
	if input.PublishedAt != nil {
		publishedAtParam = *input.PublishedAt
	}
	var actorParam any
	if actorID != nil {
		if trimmed := strings.TrimSpace(*actorID); trimmed != "" {
			actorParam = trimmed
		}
	}

	row := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_content_update($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)`,
		id,
		titleParam,
		summaryParam,
		slugParam,
		localeParam,
		statusParam,
		categoryParam,
		typeParam,
		authorParam,
		bodyParam,
		blocksJSON,
		actorParam,
		noteParam,
		publishedAtParam,
		input.ForceNewVersion,
	)
	return scanContentDetail(row)
}

func (r *Repo) DeleteContent(ctx context.Context, id string) error {
	var ok bool
	if err := r.pool.QueryRow(ctx, `SELECT heartguard.sp_content_delete($1)`, id).Scan(&ok); err != nil {
		return err
	}
	if !ok {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListContentVersions(ctx context.Context, id string, limit, offset int) ([]models.ContentVersion, error) {
	if limit <= 0 {
		limit = 20
	} else if limit > 100 {
		limit = 100
	}
	if offset < 0 {
		offset = 0
	}

	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_content_versions($1, $2, $3)`, id, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.ContentVersion, 0, limit)
	for rows.Next() {
		var (
			item       models.ContentVersion
			editorID   sql.NullString
			editorName sql.NullString
			note       sql.NullString
		)
		if err := rows.Scan(
			&item.ID,
			&item.VersionNo,
			&item.CreatedAt,
			&editorID,
			&editorName,
			&item.ChangeType,
			&note,
			&item.Published,
			&item.Body,
		); err != nil {
			return nil, err
		}
		if editorID.Valid {
			idVal := editorID.String
			item.EditorUserID = &idVal
		}
		if editorName.Valid {
			name := editorName.String
			item.EditorName = &name
		}
		if note.Valid {
			noteText := note.String
			item.Note = &noteText
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) ListContentAuthors(ctx context.Context) ([]models.ContentAuthor, error) {
	rows, err := r.pool.Query(ctx, `
SELECT u.id::text, u.name, u.email, LOWER(us.code)
FROM heartguard.users u
JOIN heartguard.user_statuses us ON us.id = u.user_status_id
WHERE LOWER(us.code) <> 'blocked'
ORDER BY LOWER(u.name), LOWER(u.email)
`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	authors := make([]models.ContentAuthor, 0, 32)
	for rows.Next() {
		var item models.ContentAuthor
		if err := rows.Scan(&item.UserID, &item.Name, &item.Email, &item.StatusCode); err != nil {
			return nil, err
		}
		authors = append(authors, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return authors, nil
}

// ------------------------------
// Metrics
// ------------------------------

func (r *Repo) MetricsOverview(ctx context.Context) (*models.MetricsOverview, error) {
	var (
		avg         sql.NullFloat64
		totalUsers  int
		totalOrgs   int
		memberships int
		pending     int
		opsRaw      []byte
	)
	if err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_metrics_overview()`).
		Scan(&avg, &totalUsers, &totalOrgs, &memberships, &pending, &opsRaw); err != nil {
		return nil, err
	}
	var ops []models.OperationStat
	if len(opsRaw) > 0 {
		if err := json.Unmarshal(opsRaw, &ops); err != nil {
			return nil, err
		}
	}
	res := &models.MetricsOverview{
		AvgResponseMs:      avg.Float64,
		TotalUsers:         totalUsers,
		TotalOrganizations: totalOrgs,
		TotalMemberships:   memberships,
		PendingInvitations: pending,
		RecentOperations:   ops,
	}
	return res, nil
}

func (r *Repo) MetricsRecentActivity(ctx context.Context, limit int) ([]models.ActivityEntry, error) {
	if limit <= 0 {
		limit = 8
	} else if limit > 50 {
		limit = 50
	}
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_metrics_recent_activity($1)`, limit)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.ActivityEntry, 0, limit)
	for rows.Next() {
		var (
			item       models.ActivityEntry
			entity     sql.NullString
			actorEmail sql.NullString
			detailsRaw []byte
		)
		if err := rows.Scan(&item.TS, &item.Action, &entity, &actorEmail, &detailsRaw); err != nil {
			return nil, err
		}
		if entity.Valid {
			s := entity.String
			item.Entity = &s
		}
		if actorEmail.Valid {
			s := actorEmail.String
			item.ActorEmail = &s
		}
		if len(detailsRaw) > 0 {
			var details map[string]any
			if err := json.Unmarshal(detailsRaw, &details); err == nil {
				item.Details = details
			}
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) MetricsUserStatusBreakdown(ctx context.Context) ([]models.StatusBreakdown, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_metrics_user_status_breakdown()`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.StatusBreakdown, 0, 8)
	for rows.Next() {
		var item models.StatusBreakdown
		if err := rows.Scan(&item.Code, &item.Label, &item.Count); err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) MetricsInvitationBreakdown(ctx context.Context) ([]models.InvitationBreakdown, error) {
	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_metrics_invitation_breakdown()`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.InvitationBreakdown, 0, 4)
	for rows.Next() {
		var item models.InvitationBreakdown
		if err := rows.Scan(&item.Status, &item.Label, &item.Count); err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) MetricsContentSnapshot(ctx context.Context) (*models.ContentMetrics, error) {
	var (
		totalsRaw     []byte
		monthlyRaw    []byte
		categoriasRaw []byte
		statusRaw     []byte
		roleRaw       []byte
		cumulativeRaw []byte
		heatmapRaw    []byte
	)
	if err := r.pool.QueryRow(ctx, `SELECT * FROM heartguard.sp_metrics_content_snapshot()`).
		Scan(&totalsRaw, &monthlyRaw, &categoriasRaw, &statusRaw, &roleRaw, &cumulativeRaw, &heatmapRaw); err != nil {
		return nil, err
	}
	metrics := &models.ContentMetrics{}
	if len(totalsRaw) > 0 {
		if err := json.Unmarshal(totalsRaw, &metrics.Totals); err != nil {
			return nil, err
		}
	}
	if len(monthlyRaw) > 0 {
		if err := json.Unmarshal(monthlyRaw, &metrics.Monthly); err != nil {
			return nil, err
		}
	}
	if len(categoriasRaw) > 0 {
		if err := json.Unmarshal(categoriasRaw, &metrics.Categories); err != nil {
			return nil, err
		}
	}
	if len(statusRaw) > 0 {
		if err := json.Unmarshal(statusRaw, &metrics.StatusTrends); err != nil {
			return nil, err
		}
	}
	if len(roleRaw) > 0 {
		if err := json.Unmarshal(roleRaw, &metrics.RoleActivity); err != nil {
			return nil, err
		}
	}
	if len(cumulativeRaw) > 0 {
		if err := json.Unmarshal(cumulativeRaw, &metrics.Cumulative); err != nil {
			return nil, err
		}
	}
	if len(heatmapRaw) > 0 {
		if err := json.Unmarshal(heatmapRaw, &metrics.UpdateHeatmap); err != nil {
			return nil, err
		}
	}
	if metrics.Monthly == nil {
		metrics.Monthly = make([]models.ContentMonthlyPoint, 0)
	}
	if metrics.Categories == nil {
		metrics.Categories = make([]models.ContentCategorySlice, 0)
	}
	if metrics.StatusTrends == nil {
		metrics.StatusTrends = make([]models.ContentStatusTrend, 0)
	}
	if metrics.RoleActivity == nil {
		metrics.RoleActivity = make([]models.ContentRoleActivity, 0)
	}
	if metrics.Cumulative == nil {
		metrics.Cumulative = make([]models.ContentCumulativePoint, 0)
	}
	if metrics.UpdateHeatmap == nil {
		metrics.UpdateHeatmap = make([]models.ContentUpdateHeatmapPoint, 0)
	}
	return metrics, nil
}

func (r *Repo) MetricsContentReport(ctx context.Context, filters models.ContentReportFilters) (*models.ContentReportResult, error) {
	limit := filters.Limit
	if limit <= 0 {
		limit = 50
	} else if limit > 500 {
		limit = 500
	}
	offset := filters.Offset
	if offset < 0 {
		offset = 0
	}

	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_metrics_content_report($1, $2, $3, $4, $5, $6, $7)`,
		filters.From,
		filters.To,
		filters.Status,
		filters.Category,
		filters.Search,
		limit,
		offset,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := &models.ContentReportResult{
		Rows:   make([]models.ContentReportRow, 0, limit),
		Limit:  limit,
		Offset: offset,
	}

	for rows.Next() {
		var (
			row          models.ContentReportRow
			authorName   sql.NullString
			authorEmail  sql.NullString
			publishedAt  sql.NullTime
			lastUpdateAt sql.NullTime
			lastEditor   sql.NullString
			totalCount   int
		)
		if err := rows.Scan(
			&row.ID,
			&row.Title,
			&row.StatusCode,
			&row.StatusLabel,
			&row.CategoryCode,
			&row.CategoryLabel,
			&authorName,
			&authorEmail,
			&publishedAt,
			&row.UpdatedAt,
			&lastUpdateAt,
			&lastEditor,
			&row.Updates30d,
			&totalCount,
		); err != nil {
			return nil, err
		}
		if authorName.Valid {
			s := authorName.String
			row.AuthorName = &s
		}
		if authorEmail.Valid {
			s := authorEmail.String
			row.AuthorEmail = &s
		}
		if publishedAt.Valid {
			t := publishedAt.Time
			row.PublishedAt = &t
		}
		if lastUpdateAt.Valid {
			t := lastUpdateAt.Time
			row.LastUpdateAt = &t
		}
		if lastEditor.Valid {
			s := lastEditor.String
			row.LastEditorName = &s
		}
		result.Rows = append(result.Rows, row)
		result.Total = totalCount
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return result, nil
}

func (r *Repo) MetricsOperationsReport(ctx context.Context, filters models.OperationsReportFilters) (*models.OperationsReportResult, error) {
	limit := filters.Limit
	if limit <= 0 {
		limit = 50
	} else if limit > 500 {
		limit = 500
	}
	offset := filters.Offset
	if offset < 0 {
		offset = 0
	}

	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_metrics_operations_report($1, $2, $3, $4, $5)`,
		filters.From,
		filters.To,
		filters.Action,
		limit,
		offset,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := &models.OperationsReportResult{
		Rows:   make([]models.OperationsReportRow, 0, limit),
		Limit:  limit,
		Offset: offset,
	}

	for rows.Next() {
		var (
			row        models.OperationsReportRow
			firstEvent sql.NullTime
			lastEvent  sql.NullTime
			totalCount int
		)
		if err := rows.Scan(
			&row.Action,
			&row.TotalEvents,
			&row.UniqueUsers,
			&row.UniqueEntities,
			&firstEvent,
			&lastEvent,
			&totalCount,
		); err != nil {
			return nil, err
		}
		if firstEvent.Valid {
			t := firstEvent.Time
			row.FirstEvent = &t
		}
		if lastEvent.Valid {
			t := lastEvent.Time
			row.LastEvent = &t
		}
		result.Rows = append(result.Rows, row)
		result.Total = totalCount
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return result, nil
}

func (r *Repo) MetricsUserActivityReport(ctx context.Context, filters models.UserActivityReportFilters) (*models.UserActivityReportResult, error) {
	limit := filters.Limit
	if limit <= 0 {
		limit = 50
	} else if limit > 500 {
		limit = 500
	}
	offset := filters.Offset
	if offset < 0 {
		offset = 0
	}

	rows, err := r.pool.Query(ctx, `SELECT * FROM heartguard.sp_metrics_users_report($1, $2, $3, $4, $5, $6)`,
		filters.From,
		filters.To,
		filters.Status,
		filters.Search,
		limit,
		offset,
	)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	result := &models.UserActivityReportResult{
		Rows:   make([]models.UserActivityReportRow, 0, limit),
		Limit:  limit,
		Offset: offset,
	}

	for rows.Next() {
		var (
			row         models.UserActivityReportRow
			statusCode  sql.NullString
			statusLabel sql.NullString
			firstAction sql.NullTime
			lastAction  sql.NullTime
			totalCount  int
		)
		if err := rows.Scan(
			&row.ID,
			&row.Name,
			&row.Email,
			&statusCode,
			&statusLabel,
			&row.CreatedAt,
			&firstAction,
			&lastAction,
			&row.ActionsCount,
			&row.DistinctActions,
			&row.Organizations,
			&totalCount,
		); err != nil {
			return nil, err
		}
		if statusCode.Valid {
			row.StatusCode = statusCode.String
		}
		if statusLabel.Valid {
			row.StatusLabel = statusLabel.String
		} else {
			row.StatusLabel = row.StatusCode
		}
		if firstAction.Valid {
			t := firstAction.Time
			row.FirstAction = &t
		}
		if lastAction.Valid {
			t := lastAction.Time
			row.LastAction = &t
		}
		result.Rows = append(result.Rows, row)
		result.Total = totalCount
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return result, nil
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
// Users
// ------------------------------
func (r *Repo) SearchUsers(ctx context.Context, q string, limit, offset int) ([]models.User, error) {
	rows, err := r.pool.Query(ctx, `
SELECT
	u.id,
	u.name,
	u.email,
	us.code AS status,
	u.created_at,
	COALESCE(
		jsonb_agg(
			jsonb_build_object(
				'org_id', o.id,
				'org_code', o.code,
				'org_name', o.name,
				'org_role_code', orl.code,
				'org_role_label', orl.label,
				'joined_at', to_char(mum.joined_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
			)
		) FILTER (WHERE o.id IS NOT NULL),
		'[]'::jsonb
	) AS memberships,
	COALESCE(
		jsonb_agg(DISTINCT jsonb_build_object(
			'role_id', gr.id,
			'role_name', gr.name,
			'description', gr.description,
			'assigned_at', to_char(ur.assigned_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')
		)) FILTER (WHERE gr.id IS NOT NULL),
		'[]'::jsonb
	) AS roles
FROM users u
JOIN user_statuses us ON us.id = u.user_status_id
LEFT JOIN user_org_membership mum ON mum.user_id = u.id
LEFT JOIN organizations o ON o.id = mum.org_id
LEFT JOIN org_roles orl ON orl.id = mum.org_role_id
LEFT JOIN user_role ur ON ur.user_id = u.id
LEFT JOIN roles gr ON gr.id = ur.role_id
WHERE ($1 = '' OR u.email ILIKE '%'||$1||'%' OR u.name ILIKE '%'||$1||'%')
GROUP BY u.id, u.name, u.email, us.code, u.created_at
ORDER BY u.created_at DESC
LIMIT $2 OFFSET $3
`, q, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var out []models.User
	for rows.Next() {
		var (
			m              models.User
			membershipsRaw []byte
			rolesRaw       []byte
		)
		if err := rows.Scan(&m.ID, &m.Name, &m.Email, &m.Status, &m.CreatedAt, &membershipsRaw, &rolesRaw); err != nil {
			return nil, err
		}
		if len(membershipsRaw) > 0 {
			if err := json.Unmarshal(membershipsRaw, &m.Memberships); err != nil {
				return nil, err
			}
		}
		if len(rolesRaw) > 0 {
			if err := json.Unmarshal(rolesRaw, &m.Roles); err != nil {
				return nil, err
			}
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
// Roles
// ------------------------------

func (r *Repo) ListRoles(ctx context.Context, limit, offset int) ([]models.Role, error) {
	rows, err := r.pool.Query(ctx, `
SELECT id::text, name, description, created_at
FROM roles
ORDER BY created_at DESC
LIMIT $1 OFFSET $2
`, limit, offset)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Role, 0, limit)
	for rows.Next() {
		var (
			item models.Role
			desc sql.NullString
		)
		if err := rows.Scan(&item.ID, &item.Name, &desc, &item.CreatedAt); err != nil {
			return nil, err
		}
		if desc.Valid {
			s := desc.String
			item.Description = &s
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) ListRolePermissions(ctx context.Context, roleID string) ([]models.RolePermission, error) {
	rows, err := r.pool.Query(ctx, `
SELECT rp.role_id::text, p.code, p.description, rp.granted_at
FROM role_permission rp
JOIN permissions p ON p.id = rp.permission_id
WHERE rp.role_id = $1::uuid
ORDER BY p.code
`, roleID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.RolePermission, 0, 8)
	for rows.Next() {
		var (
			item models.RolePermission
			desc sql.NullString
		)
		if err := rows.Scan(&item.RoleID, &item.Code, &desc, &item.GrantedAt); err != nil {
			return nil, err
		}
		if desc.Valid {
			item.Description = desc.String
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) GrantRolePermission(ctx context.Context, roleID, permissionCode string) (*models.RolePermission, error) {
	var (
		item models.RolePermission
		desc sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
WITH perm AS (
        SELECT id, code, description
        FROM permissions
        WHERE code = $2
), upsert AS (
        INSERT INTO role_permission (role_id, permission_id)
        SELECT $1::uuid, perm.id
        FROM perm
        ON CONFLICT (role_id, permission_id) DO UPDATE SET granted_at = role_permission.granted_at
        RETURNING role_id::text, permission_id, granted_at
)
SELECT u.role_id, perm.code, perm.description, u.granted_at
FROM upsert u
JOIN perm ON TRUE
`, roleID, permissionCode).Scan(&item.RoleID, &item.Code, &desc, &item.GrantedAt)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, pgx.ErrNoRows
		}
		return nil, err
	}
	if desc.Valid {
		item.Description = desc.String
	}
	return &item, nil
}

func (r *Repo) RevokeRolePermission(ctx context.Context, roleID, permissionCode string) error {
	ct, err := r.pool.Exec(ctx, `
DELETE FROM role_permission
WHERE role_id = $1::uuid
  AND permission_id = (
        SELECT id FROM permissions WHERE code = $2
)
`, roleID, permissionCode)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) CreateRole(ctx context.Context, name string, description *string) (*models.Role, error) {
	var (
		item models.Role
		desc sql.NullString
	)
	var descParam any
	if description != nil {
		descParam = *description
	}
	err := r.pool.QueryRow(ctx, `
INSERT INTO roles (name, description)
VALUES ($1, NULLIF($2, ''))
RETURNING id::text, name, description, created_at
`, name, descParam).Scan(&item.ID, &item.Name, &desc, &item.CreatedAt)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		s := desc.String
		item.Description = &s
	}
	return &item, nil
}

func (r *Repo) UpdateRole(ctx context.Context, id string, name, description *string) (*models.Role, error) {
	setClauses := make([]string, 0, 2)
	args := make([]any, 0, 3)
	idx := 2
	if name != nil {
		setClauses = append(setClauses, fmt.Sprintf("name = $%d", idx))
		args = append(args, *name)
		idx++
	}
	if description != nil {
		setClauses = append(setClauses, fmt.Sprintf("description = NULLIF($%d, '')", idx))
		args = append(args, *description)
		idx++
	}
	if len(setClauses) == 0 {
		var (
			item models.Role
			desc sql.NullString
		)
		err := r.pool.QueryRow(ctx, `SELECT id::text, name, description, created_at FROM roles WHERE id = $1`, id).
			Scan(&item.ID, &item.Name, &desc, &item.CreatedAt)
		if err != nil {
			return nil, err
		}
		if desc.Valid {
			s := desc.String
			item.Description = &s
		}
		return &item, nil
	}
	args = append([]any{id}, args...)
	query := fmt.Sprintf(`
UPDATE roles
SET %s
WHERE id = $1
RETURNING id::text, name, description, created_at
`, strings.Join(setClauses, ", "))
	var (
		item models.Role
		desc sql.NullString
	)
	err := r.pool.QueryRow(ctx, query, args...).Scan(&item.ID, &item.Name, &desc, &item.CreatedAt)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		s := desc.String
		item.Description = &s
	}
	return &item, nil
}

func (r *Repo) DeleteRole(ctx context.Context, id string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM roles WHERE id = $1`, id)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

func (r *Repo) ListUserRoles(ctx context.Context, userID string) ([]models.UserRole, error) {
	rows, err := r.pool.Query(ctx, `
SELECT r.id::text, r.name, r.description, ur.assigned_at
FROM user_role ur
JOIN roles r ON r.id = ur.role_id
WHERE ur.user_id = $1
ORDER BY ur.assigned_at DESC
`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.UserRole, 0, 4)
	for rows.Next() {
		var (
			item     models.UserRole
			desc     sql.NullString
			assigned time.Time
		)
		if err := rows.Scan(&item.RoleID, &item.RoleName, &desc, &assigned); err != nil {
			return nil, err
		}
		if desc.Valid {
			s := desc.String
			item.Description = &s
		}
		assignedCopy := assigned
		item.AssignedAt = &assignedCopy
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

func (r *Repo) AssignRoleToUser(ctx context.Context, userID, roleID string) (*models.UserRole, error) {
	var (
		item     models.UserRole
		desc     sql.NullString
		assigned time.Time
	)
	err := r.pool.QueryRow(ctx, `
WITH upsert AS (
	INSERT INTO user_role (user_id, role_id, assigned_at)
	VALUES ($1, $2, NOW())
	ON CONFLICT (user_id, role_id) DO UPDATE SET assigned_at = EXCLUDED.assigned_at
	RETURNING role_id, assigned_at
)
SELECT r.id::text, r.name, r.description, u.assigned_at
FROM upsert u
JOIN roles r ON r.id = u.role_id
`, userID, roleID).Scan(&item.RoleID, &item.RoleName, &desc, &assigned)
	if err != nil {
		return nil, err
	}
	if desc.Valid {
		s := desc.String
		item.Description = &s
	}
	assignedCopy := assigned
	item.AssignedAt = &assignedCopy
	return &item, nil
}

func (r *Repo) RemoveRoleFromUser(ctx context.Context, userID, roleID string) error {
	ct, err := r.pool.Exec(ctx, `DELETE FROM user_role WHERE user_id = $1 AND role_id = $2`, userID, roleID)
	if err != nil {
		return err
	}
	if ct.RowsAffected() == 0 {
		return pgx.ErrNoRows
	}
	return nil
}

// ------------------------------
// System settings
// ------------------------------

func (r *Repo) GetSystemSettings(ctx context.Context) (*models.SystemSettings, error) {
	var (
		settings  models.SystemSettings
		secondary sql.NullString
		logo      sql.NullString
		phone     sql.NullString
		message   sql.NullString
		updatedBy sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
SELECT
  brand_name,
  support_email,
  primary_color,
  secondary_color,
  logo_url,
  contact_phone,
  default_locale,
  default_timezone,
  maintenance_mode,
  maintenance_message,
  updated_at,
  updated_by::text
FROM system_settings
WHERE id = 1
`).Scan(
		&settings.BrandName,
		&settings.SupportEmail,
		&settings.PrimaryColor,
		&secondary,
		&logo,
		&phone,
		&settings.DefaultLocale,
		&settings.DefaultTimezone,
		&settings.MaintenanceMode,
		&message,
		&settings.UpdatedAt,
		&updatedBy,
	)
	if err != nil {
		return nil, err
	}
	if secondary.Valid {
		s := secondary.String
		settings.SecondaryColor = &s
	}
	if logo.Valid {
		s := logo.String
		settings.LogoURL = &s
	}
	if phone.Valid {
		s := phone.String
		settings.ContactPhone = &s
	}
	if message.Valid {
		s := message.String
		settings.MaintenanceMessage = &s
	}
	if updatedBy.Valid {
		s := updatedBy.String
		settings.UpdatedBy = &s
	}
	return &settings, nil
}

func (r *Repo) UpdateSystemSettings(ctx context.Context, payload models.SystemSettingsInput, updatedBy *string) (*models.SystemSettings, error) {
	var (
		secondary interface{}
		logo      interface{}
		phone     interface{}
		message   interface{}
	)
	if payload.SecondaryColor != nil {
		secondary = *payload.SecondaryColor
	}
	if payload.LogoURL != nil {
		logo = *payload.LogoURL
	}
	if payload.ContactPhone != nil {
		phone = *payload.ContactPhone
	}
	if payload.MaintenanceMessage != nil {
		message = *payload.MaintenanceMessage
	}
	var actor interface{}
	if updatedBy != nil {
		actor = *updatedBy
	}
	var (
		updated      models.SystemSettings
		outSecondary sql.NullString
		outLogo      sql.NullString
		outPhone     sql.NullString
		outMessage   sql.NullString
		outUpdatedBy sql.NullString
	)
	err := r.pool.QueryRow(ctx, `
UPDATE system_settings SET
  brand_name = $1,
  support_email = $2,
  primary_color = $3,
  secondary_color = $4,
  logo_url = $5,
  contact_phone = $6,
  default_locale = $7,
  default_timezone = $8,
  maintenance_mode = $9,
  maintenance_message = $10,
  updated_at = NOW(),
  updated_by = $11
WHERE id = 1
RETURNING
  brand_name,
  support_email,
  primary_color,
  secondary_color,
  logo_url,
  contact_phone,
  default_locale,
  default_timezone,
  maintenance_mode,
  maintenance_message,
  updated_at,
  updated_by::text
`,
		payload.BrandName,
		payload.SupportEmail,
		payload.PrimaryColor,
		secondary,
		logo,
		phone,
		payload.DefaultLocale,
		payload.DefaultTimezone,
		payload.MaintenanceMode,
		message,
		actor,
	).Scan(
		&updated.BrandName,
		&updated.SupportEmail,
		&updated.PrimaryColor,
		&outSecondary,
		&outLogo,
		&outPhone,
		&updated.DefaultLocale,
		&updated.DefaultTimezone,
		&updated.MaintenanceMode,
		&outMessage,
		&updated.UpdatedAt,
		&outUpdatedBy,
	)
	if err != nil {
		return nil, err
	}
	if outSecondary.Valid {
		s := outSecondary.String
		updated.SecondaryColor = &s
	}
	if outLogo.Valid {
		s := outLogo.String
		updated.LogoURL = &s
	}
	if outPhone.Valid {
		s := outPhone.String
		updated.ContactPhone = &s
	}
	if outMessage.Valid {
		s := outMessage.String
		updated.MaintenanceMessage = &s
	}
	if outUpdatedBy.Valid {
		s := outUpdatedBy.String
		updated.UpdatedBy = &s
	}
	return &updated, nil
}

// ------------------------------
// API Keys
// ------------------------------
func (r *Repo) ListPermissions(ctx context.Context) ([]models.Permission, error) {
	rows, err := r.pool.Query(ctx, `
	SELECT code, COALESCE(description,'')
	FROM permissions
	ORDER BY code
	`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	out := make([]models.Permission, 0, 32)
	for rows.Next() {
		var item models.Permission
		if err := rows.Scan(&item.Code, &item.Description); err != nil {
			return nil, err
		}
		out = append(out, item)
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

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
	details
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
		)
		if err := rows.Scan(
			&idText,
			&actionStr,
			&ts,
			&userUUID,
			&entity,
			&entityUUID,
			&detailsRaw,
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
		})
	}
	if err := rows.Err(); err != nil {
		return nil, err
	}
	return out, nil
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

func (r *Repo) GetUserSummary(ctx context.Context, userID string) (*models.User, error) {
	row := r.pool.QueryRow(ctx, `
SELECT u.id::text, u.name, u.email, us.code AS status, u.created_at
FROM users u
JOIN user_statuses us ON us.id = u.user_status_id
WHERE u.id = $1
`, userID)
	var u models.User
	if err := row.Scan(&u.ID, &u.Name, &u.Email, &u.Status, &u.CreatedAt); err != nil {
		return nil, err
	}
	return &u, nil
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

func refreshTokenKey(hash string) string {
	return "rt:" + hash
}

func (r *Repo) IssueRefreshToken(ctx context.Context, userID, tokenHash string, ttl time.Duration) error {
	_, err := r.pool.Exec(ctx, `
INSERT INTO refresh_tokens (user_id, token_hash, issued_at, expires_at)
VALUES ($1, $2, NOW(), NOW() + make_interval(secs => $3))
ON CONFLICT (user_id, token_hash) DO NOTHING
`, userID, tokenHash, int64(ttl.Seconds()))
	if err != nil {
		return err
	}
	if r.redis == nil || ttl <= 0 {
		return nil
	}
	if rErr := r.redis.Set(ctx, refreshTokenKey(tokenHash), userID, ttl).Err(); rErr != nil {
		log.Printf("redis set refresh token (issue): %v", rErr)
	}
	return nil
}

func (r *Repo) ValidateRefreshToken(ctx context.Context, raw string) (string, error) {
	sum := sha256.Sum256([]byte(raw))
	hash := hex.EncodeToString(sum[:])
	key := refreshTokenKey(hash)
	if r.redis != nil {
		uid, err := r.redis.Get(ctx, key).Result()
		if err == nil {
			return uid, nil
		}
		if !errors.Is(err, redis.Nil) {
			log.Printf("redis get refresh token: %v", err)
		}
	}
	var (
		uid       string
		expiresAt time.Time
	)
	err := r.pool.QueryRow(ctx, `
SELECT user_id::text, expires_at
FROM refresh_tokens
WHERE token_hash = $1 AND revoked_at IS NULL AND expires_at > NOW()
`, hash).Scan(&uid, &expiresAt)
	if err != nil {
		return "", err
	}
	if r.redis != nil {
		if ttl := time.Until(expiresAt); ttl > 0 {
			if rErr := r.redis.Set(ctx, key, uid, ttl).Err(); rErr != nil {
				log.Printf("redis set refresh token (validate): %v", rErr)
			}
		}
	}
	return uid, nil
}

func (r *Repo) RevokeRefreshToken(ctx context.Context, raw string) error {
	sum := sha256.Sum256([]byte(raw))
	hash := hex.EncodeToString(sum[:])
	_, err := r.pool.Exec(ctx, `
UPDATE refresh_tokens
SET revoked_at = NOW()
WHERE token_hash = $1 AND revoked_at IS NULL
`, hash)
	if err != nil {
		return err
	}
	if r.redis != nil {
		if rErr := r.redis.Del(ctx, refreshTokenKey(hash)).Err(); rErr != nil {
			log.Printf("redis del refresh token: %v", rErr)
		}
	}
	return nil
}

func contentBlocksToJSON(blocks []models.ContentBlockInput) ([]byte, error) {
	if len(blocks) == 0 {
		return nil, nil
	}
	type blockPayload struct {
		BlockType string  `json:"block_type"`
		Title     *string `json:"title,omitempty"`
		Content   string  `json:"content"`
		Position  int     `json:"position"`
	}
	payload := make([]blockPayload, 0, len(blocks))
	for _, block := range blocks {
		payload = append(payload, blockPayload{
			BlockType: strings.TrimSpace(block.BlockType),
			Title:     block.Title,
			Content:   block.Content,
			Position:  block.Position,
		})
	}
	return json.Marshal(payload)
}

func scanContentDetail(row pgx.Row) (*models.ContentDetail, error) {
	var (
		id                     string
		title                  string
		summary                sql.NullString
		slug                   sql.NullString
		locale                 sql.NullString
		statusCode             string
		statusLabel            string
		statusWeight           int32
		categoryCode           string
		categoryLabel          string
		typeCode               string
		typeLabel              string
		authorUserID           sql.NullString
		authorName             sql.NullString
		authorEmail            sql.NullString
		createdAt              time.Time
		updatedAt              time.Time
		publishedAt            sql.NullTime
		archivedAt             sql.NullTime
		latestVersionNo        sql.NullInt32
		latestVersionID        sql.NullString
		latestVersionCreatedAt sql.NullTime
		body                   sql.NullString
		blocksRaw              []byte
	)
	if err := row.Scan(
		&id,
		&title,
		&summary,
		&slug,
		&locale,
		&statusCode,
		&statusLabel,
		&statusWeight,
		&categoryCode,
		&categoryLabel,
		&typeCode,
		&typeLabel,
		&authorUserID,
		&authorName,
		&authorEmail,
		&createdAt,
		&updatedAt,
		&publishedAt,
		&archivedAt,
		&latestVersionNo,
		&latestVersionID,
		&latestVersionCreatedAt,
		&body,
		&blocksRaw,
	); err != nil {
		return nil, err
	}

	detail := &models.ContentDetail{
		ContentItem: models.ContentItem{
			ID:            id,
			Title:         title,
			Locale:        strings.TrimSpace(locale.String),
			StatusCode:    strings.ToLower(statusCode),
			StatusLabel:   statusLabel,
			StatusWeight:  int(statusWeight),
			CategoryCode:  strings.ToLower(categoryCode),
			CategoryLabel: categoryLabel,
			TypeCode:      strings.ToLower(typeCode),
			TypeLabel:     typeLabel,
			UpdatedAt:     updatedAt,
			CreatedAt:     createdAt,
		},
		Body:   body.String,
		Blocks: make([]models.ContentBlock, 0),
	}

	if detail.Locale == "" {
		detail.Locale = locale.String
	}

	if summary.Valid {
		val := summary.String
		detail.Summary = &val
	}
	if slug.Valid {
		val := slug.String
		detail.Slug = &val
	}
	if authorName.Valid {
		val := authorName.String
		detail.AuthorName = &val
	}
	if authorEmail.Valid {
		val := authorEmail.String
		detail.AuthorEmail = &val
	}
	if publishedAt.Valid {
		val := publishedAt.Time
		detail.PublishedAt = &val
	}
	if archivedAt.Valid {
		val := archivedAt.Time
		detail.ArchivedAt = &val
	}
	if latestVersionNo.Valid {
		v := int(latestVersionNo.Int32)
		detail.LatestVersionNo = &v
	}
	if latestVersionID.Valid {
		val := latestVersionID.String
		detail.LatestVersionID = &val
	}
	if latestVersionCreatedAt.Valid {
		val := latestVersionCreatedAt.Time
		detail.LatestVersionCreatedAt = &val
	}

	if len(blocksRaw) > 0 {
		var blocks []models.ContentBlock
		if err := json.Unmarshal(blocksRaw, &blocks); err != nil {
			return nil, err
		}
		if blocks != nil {
			detail.Blocks = blocks
		}
	}
	if detail.Blocks == nil {
		detail.Blocks = make([]models.ContentBlock, 0)
	}

	return detail, nil
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
