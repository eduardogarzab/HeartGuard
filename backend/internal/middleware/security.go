package middleware

import "net/http"

func SecurityHeaders() func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

			// Definimos las fuentes permitidas para los CDNs
			const (
				cdnScripts = "https://unpkg.com https://cdn.jsdelivr.net"
				
				// *** INICIO DE CORRECCIÓN CSP 1 ***
				// Añadimos 'raw.githubusercontent.com' para los íconos de marcador
				cdnImages = "https://*.tile.openstreetmap.org https://raw.githubusercontent.com https://cdnjs.cloudflare.com"
				
				// *** INICIO DE CORRECCIÓN CSP 2 ***
				// Añadimos los dominios de scripts a connect-src para permitir sourcemaps (.map)
				cdnConnect = "https://unpkg.com https://cdn.jsdelivr.net"
			)

			// Creamos la política CSP
			csp := []string{
				"default-src 'self'",
				
				// Permitir scripts de 'self', 'unsafe-inline' (que ya tenías) y los CDNs
				"script-src 'self' 'unsafe-inline' " + cdnScripts,
				
				// Permitir estilos de 'self', 'unsafe-inline' (que ya tenías) y los CDNs
				"style-src 'self' 'unsafe-inline' " + cdnScripts,
				
				// Permitir imágenes de 'self', data: y las fuentes de Leaflet (tiles y marcadores)
				"img-src 'self' data: " + cdnImages,

				// *** AÑADIDO: Directiva connect-src ***
				"connect-src 'self' " + cdnConnect,
				
				"font-src 'self'",
				"frame-ancestors 'none'",
			}

			// Unimos las directivas CSP en un solo string
			policy := ""
			for i, directive := range csp {
				policy += directive
				if i < len(csp)-1 {
					policy += "; "
				}
			}

			// Establecemos la cabecera CSP modificada
			w.Header().Set("Content-Security-Policy", policy)

			// Mantenemos el resto de tus cabeceras de seguridad
			w.Header().Set("X-Frame-Options", "DENY")
			w.Header().Set("Referrer-Policy", "no-referrer")
			w.Header().Set("X-Content-Type-Options", "nosniff")
			w.Header().Set("X-XSS-Protection", "0")
			
			next.ServeHTTP(w, r)
		})
	}
}