package db

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"os"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"heartguard-superadmin/internal/config"
)

func NewPool(cfg *config.Config) (*pgxpool.Pool, error) {
	pc, err := pgxpool.ParseConfig(cfg.DatabaseURL)
	if err != nil {
		return nil, err
	}
	
	// Configuración SSL/TLS para producción
	if cfg.Env == "prod" {
		// Cargar CA certificate
		caCert, err := os.ReadFile("certs/ca.crt")
		if err == nil {
			caCertPool := x509.NewCertPool()
			if caCertPool.AppendCertsFromPEM(caCert) {
				pc.ConnConfig.TLSConfig = &tls.Config{
					RootCAs:            caCertPool,
					ServerName:         "postgres", // Nombre del servidor (hostname del contenedor)
					InsecureSkipVerify: false,      // Verificar certificado del servidor
					MinVersion:         tls.VersionTLS12,
				}
				fmt.Println("✅ PostgreSQL SSL/TLS habilitado con verificación de certificado")
			}
		} else {
			fmt.Printf("⚠️  No se pudo cargar CA cert para PostgreSQL: %v\n", err)
		}
	}
	
	pc.MaxConns = 10
	pc.MinConns = 1
	pc.MaxConnLifetime = time.Hour
	pc.MaxConnIdleTime = 15 * time.Minute
	pc.HealthCheckPeriod = time.Minute
	return pgxpool.NewWithConfig(context.Background(), pc)
}
