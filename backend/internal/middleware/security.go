package middleware

import "net/http"

func SecurityHeaders() func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'")
            w.Header().Set("X-Frame-Options", "DENY")
            w.Header().Set("Referrer-Policy", "no-referrer")
            w.Header().Set("X-Content-Type-Options", "nosniff")
            w.Header().Set("X-XSS-Protection", "0")
            next.ServeHTTP(w, r)
        })
    }
}
