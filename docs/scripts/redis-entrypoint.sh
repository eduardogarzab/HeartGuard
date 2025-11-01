#!/bin/sh
# Redis entrypoint script for TLS + optional password

set -e

# Build redis-server command
CMD="redis-server"
CMD="$CMD --appendonly no"
CMD="$CMD --port 0"
CMD="$CMD --tls-port 6380"
CMD="$CMD --tls-cert-file /etc/redis/certs/redis.crt"
CMD="$CMD --tls-key-file /etc/redis/certs/redis.key"
CMD="$CMD --tls-ca-cert-file /etc/redis/certs/ca.crt"
CMD="$CMD --tls-auth-clients optional"

# Add password if set
if [ -n "$REDIS_PASSWORD" ]; then
    CMD="$CMD --requirepass $REDIS_PASSWORD"
    echo "🔒 Redis TLS habilitado con password"
else
    echo "🔒 Redis TLS habilitado sin password"
fi

# Execute
exec $CMD
