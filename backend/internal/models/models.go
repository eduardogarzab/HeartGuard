package models

import "time"

type Organization struct {
	ID        string    `json:"id"`
	Code      string    `json:"code"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
}

type OrgInvitation struct {
	ID        string     `json:"id"`
	OrgID     string     `json:"org_id"`
	Email     *string    `json:"email,omitempty"`
	OrgRoleID string     `json:"org_role_id"`
	Token     string     `json:"token"`
	ExpiresAt time.Time  `json:"expires_at"`
	UsedAt    *time.Time `json:"used_at,omitempty"`
	CreatedBy *string    `json:"created_by,omitempty"`
	CreatedAt time.Time  `json:"created_at"`
}

type User struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Email     string    `json:"email"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
}

type APIKey struct {
	ID        string     `json:"id"`
	Label     string     `json:"label"`
	CreatedAt time.Time  `json:"created_at"`
	ExpiresAt *time.Time `json:"expires_at,omitempty"`
	RevokedAt *time.Time `json:"revoked_at,omitempty"`
}

type AuditLog struct {
	ID     string    `json:"id"`
	Action string    `json:"action"`
	When   time.Time `json:"when"`
}
