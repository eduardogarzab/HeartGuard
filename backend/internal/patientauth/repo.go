package patientauth

import (
	"context"
	"errors"
	"time"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"golang.org/x/crypto/bcrypt"

	"heartguard-superadmin/internal/models"
)

var (
	ErrPatientNotFound    = errors.New("paciente no encontrado")
	ErrInvalidCredentials = errors.New("credenciales inválidas")
	ErrEmailAlreadyExists = errors.New("email ya registrado")
	ErrEmailNotVerified   = errors.New("email no verificado")
)

type Repository struct {
	pool *pgxpool.Pool
}

func NewRepository(pool *pgxpool.Pool) *Repository {
	return &Repository{pool: pool}
}

// FindPatientByEmail busca un paciente por email para autenticación
func (r *Repository) FindPatientByEmail(ctx context.Context, email string) (*models.Patient, string, error) {
	var (
		id            string
		personName    string
		patientEmail  string
		passwordHash  string
		emailVerified bool
		orgID         string
		lastLoginAt   *time.Time
	)

	err := r.pool.QueryRow(ctx,
		`SELECT id, person_name, email, password_hash, email_verified, org_id, last_login_at
		 FROM heartguard.sp_patient_find_by_email($1)`,
		email,
	).Scan(&id, &personName, &patientEmail, &passwordHash, &emailVerified, &orgID, &lastLoginAt)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return nil, "", ErrPatientNotFound
		}
		return nil, "", err
	}

	patient := &models.Patient{
		ID:            id,
		OrgID:         &orgID,
		Name:          personName,
		Email:         &patientEmail,
		EmailVerified: emailVerified,
		LastLoginAt:   lastLoginAt,
	}

	return patient, passwordHash, nil
}

// AuthenticatePatient valida las credenciales de un paciente
func (r *Repository) AuthenticatePatient(ctx context.Context, email, password string) (*models.Patient, error) {
	patient, passwordHash, err := r.FindPatientByEmail(ctx, email)
	if err != nil {
		if errors.Is(err, ErrPatientNotFound) {
			return nil, ErrInvalidCredentials
		}
		return nil, err
	}

	if err := bcrypt.CompareHashAndPassword([]byte(passwordHash), []byte(password)); err != nil {
		return nil, ErrInvalidCredentials
	}

	if !patient.EmailVerified {
		return nil, ErrEmailNotVerified
	}

	return patient, nil
}

// UpdateLastLogin actualiza la fecha de último login del paciente
func (r *Repository) UpdateLastLogin(ctx context.Context, patientID string) error {
	id, err := uuid.Parse(patientID)
	if err != nil {
		return err
	}

	var success bool
	err = r.pool.QueryRow(ctx,
		`SELECT heartguard.sp_patient_update_last_login($1)`,
		id,
	).Scan(&success)

	if err != nil {
		return err
	}

	if !success {
		return ErrPatientNotFound
	}

	return nil
}

// RegisterPatient registra un nuevo paciente con email y password
func (r *Repository) RegisterPatient(ctx context.Context, input RegisterInput) (*models.Patient, error) {
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(input.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	orgID, err := uuid.Parse(input.OrgID)
	if err != nil {
		return nil, err
	}

	var sexID *uuid.UUID
	if input.SexID != nil && *input.SexID != "" {
		parsed, err := uuid.Parse(*input.SexID)
		if err != nil {
			return nil, err
		}
		sexID = &parsed
	}

	var (
		id            string
		personName    string
		email         string
		emailVerified bool
		retOrgID      string
		birthdate     *time.Time
		retSexID      *string
		riskLevelID   *string
		photoURL      *string
		createdAt     time.Time
		lastLoginAt   *time.Time
	)

	err = r.pool.QueryRow(ctx,
		`SELECT id, person_name, email, email_verified, org_id, birthdate, sex_id, 
		        risk_level_id, profile_photo_url, created_at, last_login_at
		 FROM heartguard.sp_patient_register($1, $2, $3, $4, $5, $6)`,
		orgID,
		input.PersonName,
		input.Email,
		string(hashedPassword),
		input.Birthdate,
		sexID,
	).Scan(&id, &personName, &email, &emailVerified, &retOrgID, &birthdate, &retSexID,
		&riskLevelID, &photoURL, &createdAt, &lastLoginAt)

	if err != nil {
		// Check for unique constraint violation (duplicate email)
		if errors.Is(err, pgx.ErrNoRows) || (err != nil && err.Error() == "Email ya registrado") {
			return nil, ErrEmailAlreadyExists
		}
		return nil, err
	}

	patient := &models.Patient{
		ID:              id,
		OrgID:           &retOrgID,
		Name:            personName,
		Email:           &email,
		EmailVerified:   emailVerified,
		Birthdate:       birthdate,
		RiskLevelID:     riskLevelID,
		ProfilePhotoURL: photoURL,
		CreatedAt:       createdAt,
		LastLoginAt:     lastLoginAt,
	}

	return patient, nil
}

// VerifyPatientEmail marca el email del paciente como verificado
func (r *Repository) VerifyPatientEmail(ctx context.Context, patientID string) error {
	id, err := uuid.Parse(patientID)
	if err != nil {
		return err
	}

	var success bool
	err = r.pool.QueryRow(ctx,
		`SELECT heartguard.sp_patient_verify_email($1)`,
		id,
	).Scan(&success)

	if err != nil {
		return err
	}

	if !success {
		return ErrPatientNotFound
	}

	return nil
}

// SetPatientPassword actualiza el password de un paciente
func (r *Repository) SetPatientPassword(ctx context.Context, patientID, password string) error {
	id, err := uuid.Parse(patientID)
	if err != nil {
		return err
	}

	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return err
	}

	var success bool
	err = r.pool.QueryRow(ctx,
		`SELECT heartguard.sp_patient_set_password($1, $2)`,
		id,
		string(hashedPassword),
	).Scan(&success)

	if err != nil {
		return err
	}

	if !success {
		return ErrPatientNotFound
	}

	return nil
}

// RegisterInput datos para registrar un paciente
type RegisterInput struct {
	OrgID      string
	PersonName string
	Email      string
	Password   string
	Birthdate  *time.Time
	SexID      *string
}
