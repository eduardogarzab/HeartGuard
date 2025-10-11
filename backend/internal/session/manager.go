package session

import (
    "context"
    "crypto/rand"
    "encoding/base64"
    "encoding/json"
    "errors"
    "net/http"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "github.com/google/uuid"
    redis "github.com/redis/go-redis/v9"

    "heartguard-superadmin/internal/config"
)

const (
    sessionKeyPrefix = "session:"
    csrfKeyPrefix    = "csrf:"
    flashKeyPrefix   = "flash:"
    denyKeyPrefix    = "jwt:deny:"
    cookieName       = "hg_session"
    guestCSRFPrefix  = "csrf:guest:"
    guestCSRFCookie  = "hg_guest_csrf"
)

var (
    ErrNoSession    = errors.New("session not found")
    ErrInvalidCSRF  = errors.New("invalid csrf token")
    ErrMissingCSRF  = errors.New("missing csrf token")
)

type Manager struct {
    cfg   *config.Config
    redis *redis.Client
}

type Flash struct {
    Type    string `json:"type"`
    Message string `json:"message"`
}

func NewManager(cfg *config.Config, redis *redis.Client) *Manager {
    return &Manager{cfg: cfg, redis: redis}
}

func (m *Manager) CookieName() string { return cookieName }
func (m *Manager) GuestCookieName() string { return guestCSRFCookie }

func (m *Manager) sessionKey(jti string) string { return sessionKeyPrefix + jti }
func (m *Manager) csrfKey(jti string) string    { return csrfKeyPrefix + jti }
func (m *Manager) flashKey(jti string) string   { return flashKeyPrefix + jti }
func (m *Manager) denyKey(jti string) string    { return denyKeyPrefix + jti }

func (m *Manager) Issue(ctx context.Context, userID string) (token string, jti string, csrf string, err error) {
    jti = uuid.NewString()
    token, err = signJWT(m.cfg.JWTSecret, userID, jti, m.cfg.AccessTokenTTL)
    if err != nil {
        return "", "", "", err
    }
    if err = m.redis.Set(ctx, m.sessionKey(jti), userID, m.cfg.AccessTokenTTL).Err(); err != nil {
        return "", "", "", err
    }
    csrf, err = randomToken()
    if err != nil {
        return "", "", "", err
    }
    if err = m.redis.Set(ctx, m.csrfKey(jti), csrf, m.cfg.AccessTokenTTL).Err(); err != nil {
        return "", "", "", err
    }
    return token, jti, csrf, nil
}

func (m *Manager) Validate(ctx context.Context, token string) (*Claims, error) {
    claims, err := parseJWT(m.cfg.JWTSecret, token)
    if err != nil {
        return nil, err
    }
    if claims.JTI == "" {
        return nil, ErrNoSession
    }
    stored, err := m.redis.Get(ctx, m.sessionKey(claims.JTI)).Result()
    if err != nil {
        if errors.Is(err, redis.Nil) {
            return nil, ErrNoSession
        }
        return nil, err
    }
    if stored != claims.UserID {
        return nil, ErrNoSession
    }
    return claims, nil
}

func (m *Manager) Revoke(ctx context.Context, jti string) {
    _ = m.redis.Del(ctx, m.sessionKey(jti)).Err()
    _ = m.redis.Del(ctx, m.csrfKey(jti)).Err()
    _ = m.redis.Set(ctx, m.denyKey(jti), "revoked", m.cfg.AccessTokenTTL).Err()
}

func (m *Manager) EnsureCSRF(ctx context.Context, jti string) (string, error) {
    if jti == "" {
        return "", ErrNoSession
    }
    token, err := m.redis.Get(ctx, m.csrfKey(jti)).Result()
    if err == nil {
        return token, nil
    }
    if !errors.Is(err, redis.Nil) {
        return "", err
    }
    token, err = randomToken()
    if err != nil {
        return "", err
    }
    if err := m.redis.Set(ctx, m.csrfKey(jti), token, m.cfg.AccessTokenTTL).Err(); err != nil {
        return "", err
    }
    return token, nil
}

func (m *Manager) ValidateCSRF(ctx context.Context, jti, token string) error {
    if token == "" {
        return ErrMissingCSRF
    }
    stored, err := m.redis.Get(ctx, m.csrfKey(jti)).Result()
    if err != nil {
        if errors.Is(err, redis.Nil) {
            return ErrInvalidCSRF
        }
        return err
    }
    if subtleConstantTimeCompare(stored, token) {
        return nil
    }
    return ErrInvalidCSRF
}

func (m *Manager) PushFlash(ctx context.Context, jti string, flash Flash) {
    if jti == "" {
        return
    }
    payload, err := json.Marshal(flash)
    if err != nil {
        return
    }
    key := m.flashKey(jti)
    if err := m.redis.RPush(ctx, key, payload).Err(); err == nil {
        _ = m.redis.Expire(ctx, key, m.cfg.AccessTokenTTL).Err()
    }
}

func (m *Manager) PopFlashes(ctx context.Context, jti string) []Flash {
    if jti == "" {
        return nil
    }
    key := m.flashKey(jti)
    vals, err := m.redis.LRange(ctx, key, 0, -1).Result()
    if err != nil {
        return nil
    }
    _ = m.redis.Del(ctx, key).Err()
    out := make([]Flash, 0, len(vals))
    for _, v := range vals {
        var f Flash
        if err := json.Unmarshal([]byte(v), &f); err == nil {
            out = append(out, f)
        }
    }
    return out
}

func randomToken() (string, error) {
    b := make([]byte, 32)
    if _, err := rand.Read(b); err != nil {
        return "", err
    }
    return base64.RawURLEncoding.EncodeToString(b), nil
}

func subtleConstantTimeCompare(a, b string) bool {
    if len(a) != len(b) {
        return false
    }
    var res byte
    for i := 0; i < len(a); i++ {
        res |= a[i] ^ b[i]
    }
    return res == 0
}

func (m *Manager) RemainingTTL(ctx context.Context, jti string) time.Duration {
    if jti == "" {
        return 0
    }
    ttl, err := m.redis.TTL(ctx, m.sessionKey(jti)).Result()
    if err != nil {
        return 0
    }
    return ttl
}

func (m *Manager) Refresh(ctx context.Context, jti string) {
    if jti == "" {
        return
    }
    ttl := m.cfg.AccessTokenTTL
    _ = m.redis.Expire(ctx, m.sessionKey(jti), ttl).Err()
    _ = m.redis.Expire(ctx, m.csrfKey(jti), ttl).Err()
}

func (m *Manager) SessionCookie(token string, ttl time.Duration) *http.Cookie {
	return &http.Cookie{
		Name:     cookieName,
		Value:    token,
		HttpOnly: true,
		Secure:   m.cfg.SecureCookies,
		SameSite: http.SameSiteStrictMode,
		Path:     "/",
		Expires:  time.Now().Add(ttl),
	}
}func (m *Manager) ClearCookie() *http.Cookie {
    return &http.Cookie{
        Name:     cookieName,
        Value:    "",
        Path:     "/",
        MaxAge:   -1,
        HttpOnly: true,
        Secure:   m.cfg.SecureCookies,
        SameSite: http.SameSiteStrictMode,
        Expires:  time.Unix(0, 0),
    }
}

func (m *Manager) IssueGuestCSRF(ctx context.Context, ttl time.Duration) (string, error) {
    token, err := randomToken()
    if err != nil {
        return "", err
    }
    if ttl <= 0 {
        ttl = 10 * time.Minute
    }
    if err := m.redis.Set(ctx, guestCSRFPrefix+token, "1", ttl).Err(); err != nil {
        return "", err
    }
    return token, nil
}

func (m *Manager) ValidateGuestCSRF(ctx context.Context, token string) error {
    if token == "" {
        return ErrMissingCSRF
    }
    _, err := m.redis.Get(ctx, guestCSRFPrefix+token).Result()
    if err != nil {
        if errors.Is(err, redis.Nil) {
            return ErrInvalidCSRF
        }
        return err
    }
    return nil
}

func (m *Manager) ConsumeGuestCSRF(ctx context.Context, token string) {
    if token == "" {
        return
    }
    _ = m.redis.Del(ctx, guestCSRFPrefix+token).Err()
}

func (m *Manager) GuestCSRFCookie(token string, ttl time.Duration) *http.Cookie {
	if ttl <= 0 {
		ttl = 10 * time.Minute
	}
	return &http.Cookie{
		Name:     guestCSRFCookie,
		Value:    token,
		HttpOnly: true,
		Secure:   m.cfg.SecureCookies,
		SameSite: http.SameSiteStrictMode,
		Path:     "/login",
		Expires:  time.Now().Add(ttl),
	}
}func (m *Manager) ClearGuestCSRFCookie() *http.Cookie {
    return &http.Cookie{
        Name:     guestCSRFCookie,
        Value:    "",
        Path:     "/login",
        MaxAge:   -1,
        HttpOnly: true,
        Secure:   m.cfg.SecureCookies,
        SameSite: http.SameSiteStrictMode,
        Expires:  time.Unix(0, 0),
    }
}

type Claims struct {
    UserID string `json:"uid"`
    JTI    string `json:"jti"`
    jwt.RegisteredClaims
}

func signJWT(secret, userID, jti string, ttl time.Duration) (string, error) {
    now := time.Now()
    claims := &Claims{
        UserID: userID,
        JTI:    jti,
        RegisteredClaims: jwt.RegisteredClaims{
            Subject:   userID,
            IssuedAt:  jwt.NewNumericDate(now),
            ExpiresAt: jwt.NewNumericDate(now.Add(ttl)),
        },
    }
    t := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
    return t.SignedString([]byte(secret))
}

func parseJWT(secret, token string) (*Claims, error) {
    parsed, err := jwt.ParseWithClaims(token, &Claims{}, func(token *jwt.Token) (any, error) {
        return []byte(secret), nil
    })
    if err != nil {
        return nil, err
    }
    if c, ok := parsed.Claims.(*Claims); ok && parsed.Valid {
        return c, nil
    }
    return nil, jwt.ErrTokenInvalidClaims
}
