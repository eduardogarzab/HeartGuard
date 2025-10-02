package models

import "time"

type Organization struct {
	ID        string    `json:"id"`
	Code      string    `json:"code"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
}

type OrgInvitation struct {
	ID          string     `json:"id"`
	OrgID       string     `json:"org_id"`
	Email       *string    `json:"email,omitempty"`
	OrgRoleID   string     `json:"org_role_id"`
	OrgRoleCode string     `json:"org_role_code,omitempty"`
	Token       string     `json:"token"`
	ExpiresAt   time.Time  `json:"expires_at"`
	UsedAt      *time.Time `json:"used_at,omitempty"`
	RevokedAt   *time.Time `json:"revoked_at,omitempty"`
	Status      string     `json:"status"`
	CreatedBy   *string    `json:"created_by,omitempty"`
	CreatedAt   time.Time  `json:"created_at"`
}

type User struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Email     string    `json:"email"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
}

type APIKey struct {
	ID          string     `json:"id"`
	Label       string     `json:"label"`
	OwnerUserID *string    `json:"owner_user_id,omitempty"`
	Scopes      []string   `json:"scopes,omitempty"`
	CreatedAt   time.Time  `json:"created_at"`
	ExpiresAt   *time.Time `json:"expires_at,omitempty"`
	RevokedAt   *time.Time `json:"revoked_at,omitempty"`
	Revoked     bool       `json:"revoked"`
}

type Membership struct {
	OrgID        string    `json:"org_id"`
	UserID       string    `json:"user_id"`
	Email        string    `json:"email"`
	Name         string    `json:"name"`
	OrgRoleID    string    `json:"org_role_id"`
	OrgRoleCode  string    `json:"org_role_code"`
	OrgRoleLabel string    `json:"org_role_label"`
	JoinedAt     time.Time `json:"joined_at"`
}

type AuditLog struct {
	ID       string         `json:"id"`
	Action   string         `json:"action"`
	TS       time.Time      `json:"ts"`                  // antes "When"
	UserID   *string        `json:"user_id,omitempty"`   // uuid -> string
	Entity   *string        `json:"entity,omitempty"`    // p.ej. "api_key", "organization"
	EntityID *string        `json:"entity_id,omitempty"` // uuid -> string
	Details  map[string]any `json:"details,omitempty"`   // JSONB
	IP       *string        `json:"ip,omitempty"`        // inet -> string
}
