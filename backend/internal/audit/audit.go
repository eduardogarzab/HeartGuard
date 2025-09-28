package audit

import (
	"context"
	"encoding/json"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

// Write inserta un registro de auditoría con user_id (opcional), acción, entidad, entity_id (opcional),
// detalles (json) e IP (opcional). Usa NOW() para la marca de tiempo.
func Write(
	ctx context.Context,
	pool *pgxpool.Pool,
	userID *string,
	action string,
	entity string,
	entityID *string,
	details map[string]any,
	ip *string,
) error {
	var b []byte
	if details != nil {
		if bb, err := json.Marshal(details); err == nil {
			b = bb
		}
	}
	_, err := pool.Exec(ctx, `
INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, details, ip)
VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW(), $5, $6)
`, userID, action, entity, entityID, b, ip)
	return err
}

// Ctx limita la operación de auditoría a 2s para no colgar el request principal.
func Ctx(parent context.Context) (context.Context, context.CancelFunc) {
	return context.WithTimeout(parent, 2*time.Second)
}
