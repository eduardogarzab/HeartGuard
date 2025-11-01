package rediscli

import (
	"context"
	"crypto/tls"
	"crypto/x509"
	"fmt"
	"log"
	"os"

	"github.com/redis/go-redis/v9"
)

var Ctx = context.Background()

func New(url string) *redis.Client {
	opt, err := redis.ParseURL(url)
	if err != nil { 
		log.Fatalf("redis parse: %v", err) 
	}
	
	// Si la URL usa rediss:// (TLS), configurar certificados
	if opt.TLSConfig != nil {
		// Cargar CA certificate
		caCert, err := os.ReadFile("certs/ca.crt")
		if err == nil {
			caCertPool := x509.NewCertPool()
			if caCertPool.AppendCertsFromPEM(caCert) {
				opt.TLSConfig = &tls.Config{
					RootCAs:            caCertPool,
					InsecureSkipVerify: false, // Verificar certificado del servidor
					MinVersion:         tls.VersionTLS12,
				}
				fmt.Println("✅ Redis TLS habilitado con verificación de certificado")
			}
		} else {
			fmt.Printf("⚠️  No se pudo cargar CA cert para Redis: %v (usando TLS sin verificación)\n", err)
			// Fallback: TLS sin verificación (no recomendado en producción)
			opt.TLSConfig = &tls.Config{
				InsecureSkipVerify: true,
				MinVersion:         tls.VersionTLS12,
			}
		}
	}
	
	return redis.NewClient(opt)
}
