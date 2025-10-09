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

type CatalogItem struct {
	ID     string `json:"id"`
	Code   string `json:"code"`
	Label  string `json:"label"`
	Weight *int   `json:"weight,omitempty"`
}

type CatalogDefinition struct {
	Slug        string `json:"slug"`
	Label       string `json:"label"`
	Description string `json:"description,omitempty"`
	HasWeight   bool   `json:"has_weight"`
}

type OperationStat struct {
	Type  string `json:"type"`
	Count int    `json:"count"`
}

type StatusBreakdown struct {
	Code  string `json:"code"`
	Label string `json:"label"`
	Count int    `json:"count"`
}

type InvitationBreakdown struct {
	Status string `json:"status"`
	Label  string `json:"label"`
	Count  int    `json:"count"`
}

type MetricsOverview struct {
	AvgResponseMs       float64         `json:"avg_response_ms"`
	ActiveUsers         int             `json:"active_users"`
	ActiveOrganizations int             `json:"active_organizations"`
	ActiveMemberships   int             `json:"active_memberships"`
	PendingInvitations  int             `json:"pending_invitations"`
	RecentOperations    []OperationStat `json:"recent_operations"`
}

type ContentTotals struct {
	Total                 int     `json:"total"`
	Published             int     `json:"published"`
	Drafts                int     `json:"drafts"`
	InReview              int     `json:"in_review"`
	Scheduled             int     `json:"scheduled"`
	Archived              int     `json:"archived"`
	Stale                 int     `json:"stale"`
	ActiveAuthors         int     `json:"active_authors"`
	UpdatesLast30Days     int     `json:"updates_last_30_days"`
	AvgUpdateIntervalDays float64 `json:"avg_update_interval_days"`
}

type ContentMonthlyPoint struct {
	Period    string `json:"period"`
	Total     int    `json:"total"`
	Published int    `json:"published"`
	Drafts    int    `json:"drafts"`
}

type ContentCategorySlice struct {
	Category string `json:"category"`
	Label    string `json:"label"`
	Count    int    `json:"count"`
}

type ContentStatusTrend struct {
	Period string `json:"period"`
	Status string `json:"status"`
	Count  int    `json:"count"`
}

type ContentRoleActivity struct {
	Role  string `json:"role"`
	Count int    `json:"count"`
}

type ContentCumulativePoint struct {
	Period string `json:"period"`
	Count  int    `json:"count"`
}

type ContentTopAuthor struct {
	UserID        string  `json:"user_id"`
	Name          string  `json:"name"`
	Email         *string `json:"email,omitempty"`
	Published     int     `json:"published"`
	LastPublished *string `json:"last_published,omitempty"`
}

type ContentUpdateHeatmapPoint struct {
	Date  string `json:"date"`
	Count int    `json:"count"`
}

type ContentMetrics struct {
	Totals       ContentTotals                `json:"totals"`
	Monthly      []ContentMonthlyPoint        `json:"monthly"`
	Categories   []ContentCategorySlice       `json:"categories"`
	StatusTrends []ContentStatusTrend         `json:"status_trends"`
	RoleActivity []ContentRoleActivity        `json:"role_activity"`
	Cumulative   []ContentCumulativePoint     `json:"cumulative"`
	TopAuthors   []ContentTopAuthor           `json:"top_authors"`
	UpdateHeatmap []ContentUpdateHeatmapPoint `json:"update_heatmap"`
}

type ContentReportFilters struct {
	From      *time.Time `json:"from,omitempty"`
	To        *time.Time `json:"to,omitempty"`
	Status    *string    `json:"status,omitempty"`
	Category  *string    `json:"category,omitempty"`
	Search    *string    `json:"search,omitempty"`
	Sort      string     `json:"sort,omitempty"`
	Direction string     `json:"direction,omitempty"`
	Limit     int        `json:"limit"`
	Offset    int        `json:"offset"`
}

type ContentReportRow struct {
	ID              string     `json:"id"`
	Title           string     `json:"title"`
	StatusCode      string     `json:"status_code"`
	StatusLabel     string     `json:"status_label"`
	CategoryCode    string     `json:"category_code"`
	CategoryLabel   string     `json:"category_label"`
	AuthorName      *string    `json:"author_name,omitempty"`
	AuthorEmail     *string    `json:"author_email,omitempty"`
	PublishedAt     *time.Time `json:"published_at,omitempty"`
	UpdatedAt       time.Time  `json:"updated_at"`
	LastUpdateAt    *time.Time `json:"last_update_at,omitempty"`
	LastEditorName  *string    `json:"last_editor_name,omitempty"`
	Updates30d      int        `json:"updates_30d"`
}

type ContentReportResult struct {
	Rows   []ContentReportRow `json:"rows"`
	Total  int                `json:"total"`
	Limit  int                `json:"limit"`
	Offset int                `json:"offset"`
}

type OperationsReportFilters struct {
	From   *time.Time `json:"from,omitempty"`
	To     *time.Time `json:"to,omitempty"`
	Action *string    `json:"action,omitempty"`
	Limit  int        `json:"limit"`
	Offset int        `json:"offset"`
}

type OperationsReportRow struct {
	Action         string     `json:"action"`
	ActionLabel    string     `json:"action_label"`
	TotalEvents    int        `json:"total_events"`
	UniqueUsers    int        `json:"unique_users"`
	UniqueEntities int        `json:"unique_entities"`
	FirstEvent     *time.Time `json:"first_event,omitempty"`
	LastEvent      *time.Time `json:"last_event,omitempty"`
	AvgPerDay      float64    `json:"avg_per_day"`
}

type OperationsReportResult struct {
	Rows       []OperationsReportRow `json:"rows"`
	Total      int                   `json:"total"`
	Limit      int                   `json:"limit"`
	Offset     int                   `json:"offset"`
	PeriodDays int                   `json:"period_days"`
}

type UserActivityReportFilters struct {
	From   *time.Time `json:"from,omitempty"`
	To     *time.Time `json:"to,omitempty"`
	Status *string    `json:"status,omitempty"`
	Search *string    `json:"search,omitempty"`
	Limit  int        `json:"limit"`
	Offset int        `json:"offset"`
}

type UserActivityReportRow struct {
	ID               string     `json:"id"`
	Name             string     `json:"name"`
	Email            string     `json:"email"`
	StatusCode       string     `json:"status_code"`
	StatusLabel      string     `json:"status_label"`
	CreatedAt        time.Time  `json:"created_at"`
	FirstAction      *time.Time `json:"first_action,omitempty"`
	LastAction       *time.Time `json:"last_action,omitempty"`
	ActionsCount     int        `json:"actions_count"`
	DistinctActions  int        `json:"distinct_actions"`
	Organizations    int        `json:"organizations"`
	AvgActionsPerDay float64    `json:"avg_actions_per_day"`
}

type UserActivityReportResult struct {
	Rows       []UserActivityReportRow `json:"rows"`
	Total      int                     `json:"total"`
	Limit      int                     `json:"limit"`
	Offset     int                     `json:"offset"`
	PeriodDays int                     `json:"period_days"`
}

type User struct {
	ID          string           `json:"id"`
	Name        string           `json:"name"`
	Email       string           `json:"email"`
	Status      string           `json:"status"`
	CreatedAt   time.Time        `json:"created_at"`
	Memberships []UserMembership `json:"memberships"`
	Roles       []UserRole       `json:"roles"`
}

type Role struct {
	ID          string     `json:"id"`
	Name        string     `json:"name"`
	Description *string    `json:"description,omitempty"`
	CreatedAt   time.Time  `json:"created_at"`
	Permissions []string   `json:"permissions,omitempty"`
}

type UserRole struct {
	RoleID      string     `json:"role_id"`
	RoleName    string     `json:"role_name"`
	Description *string    `json:"description,omitempty"`
	AssignedAt  *time.Time `json:"assigned_at,omitempty"`
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

type UserMembership struct {
	OrgID        string     `json:"org_id"`
	OrgCode      string     `json:"org_code"`
	OrgName      string     `json:"org_name"`
	OrgRoleCode  string     `json:"org_role_code"`
	OrgRoleLabel string     `json:"org_role_label"`
	JoinedAt     *time.Time `json:"joined_at,omitempty"`
}

type Permission struct {
	Code        string `json:"code"`
	Description string `json:"description"`
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

type OperationCount struct {
	Action string `json:"action"`
	Count  int    `json:"count"`
}

type ActivityEntry struct {
	TS         time.Time         `json:"ts"`
	Action     string            `json:"action"`
	Entity     *string           `json:"entity,omitempty"`
	UserID     *string           `json:"user_id,omitempty"`
	ActorEmail *string           `json:"actor_email,omitempty"`
	Details    map[string]any    `json:"details,omitempty"`
}

type SystemSettings struct {
	BrandName          string     `json:"brand_name"`
	SupportEmail       string     `json:"support_email"`
	PrimaryColor       string     `json:"primary_color"`
	SecondaryColor     *string    `json:"secondary_color,omitempty"`
	LogoURL            *string    `json:"logo_url,omitempty"`
	ContactPhone       *string    `json:"contact_phone,omitempty"`
	DefaultLocale      string     `json:"default_locale"`
	DefaultTimezone    string     `json:"default_timezone"`
	MaintenanceMode    bool       `json:"maintenance_mode"`
	MaintenanceMessage *string    `json:"maintenance_message,omitempty"`
	UpdatedAt          time.Time  `json:"updated_at"`
	UpdatedBy          *string    `json:"updated_by,omitempty"`
}

type SystemSettingsInput struct {
	BrandName          string  `json:"brand_name"`
	SupportEmail       string  `json:"support_email"`
	PrimaryColor       string  `json:"primary_color"`
	SecondaryColor     *string `json:"secondary_color,omitempty"`
	LogoURL            *string `json:"logo_url,omitempty"`
	ContactPhone       *string `json:"contact_phone,omitempty"`
	DefaultLocale      string  `json:"default_locale"`
	DefaultTimezone    string  `json:"default_timezone"`
	MaintenanceMode    bool    `json:"maintenance_mode"`
	MaintenanceMessage *string `json:"maintenance_message,omitempty"`
}
