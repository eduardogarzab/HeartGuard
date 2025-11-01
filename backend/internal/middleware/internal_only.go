package middleware

import (
	"net"
	"net/http"
	"strings"
)

// LoopbackOnly rejects requests that do not originate from the local host.
func LoopbackOnly(logger Logger, extra []*net.IPNet) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if !isLoopbackRequest(r, extra) {
				if logger != nil {
					logger.Info(
						"blocked non-loopback request",
						Field("remote_addr", r.RemoteAddr),
						Field("xff", r.Header.Get("X-Forwarded-For")),
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

func isLoopbackRequest(r *http.Request, extra []*net.IPNet) bool {
	// For loopback check, we validate the direct connection (RemoteAddr),
	// not the end-user IP from X-Forwarded-For headers.
	// This ensures requests come from trusted proxy (nginx) or localhost.
	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		host = r.RemoteAddr
	}
	ip := net.ParseIP(host)
	if ip == nil {
		return false
	}
	if ip.IsLoopback() {
		return true
	}
	for _, network := range extra {
		if network.Contains(ip) {
			return true
		}
	}
	return false
}

func extractClientIP(r *http.Request) net.IP {
	if xff := r.Header.Get("X-Forwarded-For"); xff != "" {
		parts := strings.Split(xff, ",")
		if len(parts) > 0 {
			if ip := net.ParseIP(strings.TrimSpace(parts[0])); ip != nil {
				return ip
			}
		}
	}
	if xrip := r.Header.Get("X-Real-IP"); xrip != "" {
		if ip := net.ParseIP(strings.TrimSpace(xrip)); ip != nil {
			return ip
		}
	}

	host, _, err := net.SplitHostPort(r.RemoteAddr)
	if err != nil {
		host = r.RemoteAddr
	}
	return net.ParseIP(host)
}
