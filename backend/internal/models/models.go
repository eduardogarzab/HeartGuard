package models

import "time"

type Organization struct {
	ID        string    `json:"id"`
	Code      string    `json:"code"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
}

type OrganizationStats struct {
	MemberCount    int `json:"member_count"`
	PatientCount   int `json:"patient_count"`
	CareTeamCount  int `json:"care_team_count"`
	CaregiverCount int `json:"caregiver_count"`
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

type AlertResponseStats struct {
	AvgAckDuration     time.Duration `json:"avg_ack_duration"`
	AvgResolveDuration time.Duration `json:"avg_resolve_duration"`
}

type MetricsOverview struct {
	AvgResponseMs      float64         `json:"avg_response_ms"`
	TotalUsers         int             `json:"total_users"`
	TotalOrganizations int             `json:"total_organizations"`
	TotalMemberships   int             `json:"total_memberships"`
	PendingInvitations int             `json:"pending_invitations"`
	RecentOperations   []OperationStat `json:"recent_operations"`
}

type Patient struct {
	ID              string     `json:"id"`
	OrgID           *string    `json:"org_id,omitempty"`
	OrgName         *string    `json:"org_name,omitempty"`
	Name            string     `json:"name"`
	Birthdate       *time.Time `json:"birthdate,omitempty"`
	SexCode         *string    `json:"sex_code,omitempty"`
	SexLabel        *string    `json:"sex_label,omitempty"`
	RiskLevelID     *string    `json:"risk_level_id,omitempty"`
	RiskLevelCode   *string    `json:"risk_level_code,omitempty"`
	RiskLevelLabel  *string    `json:"risk_level_label,omitempty"`
	ProfilePhotoURL *string    `json:"profile_photo_url,omitempty"`
	CreatedAt       time.Time  `json:"created_at"`
}

type PatientInput struct {
	OrgID           *string    `json:"org_id,omitempty"`
	Name            string     `json:"name"`
	Birthdate       *time.Time `json:"birthdate,omitempty"`
	SexCode         *string    `json:"sex_code,omitempty"`
	RiskLevelID     *string    `json:"risk_level_id,omitempty"`
	ProfilePhotoURL *string    `json:"profile_photo_url,omitempty"`
}

type CareTeam struct {
	ID        string    `json:"id"`
	OrgID     *string   `json:"org_id,omitempty"`
	OrgName   *string   `json:"org_name,omitempty"`
	Name      string    `json:"name"`
	CreatedAt time.Time `json:"created_at"`
}

type CareTeamInput struct {
	OrgID *string `json:"org_id,omitempty"`
	Name  string  `json:"name"`
}

type CareTeamUpdateInput struct {
	OrgID *string `json:"org_id,omitempty"`
	Name  *string `json:"name,omitempty"`
}

type CareTeamMember struct {
	CareTeamID   string    `json:"care_team_id"`
	CareTeamName string    `json:"care_team_name"`
	UserID       string    `json:"user_id"`
	UserName     string    `json:"user_name"`
	UserEmail    string    `json:"user_email"`
	RoleID       string    `json:"role_id"`
	RoleCode     string    `json:"role_code"`
	RoleLabel    string    `json:"role_label"`
	JoinedAt     time.Time `json:"joined_at"`
}

type CareTeamMemberInput struct {
	UserID string `json:"user_id"`
	RoleID string `json:"role_id"`
}

type CareTeamMemberUpdateInput struct {
	RoleID *string `json:"role_id,omitempty"`
}

type PatientCareTeamLink struct {
	CareTeamID   string `json:"care_team_id"`
	CareTeamName string `json:"care_team_name"`
	PatientID    string `json:"patient_id"`
	PatientName  string `json:"patient_name"`
}

type PatientLocation struct {
	ID          string    `json:"id"`
	PatientID   string    `json:"patient_id"`
	PatientName *string   `json:"patient_name,omitempty"`
	RecordedAt  time.Time `json:"recorded_at"`
	Latitude    float64   `json:"latitude"`
	Longitude   float64   `json:"longitude"`
	Source      *string   `json:"source,omitempty"`
	AccuracyM   *float64  `json:"accuracy_m,omitempty"`
}

type PatientLocationInput struct {
	PatientID  string     `json:"patient_id"`
	RecordedAt *time.Time `json:"recorded_at,omitempty"`
	Latitude   float64    `json:"latitude"`
	Longitude  float64    `json:"longitude"`
	Source     *string    `json:"source,omitempty"`
	AccuracyM  *float64   `json:"accuracy_m,omitempty"`
}

type PatientLocationFilters struct {
	PatientID *string    `json:"patient_id,omitempty"`
	From      *time.Time `json:"from,omitempty"`
	To        *time.Time `json:"to,omitempty"`
}

type CaregiverRelationshipType struct {
	ID    string `json:"id"`
	Code  string `json:"code"`
	Label string `json:"label"`
}

type CaregiverRelationshipTypeInput struct {
	Code  string `json:"code"`
	Label string `json:"label"`
}

type CaregiverRelationshipTypeUpdateInput struct {
	Code  *string `json:"code,omitempty"`
	Label *string `json:"label,omitempty"`
}

type CaregiverAssignment struct {
	PatientID             string     `json:"patient_id"`
	PatientName           string     `json:"patient_name"`
	CaregiverID           string     `json:"caregiver_id"`
	CaregiverName         string     `json:"caregiver_name"`
	CaregiverEmail        string     `json:"caregiver_email"`
	RelationshipTypeID    *string    `json:"relationship_type_id,omitempty"`
	RelationshipTypeCode  *string    `json:"relationship_type_code,omitempty"`
	RelationshipTypeLabel *string    `json:"relationship_type_label,omitempty"`
	IsPrimary             bool       `json:"is_primary"`
	StartedAt             time.Time  `json:"started_at"`
	EndedAt               *time.Time `json:"ended_at,omitempty"`
	Note                  *string    `json:"note,omitempty"`
}

type CaregiverAssignmentInput struct {
	PatientID          string     `json:"patient_id"`
	CaregiverID        string     `json:"caregiver_id"`
	RelationshipTypeID *string    `json:"relationship_type_id,omitempty"`
	IsPrimary          *bool      `json:"is_primary,omitempty"`
	StartedAt          *time.Time `json:"started_at,omitempty"`
	EndedAt            *time.Time `json:"ended_at,omitempty"`
	Note               *string    `json:"note,omitempty"`
}

type CaregiverAssignmentUpdateInput struct {
	RelationshipTypeID *string    `json:"relationship_type_id,omitempty"`
	IsPrimary          *bool      `json:"is_primary,omitempty"`
	StartedAt          *time.Time `json:"started_at,omitempty"`
	EndedAt            *time.Time `json:"ended_at,omitempty"`
	Note               *string    `json:"note,omitempty"`
	ClearEndedAt       bool       `json:"clear_ended_at"`
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
	ID    string  `json:"id"`
	Code  string  `json:"code"`
	Label *string `json:"label,omitempty"`
}

type Service struct {
	ID                string     `json:"id"`
	Name              string     `json:"name"`
	URL               string     `json:"url"`
	Description       *string    `json:"description,omitempty"`
	CreatedAt         time.Time  `json:"created_at"`
	LatestStatusCode  *string    `json:"latest_status_code,omitempty"`
	LatestStatusLabel *string    `json:"latest_status_label,omitempty"`
	LatestCheckedAt   *time.Time `json:"latest_checked_at,omitempty"`
	LatestLatencyMs   *int       `json:"latest_latency_ms,omitempty"`
	LatestVersion     *string    `json:"latest_version,omitempty"`
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

type GroundTruthLabel struct {
	ID                string     `json:"id"`
	PatientID         string     `json:"patient_id"`
	PatientName       string     `json:"patient_name"`
	EventTypeID       string     `json:"event_type_id"`
	EventTypeCode     string     `json:"event_type_code"`
	EventTypeLabel    string     `json:"event_type_label"`
	Onset             time.Time  `json:"onset"`
	OffsetAt          *time.Time `json:"offset_at,omitempty"`
	AnnotatedByUserID *string    `json:"annotated_by_user_id,omitempty"`
	AnnotatedByName   *string    `json:"annotated_by_name,omitempty"`
	Source            *string    `json:"source,omitempty"`
	Note              *string    `json:"note,omitempty"`
}

type GroundTruthLabelCreateInput struct {
	EventTypeID       string     `json:"event_type_id"`
	Onset             time.Time  `json:"onset"`
	OffsetAt          *time.Time `json:"offset_at,omitempty"`
	AnnotatedByUserID *string    `json:"annotated_by_user_id,omitempty"`
	Source            *string    `json:"source,omitempty"`
	Note              *string    `json:"note,omitempty"`
}

type GroundTruthLabelUpdateInput struct {
	EventTypeID          *string    `json:"event_type_id,omitempty"`
	Onset                *time.Time `json:"onset,omitempty"`
	OffsetAt             *time.Time `json:"offset_at,omitempty"`
	OffsetAtSet          bool       `json:"-"`
	AnnotatedByUserID    *string    `json:"annotated_by_user_id,omitempty"`
	AnnotatedByUserIDSet bool       `json:"-"`
	Source               *string    `json:"source,omitempty"`
	SourceSet            bool       `json:"-"`
	Note                 *string    `json:"note,omitempty"`
	NoteSet              bool       `json:"-"`
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
	ID              string           `json:"id"`
	Name            string           `json:"name"`
	Email           string           `json:"email"`
	Status          string           `json:"status"`
	ProfilePhotoURL *string          `json:"profile_photo_url,omitempty"`
	CreatedAt       time.Time        `json:"created_at"`
	Memberships     []UserMembership `json:"memberships"`
	Roles           []UserRole       `json:"roles"`
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

type RoleAssignment struct {
	UserID     string    `json:"user_id"`
	UserName   string    `json:"user_name"`
	UserEmail  string    `json:"user_email"`
	AssignedAt time.Time `json:"assigned_at"`
}

type UserRole struct {
	RoleID      string     `json:"role_id"`
	RoleName    string     `json:"role_name"`
	Description *string    `json:"description,omitempty"`
	AssignedAt  *time.Time `json:"assigned_at,omitempty"`
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

type RiskLevel struct {
	ID     string `json:"id"`
	Code   string `json:"code"`
	Label  string `json:"label"`
	Weight *int   `json:"weight,omitempty"`
}

type TeamMemberRole struct {
	ID    string `json:"id"`
	Code  string `json:"code"`
	Label string `json:"label"`
}
