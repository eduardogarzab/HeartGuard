package middleware

import (
	"net/http"
	"strings"
)

func SecurityHeaders() func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            csp := []string{
                "default-src 'self'",
                "script-src 'self' https://unpkg.com/leaflet@1.9.4/dist/leaflet.js https://cdnjs.cloudflare.com 'unsafe-inline'",
                "style-src 'self' https://unpkg.com/leaflet@1.9.4/dist/leaflet.css https://cdnjs.cloudflare.com 'unsafe-inline'",
                "img-src 'self' data: https://tiles.stadiamaps.com/ https://unpkg.com/leaflet@1.9.4/dist/images/",
                "font-src 'self'",
                "frame-ancestors 'none'",
                "connect-src 'self' https://unpkg.com",
            }
            w.Header().Set("Content-Security-Policy", strings.Join(csp, "; "))
            w.Header().Set("X-Frame-Options", "DENY")
            w.Header().Set("Referrer-Policy", "no-referrer")
            w.Header().Set("X-Content-Type-Options", "nosniff")
            w.Header().Set("X-XSS-Protection", "0")
            next.ServeHTTP(w, r)
        })
    }
}