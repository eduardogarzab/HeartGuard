package middleware

import (
    "net"
    "net/http"
)

// LoopbackOnly rejects requests that do not originate from the local host.
func LoopbackOnly(logger Logger) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            if !isLoopbackRequest(r) {
                if logger != nil {
                    logger.Info(
                        "blocked non-loopback request",
                        Field("remote_addr", r.RemoteAddr),
                        Field("path", r.URL.Path),
                    )
                }
                http.Error(w, "forbidden", http.StatusForbidden)
                return
            }
            next.ServeHTTP(w, r)
        })
    }
}

func isLoopbackRequest(r *http.Request) bool {
    host, _, err := net.SplitHostPort(r.RemoteAddr)
    if err != nil {
        host = r.RemoteAddr
    }
    ip := net.ParseIP(host)
    if ip == nil {
        return false
    }
    return ip.IsLoopback()
}
