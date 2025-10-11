package audit

import (
	"context"
	"encoding/json"
	"time"

	"github.com/jackc/pgx/v5"
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
	tx, err := pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer tx.Rollback(ctx) // safe even after commit

	var logID string
	if err := tx.QueryRow(ctx, `
INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, ip)
VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW(), $5)
RETURNING id::text
`, userID, action, entity, entityID, ip).Scan(&logID); err != nil {
		return err
	}

	if len(details) > 0 {
		batch := &pgx.Batch{}
		for key, val := range details {
			raw, err := json.Marshal(val)
			if err != nil {
				return err
			}
			batch.Queue(`
INSERT INTO audit_log_details (audit_log_id, detail_key, value_json)
VALUES ($1, $2, $3)
ON CONFLICT (audit_log_id, detail_key) DO UPDATE SET value_json = EXCLUDED.value_json
`, logID, key, string(raw))
		}
		br := tx.SendBatch(ctx, batch)
		for i := 0; i < batch.Len(); i++ {
			if _, err := br.Exec(); err != nil {
				br.Close()
				return err
			}
		}
		if err := br.Close(); err != nil {
			return err
		}
	}

	return tx.Commit(ctx)
}

// Ctx limita la operación de auditoría a 2s para no colgar el request principal.
func Ctx(parent context.Context) (context.Context, context.CancelFunc) {
	return context.WithTimeout(parent, 2*time.Second)
}
