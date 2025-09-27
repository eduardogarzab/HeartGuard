package audit

import (
	"context"
	"encoding/json"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
)

func Write(ctx context.Context, pool *pgxpool.Pool, userID *string, action, entity string, entityID *string, details map[string]any) error {
	var b []byte
	if details != nil {
		if bb, err := json.Marshal(details); err == nil {
			b = bb
		}
	}
	_, err := pool.Exec(ctx,
		`INSERT INTO audit_logs (id, user_id, action, entity, entity_id, ts, details)
		 VALUES (gen_random_uuid(), $1, $2, $3, $4, NOW(), $5)`,
		userID, action, entity, entityID, b,
	)
	return err
}

func Ctx(parent context.Context) (context.Context, context.CancelFunc) {
	return context.WithTimeout(parent, 2*time.Second)
}
