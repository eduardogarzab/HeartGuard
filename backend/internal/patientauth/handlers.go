package patientauth

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"go.uber.org/zap"

	"heartguard-superadmin/internal/config"
	"heartguard-superadmin/internal/session"
)

type Handlers struct {
	cfg      *config.Config
	repo     *Repository
	sessions *session.Manager
	logger   *zap.Logger
}

func NewHandlers(cfg *config.Config, repo *Repository, sessions *session.Manager, logger *zap.Logger) *Handlers {
	return &Handlers{
		cfg:      cfg,
		repo:     repo,
		sessions: sessions,
		logger:   logger,
	}
}

type LoginRequest struct {
	Email    string `json:"email"`
	Password string `json:"password"`
}

type LoginResponse struct {
	Success bool              `json:"success"`
	Token   string            `json:"token,omitempty"`
	Patient *PatientResponse  `json:"patient,omitempty"`
	Error   string            `json:"error,omitempty"`
}

type RegisterRequest struct {
	OrgID      string  `json:"org_id"`
	PersonName string  `json:"person_name"`
	Email      string  `json:"email"`
	Password   string  `json:"password"`
	Birthdate  *string `json:"birthdate,omitempty"`
	SexID      *string `json:"sex_id,omitempty"`
}

type RegisterResponse struct {
	Success bool             `json:"success"`
	Patient *PatientResponse `json:"patient,omitempty"`
	Error   string           `json:"error,omitempty"`
}

type PatientResponse struct {
	ID            string     `json:"id"`
	OrgID         string     `json:"org_id"`
	PersonName    string     `json:"person_name"`
	Email         string     `json:"email"`
	EmailVerified bool       `json:"email_verified"`
	Birthdate     *time.Time `json:"birthdate,omitempty"`
	CreatedAt     time.Time  `json:"created_at"`
}

// Login maneja el login de pacientes
func (h *Handlers) Login(w http.ResponseWriter, r *http.Request) {
	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.jsonError(w, "Datos inválidos", http.StatusBadRequest)
		return
	}

	email := strings.TrimSpace(strings.ToLower(req.Email))
	password := strings.TrimSpace(req.Password)

	if email == "" || password == "" {
		h.jsonError(w, "Email y contraseña son requeridos", http.StatusBadRequest)
		return
	}

	patient, err := h.repo.AuthenticatePatient(r.Context(), email, password)
	if err != nil {
		if err == ErrInvalidCredentials {
			h.jsonError(w, "Credenciales inválidas", http.StatusUnauthorized)
			return
		}
		if err == ErrEmailNotVerified {
			h.jsonError(w, "Debes verificar tu email antes de iniciar sesión", http.StatusForbidden)
			return
		}
		h.logger.Error("patient authentication error", zap.Error(err))
		h.jsonError(w, "Error al autenticar", http.StatusInternalServerError)
		return
	}

	// Update last login
	if err := h.repo.UpdateLastLogin(r.Context(), patient.ID); err != nil {
		h.logger.Error("update last login error", zap.Error(err))
	}

	// Issue session token
	token, _, _, err := h.sessions.Issue(r.Context(), patient.ID)
	if err != nil {
		h.logger.Error("session issue error", zap.Error(err))
		h.jsonError(w, "Error al crear sesión", http.StatusInternalServerError)
		return
	}

	resp := LoginResponse{
		Success: true,
		Token:   token,
		Patient: &PatientResponse{
			ID:            patient.ID,
			OrgID:         *patient.OrgID,
			PersonName:    patient.Name,
			Email:         *patient.Email,
			EmailVerified: patient.EmailVerified,
			Birthdate:     patient.Birthdate,
			CreatedAt:     patient.CreatedAt,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(resp)
}

// Register maneja el registro de nuevos pacientes
func (h *Handlers) Register(w http.ResponseWriter, r *http.Request) {
	var req RegisterRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.jsonError(w, "Datos inválidos", http.StatusBadRequest)
		return
	}

	// Validaciones
	if req.PersonName == "" || req.Email == "" || req.Password == "" || req.OrgID == "" {
		h.jsonError(w, "Nombre, email, contraseña y organización son requeridos", http.StatusBadRequest)
		return
	}

	if len(req.Password) < 8 {
		h.jsonError(w, "La contraseña debe tener al menos 8 caracteres", http.StatusBadRequest)
		return
	}

	// Parse birthdate if provided
	var birthdate *time.Time
	if req.Birthdate != nil && *req.Birthdate != "" {
		t, err := time.Parse("2006-01-02", *req.Birthdate)
		if err != nil {
			h.jsonError(w, "Formato de fecha inválido (use YYYY-MM-DD)", http.StatusBadRequest)
			return
		}
		birthdate = &t
	}

	input := RegisterInput{
		OrgID:      req.OrgID,
		PersonName: strings.TrimSpace(req.PersonName),
		Email:      strings.TrimSpace(strings.ToLower(req.Email)),
		Password:   req.Password,
		Birthdate:  birthdate,
		SexID:      req.SexID,
	}

	patient, err := h.repo.RegisterPatient(r.Context(), input)
	if err != nil {
		if err == ErrEmailAlreadyExists {
			h.jsonError(w, "Este email ya está registrado", http.StatusConflict)
			return
		}
		h.logger.Error("patient registration error", zap.Error(err))
		h.jsonError(w, "Error al registrar paciente", http.StatusInternalServerError)
		return
	}

	resp := RegisterResponse{
		Success: true,
		Patient: &PatientResponse{
			ID:            patient.ID,
			OrgID:         *patient.OrgID,
			PersonName:    patient.Name,
			Email:         *patient.Email,
			EmailVerified: patient.EmailVerified,
			Birthdate:     patient.Birthdate,
			CreatedAt:     patient.CreatedAt,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(resp)
}

// VerifyEmail marca el email del paciente como verificado
func (h *Handlers) VerifyEmail(w http.ResponseWriter, r *http.Request) {
	var req struct {
		PatientID string `json:"patient_id"`
		Token     string `json:"token"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.jsonError(w, "Datos inválidos", http.StatusBadRequest)
		return
	}

	if req.PatientID == "" || req.Token == "" {
		h.jsonError(w, "ID de paciente y token son requeridos", http.StatusBadRequest)
		return
	}

	// TODO: Validar token de verificación (implementar sistema de tokens de verificación)
	// Por ahora, solo verificar directamente
	if err := h.repo.VerifyPatientEmail(r.Context(), req.PatientID); err != nil {
		if err == ErrPatientNotFound {
			h.jsonError(w, "Paciente no encontrado", http.StatusNotFound)
			return
		}
		h.logger.Error("verify email error", zap.Error(err))
		h.jsonError(w, "Error al verificar email", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]any{
		"success": true,
		"message": "Email verificado exitosamente",
	})
}

// ResetPassword solicita un reset de contraseña
func (h *Handlers) ResetPassword(w http.ResponseWriter, r *http.Request) {
	var req struct {
		Email string `json:"email"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		h.jsonError(w, "Datos inválidos", http.StatusBadRequest)
		return
	}

	email := strings.TrimSpace(strings.ToLower(req.Email))
	if email == "" {
		h.jsonError(w, "Email es requerido", http.StatusBadRequest)
		return
	}

	// TODO: Implementar sistema de tokens de reset de contraseña y envío de email
	// Por ahora solo verificar que el paciente existe
	_, _, err := h.repo.FindPatientByEmail(r.Context(), email)
	if err != nil {
		// No revelamos si el email existe o no por seguridad
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		json.NewEncoder(w).Encode(map[string]any{
			"success": true,
			"message": "Si el email existe, recibirás instrucciones para resetear tu contraseña",
		})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusOK)
	json.NewEncoder(w).Encode(map[string]any{
		"success": true,
		"message": "Si el email existe, recibirás instrucciones para resetear tu contraseña",
	})
}

func (h *Handlers) jsonError(w http.ResponseWriter, message string, status int) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]any{
		"success": false,
		"error":   message,
	})
}
