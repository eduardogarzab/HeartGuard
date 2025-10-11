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
	AvgResponseMs      float64         `json:"avg_response_ms"`
	TotalUsers         int             `json:"total_users"`
	TotalOrganizations int             `json:"total_organizations"`
	TotalMemberships   int             `json:"total_memberships"`
	PendingInvitations int             `json:"pending_invitations"`
	RecentOperations   []OperationStat `json:"recent_operations"`
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

type ContentBlockType struct {
	ID          string  `json:"id"`
	Code        string  `json:"code"`
	Label       string  `json:"label"`
	Description *string `json:"description,omitempty"`
}

type Patient struct {
	ID        string     `json:"id"`
	OrgID     *string    `json:"org_id,omitempty"`
	OrgName   *string    `json:"org_name,omitempty"`
	Name      string     `json:"name"`
	Birthdate *time.Time `json:"birthdate,omitempty"`
	SexCode   *string    `json:"sex_code,omitempty"`
	SexLabel  *string    `json:"sex_label,omitempty"`
	RiskLevel *string    `json:"risk_level,omitempty"`
	CreatedAt time.Time  `json:"created_at"`
}

type PatientInput struct {
	OrgID     *string    `json:"org_id,omitempty"`
	Name      string     `json:"name"`
	Birthdate *time.Time `json:"birthdate,omitempty"`
	SexCode   *string    `json:"sex_code,omitempty"`
	RiskLevel *string    `json:"risk_level,omitempty"`
}

type Device struct {
	ID               string    `json:"id"`
	OrgID            *string   `json:"org_id,omitempty"`
	OrgName          *string   `json:"org_name,omitempty"`
	Serial           string    `json:"serial"`
	Brand            *string   `json:"brand,omitempty"`
	Model            *string   `json:"model,omitempty"`
	DeviceTypeCode   string    `json:"device_type_code"`
	DeviceTypeLabel  string    `json:"device_type_label"`
	OwnerPatientID   *string   `json:"owner_patient_id,omitempty"`
	OwnerPatientName *string   `json:"owner_patient_name,omitempty"`
	RegisteredAt     time.Time `json:"registered_at"`
	Active           bool      `json:"active"`
}

type PushDevice struct {
	ID            string    `json:"id"`
	UserID        string    `json:"user_id"`
	UserName      string    `json:"user_name"`
	UserEmail     string    `json:"user_email"`
	PlatformCode  string    `json:"platform_code"`
	PlatformLabel string    `json:"platform_label"`
	PushToken     string    `json:"push_token"`
	LastSeenAt    time.Time `json:"last_seen_at"`
	Active        bool      `json:"active"`
}

type DeviceInput struct {
	OrgID          *string `json:"org_id,omitempty"`
	Serial         string  `json:"serial"`
	Brand          *string `json:"brand,omitempty"`
	Model          *string `json:"model,omitempty"`
	DeviceTypeCode string  `json:"device_type_code"`
	OwnerPatientID *string `json:"owner_patient_id,omitempty"`
	Active         *bool   `json:"active,omitempty"`
}

type PushDeviceInput struct {
	UserID       string     `json:"user_id"`
	PlatformCode string     `json:"platform_code"`
	PushToken    string     `json:"push_token"`
	LastSeenAt   *time.Time `json:"last_seen_at,omitempty"`
	Active       *bool      `json:"active,omitempty"`
}

type DeviceType struct {
	ID          string  `json:"id"`
	Code        string  `json:"code"`
	Description *string `json:"description,omitempty"`
}

type SignalStream struct {
	ID           string     `json:"id"`
	PatientID    string     `json:"patient_id"`
	PatientName  string     `json:"patient_name"`
	DeviceID     string     `json:"device_id"`
	DeviceSerial string     `json:"device_serial"`
	SignalType   string     `json:"signal_type"`
	SignalLabel  string     `json:"signal_label"`
	SampleRateHz float64    `json:"sample_rate_hz"`
	StartedAt    time.Time  `json:"started_at"`
	EndedAt      *time.Time `json:"ended_at,omitempty"`
}

type SignalStreamInput struct {
	PatientID    string     `json:"patient_id"`
	DeviceID     string     `json:"device_id"`
	SignalType   string     `json:"signal_type"`
	SampleRateHz float64    `json:"sample_rate_hz"`
	StartedAt    time.Time  `json:"started_at"`
	EndedAt      *time.Time `json:"ended_at,omitempty"`
}

type TimeseriesBinding struct {
	ID            string                 `json:"id"`
	StreamID      string                 `json:"stream_id"`
	InfluxOrg     *string                `json:"influx_org,omitempty"`
	InfluxBucket  string                 `json:"influx_bucket"`
	Measurement   string                 `json:"measurement"`
	RetentionHint *string                `json:"retention_hint,omitempty"`
	CreatedAt     time.Time              `json:"created_at"`
	Tags          []TimeseriesBindingTag `json:"tags,omitempty"`
}

type TimeseriesBindingInput struct {
	InfluxOrg     *string `json:"influx_org,omitempty"`
	InfluxBucket  string  `json:"influx_bucket"`
	Measurement   string  `json:"measurement"`
	RetentionHint *string `json:"retention_hint,omitempty"`
}

type TimeseriesBindingUpdateInput struct {
	InfluxOrg     *string `json:"influx_org,omitempty"`
	InfluxBucket  *string `json:"influx_bucket,omitempty"`
	Measurement   *string `json:"measurement,omitempty"`
	RetentionHint *string `json:"retention_hint,omitempty"`
}

type TimeseriesBindingTag struct {
	ID        string `json:"id"`
	BindingID string `json:"binding_id"`
	TagKey    string `json:"tag_key"`
	TagValue  string `json:"tag_value"`
}

type TimeseriesBindingTagInput struct {
	TagKey   string `json:"tag_key"`
	TagValue string `json:"tag_value"`
}

type TimeseriesBindingTagUpdateInput struct {
	TagKey   *string `json:"tag_key,omitempty"`
	TagValue *string `json:"tag_value,omitempty"`
}

type MLModel struct {
	ID              string    `json:"id"`
	Name            string    `json:"name"`
	Version         string    `json:"version"`
	Task            string    `json:"task"`
	TrainingDataRef *string   `json:"training_data_ref,omitempty"`
	Hyperparams     *string   `json:"hyperparams,omitempty"`
	CreatedAt       time.Time `json:"created_at"`
}

type MLModelInput struct {
	Name            string  `json:"name"`
	Version         string  `json:"version"`
	Task            string  `json:"task"`
	TrainingDataRef *string `json:"training_data_ref,omitempty"`
	Hyperparams     *string `json:"hyperparams,omitempty"`
}

type EventType struct {
	ID                   string  `json:"id"`
	Code                 string  `json:"code"`
	Description          *string `json:"description,omitempty"`
	SeverityDefault      string  `json:"severity_default"`
	SeverityDefaultLabel string  `json:"severity_default_label"`
}

type EventTypeInput struct {
	Code            string  `json:"code"`
	Description     *string `json:"description,omitempty"`
	SeverityDefault string  `json:"severity_default"`
}

type Inference struct {
	ID           string    `json:"id"`
	ModelID      *string   `json:"model_id,omitempty"`
	ModelName    *string   `json:"model_name,omitempty"`
	StreamID     string    `json:"stream_id"`
	StreamLabel  string    `json:"stream_label"`
	PatientName  string    `json:"patient_name"`
	DeviceSerial string    `json:"device_serial"`
	WindowStart  time.Time `json:"window_start"`
	WindowEnd    time.Time `json:"window_end"`
	EventCode    string    `json:"event_code"`
	EventLabel   string    `json:"event_label"`
	Score        *float32  `json:"score,omitempty"`
	Threshold    *float32  `json:"threshold,omitempty"`
	CreatedAt    time.Time `json:"created_at"`
	SeriesRef    *string   `json:"series_ref,omitempty"`
}

type InferenceInput struct {
	ModelID         *string   `json:"model_id,omitempty"`
	StreamID        string    `json:"stream_id"`
	EventCode       string    `json:"event_code"`
	WindowStart     time.Time `json:"window_start"`
	WindowEnd       time.Time `json:"window_end"`
	Score           *float32  `json:"score,omitempty"`
	Threshold       *float32  `json:"threshold,omitempty"`
	Metadata        *string   `json:"metadata,omitempty"`
	SeriesRef       *string   `json:"series_ref,omitempty"`
	FeatureSnapshot *string   `json:"feature_snapshot,omitempty"`
}

type Alert struct {
	ID             string    `json:"id"`
	OrgID          *string   `json:"org_id,omitempty"`
	OrgName        *string   `json:"org_name,omitempty"`
	PatientID      string    `json:"patient_id"`
	PatientName    string    `json:"patient_name"`
	AlertTypeCode  string    `json:"alert_type_code"`
	AlertTypeLabel string    `json:"alert_type_label"`
	LevelCode      string    `json:"level_code"`
	LevelLabel     string    `json:"level_label"`
	StatusCode     string    `json:"status_code"`
	StatusLabel    string    `json:"status_label"`
	CreatedAt      time.Time `json:"created_at"`
	Description    *string   `json:"description,omitempty"`
}

type AlertInput struct {
	PatientID   string  `json:"patient_id"`
	AlertType   string  `json:"alert_type"`
	AlertLevel  string  `json:"alert_level"`
	Status      string  `json:"status"`
	ModelID     *string `json:"model_id,omitempty"`
	InferenceID *string `json:"inference_id,omitempty"`
	Description *string `json:"description,omitempty"`
	LocationWKT *string `json:"location_wkt,omitempty"`
}

type AlertType struct {
	ID          string  `json:"id"`
	Code        string  `json:"code"`
	Description *string `json:"description,omitempty"`
}

type AlertStatus struct {
	ID          string `json:"id"`
	Code        string `json:"code"`
	Description string `json:"description"`
	StepOrder   int    `json:"step_order"`
}

type AlertAssignment struct {
	AlertID          string    `json:"alert_id"`
	AssigneeUserID   string    `json:"assignee_user_id"`
	AssigneeName     *string   `json:"assignee_name,omitempty"`
	AssignedByUserID *string   `json:"assigned_by_user_id,omitempty"`
	AssignedByName   *string   `json:"assigned_by_name,omitempty"`
	AssignedAt       time.Time `json:"assigned_at"`
}

type AlertAck struct {
	ID          string    `json:"id"`
	AlertID     string    `json:"alert_id"`
	AckByUserID *string   `json:"ack_by_user_id,omitempty"`
	AckByName   *string   `json:"ack_by_name,omitempty"`
	AckAt       time.Time `json:"ack_at"`
	Note        *string   `json:"note,omitempty"`
}

type AlertResolution struct {
	ID               string    `json:"id"`
	AlertID          string    `json:"alert_id"`
	ResolvedByUserID *string   `json:"resolved_by_user_id,omitempty"`
	ResolvedByName   *string   `json:"resolved_by_name,omitempty"`
	ResolvedAt       time.Time `json:"resolved_at"`
	Outcome          *string   `json:"outcome,omitempty"`
	Note             *string   `json:"note,omitempty"`
}

type AlertDelivery struct {
	ID                  string    `json:"id"`
	AlertID             string    `json:"alert_id"`
	ChannelID           string    `json:"channel_id"`
	ChannelCode         string    `json:"channel_code"`
	ChannelLabel        string    `json:"channel_label"`
	Target              string    `json:"target"`
	SentAt              time.Time `json:"sent_at"`
	DeliveryStatusID    string    `json:"delivery_status_id"`
	DeliveryStatusCode  string    `json:"delivery_status_code"`
	DeliveryStatusLabel string    `json:"delivery_status_label"`
	ResponsePayload     *string   `json:"response_payload,omitempty"`
}

type ContentRoleActivity struct {
	Role  string `json:"role"`
	Count int    `json:"count"`
}

type ContentCumulativePoint struct {
	Period string `json:"period"`
	Count  int    `json:"count"`
}

type ContentUpdateHeatmapPoint struct {
	Date  string `json:"date"`
	Count int    `json:"count"`
}

type ContentMetrics struct {
	Totals        ContentTotals               `json:"totals"`
	Monthly       []ContentMonthlyPoint       `json:"monthly"`
	Categories    []ContentCategorySlice      `json:"categories"`
	StatusTrends  []ContentStatusTrend        `json:"status_trends"`
	RoleActivity  []ContentRoleActivity       `json:"role_activity"`
	Cumulative    []ContentCumulativePoint    `json:"cumulative"`
	UpdateHeatmap []ContentUpdateHeatmapPoint `json:"update_heatmap"`
}

type ContentItem struct {
	ID            string     `json:"id"`
	Title         string     `json:"title"`
	Summary       *string    `json:"summary,omitempty"`
	Slug          *string    `json:"slug,omitempty"`
	Locale        string     `json:"locale"`
	StatusCode    string     `json:"status_code"`
	StatusLabel   string     `json:"status_label"`
	StatusWeight  int        `json:"status_weight"`
	CategoryCode  string     `json:"category_code"`
	CategoryLabel string     `json:"category_label"`
	TypeCode      string     `json:"type_code"`
	TypeLabel     string     `json:"type_label"`
	AuthorName    *string    `json:"author_name,omitempty"`
	AuthorEmail   *string    `json:"author_email,omitempty"`
	UpdatedAt     time.Time  `json:"updated_at"`
	PublishedAt   *time.Time `json:"published_at,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
	ArchivedAt    *time.Time `json:"archived_at,omitempty"`
}

type ContentFilters struct {
	TypeCode     *string `json:"type_code,omitempty"`
	StatusCode   *string `json:"status_code,omitempty"`
	CategoryCode *string `json:"category_code,omitempty"`
	Search       *string `json:"search,omitempty"`
	Limit        int     `json:"limit"`
	Offset       int     `json:"offset"`
}

type ContentBlock struct {
	ID             string  `json:"id"`
	BlockTypeCode  string  `json:"block_type_code"`
	BlockTypeLabel string  `json:"block_type_label"`
	Position       int     `json:"position"`
	Title          *string `json:"title,omitempty"`
	Content        string  `json:"content"`
}

type ContentAuthor struct {
	UserID     string `json:"user_id"`
	Name       string `json:"name"`
	Email      string `json:"email"`
	StatusCode string `json:"status_code"`
}

type ContentVersion struct {
	ID           string    `json:"id"`
	VersionNo    int       `json:"version_no"`
	CreatedAt    time.Time `json:"created_at"`
	EditorUserID *string   `json:"editor_user_id,omitempty"`
	EditorName   *string   `json:"editor_name,omitempty"`
	ChangeType   string    `json:"change_type"`
	Note         *string   `json:"note,omitempty"`
	Published    bool      `json:"published"`
	Body         string    `json:"body"`
}

type ContentDetail struct {
	ContentItem
	Body                   string         `json:"body"`
	LatestVersionID        *string        `json:"latest_version_id,omitempty"`
	LatestVersionNo        *int           `json:"latest_version_no,omitempty"`
	LatestVersionCreatedAt *time.Time     `json:"latest_version_created_at,omitempty"`
	Blocks                 []ContentBlock `json:"blocks"`
}

type ContentBlockInput struct {
	BlockType string  `json:"block_type"`
	Title     *string `json:"title,omitempty"`
	Content   string  `json:"content"`
	Position  int     `json:"position"`
}

type ContentCreateInput struct {
	Title        string              `json:"title"`
	Summary      *string             `json:"summary,omitempty"`
	Slug         *string             `json:"slug,omitempty"`
	Locale       *string             `json:"locale,omitempty"`
	StatusCode   string              `json:"status_code"`
	CategoryCode string              `json:"category_code"`
	TypeCode     string              `json:"type_code"`
	AuthorEmail  *string             `json:"author_email,omitempty"`
	Body         string              `json:"body"`
	Blocks       []ContentBlockInput `json:"blocks,omitempty"`
	Note         *string             `json:"note,omitempty"`
	PublishedAt  *time.Time          `json:"published_at,omitempty"`
}

type ContentUpdateInput struct {
	Title           *string             `json:"title,omitempty"`
	Summary         *string             `json:"summary,omitempty"`
	Slug            *string             `json:"slug,omitempty"`
	Locale          *string             `json:"locale,omitempty"`
	StatusCode      *string             `json:"status_code,omitempty"`
	CategoryCode    *string             `json:"category_code,omitempty"`
	TypeCode        *string             `json:"type_code,omitempty"`
	AuthorEmail     *string             `json:"author_email,omitempty"`
	Body            *string             `json:"body,omitempty"`
	Blocks          []ContentBlockInput `json:"blocks,omitempty"`
	Note            *string             `json:"note,omitempty"`
	PublishedAt     *time.Time          `json:"published_at,omitempty"`
	ForceNewVersion bool                `json:"force_new_version"`
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
	ID             string     `json:"id"`
	Title          string     `json:"title"`
	StatusCode     string     `json:"status_code"`
	StatusLabel    string     `json:"status_label"`
	CategoryCode   string     `json:"category_code"`
	CategoryLabel  string     `json:"category_label"`
	AuthorName     *string    `json:"author_name,omitempty"`
	AuthorEmail    *string    `json:"author_email,omitempty"`
	PublishedAt    *time.Time `json:"published_at,omitempty"`
	UpdatedAt      time.Time  `json:"updated_at"`
	LastUpdateAt   *time.Time `json:"last_update_at,omitempty"`
	LastEditorName *string    `json:"last_editor_name,omitempty"`
	Updates30d     int        `json:"updates_30d"`
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
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description *string   `json:"description,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
	Permissions []string  `json:"permissions,omitempty"`
}

type RolePermission struct {
	RoleID      string    `json:"role_id"`
	Code        string    `json:"code"`
	Description string    `json:"description,omitempty"`
	GrantedAt   time.Time `json:"granted_at"`
}

type RolePermissionRequest struct {
	Permission string `json:"permission" validate:"required"`
}

type RolePermissionsResponse struct {
	RoleID      string           `json:"role_id"`
	Permissions []RolePermission `json:"permissions"`
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
	TS         time.Time      `json:"ts"`
	Action     string         `json:"action"`
	Entity     *string        `json:"entity,omitempty"`
	UserID     *string        `json:"user_id,omitempty"`
	ActorEmail *string        `json:"actor_email,omitempty"`
	Details    map[string]any `json:"details,omitempty"`
}

type SystemSettings struct {
	BrandName          string    `json:"brand_name"`
	SupportEmail       string    `json:"support_email"`
	PrimaryColor       string    `json:"primary_color"`
	SecondaryColor     *string   `json:"secondary_color,omitempty"`
	LogoURL            *string   `json:"logo_url,omitempty"`
	ContactPhone       *string   `json:"contact_phone,omitempty"`
	DefaultLocale      string    `json:"default_locale"`
	DefaultTimezone    string    `json:"default_timezone"`
	MaintenanceMode    bool      `json:"maintenance_mode"`
	MaintenanceMessage *string   `json:"maintenance_message,omitempty"`
	UpdatedAt          time.Time `json:"updated_at"`
	UpdatedBy          *string   `json:"updated_by,omitempty"`
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
