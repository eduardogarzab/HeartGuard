#!/bin/bash
# Script para generar certificados SSL/TLS auto-firmados para PostgreSQL y Redis
# Para producción REAL, usar certificados de Let's Encrypt o una CA confiable

set -e

echo "🔐 Generando certificados SSL/TLS para HeartGuard..."

# Crear directorios
mkdir -p certs/postgres certs/redis

# Generar CA (Certificate Authority)
echo "📜 Generando CA (Certificate Authority)..."
openssl req -new -x509 -days 3650 -nodes \
    -out certs/ca.crt \
    -keyout certs/ca.key \
    -subj "/C=MX/ST=NuevoLeon/L=Monterrey/O=HeartGuard/OU=DevOps/CN=HeartGuard-CA"

# === POSTGRESQL ===
echo "🐘 Generando certificados para PostgreSQL..."

# Server key
openssl genrsa -out certs/postgres/server.key 2048
chmod 600 certs/postgres/server.key

# Create SAN config for PostgreSQL
cat > certs/postgres/san.cnf <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = MX
ST = NuevoLeon
L = Monterrey
O = HeartGuard
OU = Database
CN = postgres

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = postgres
DNS.2 = localhost
DNS.3 = heartguard-postgres
IP.1 = 127.0.0.1
IP.2 = 172.18.0.2
EOF

# Server CSR with SAN
openssl req -new -key certs/postgres/server.key \
    -out certs/postgres/server.csr \
    -config certs/postgres/san.cnf

# Server certificate with SAN
openssl x509 -req -in certs/postgres/server.csr \
    -CA certs/ca.crt -CAkey certs/ca.key \
    -CAcreateserial -out certs/postgres/server.crt \
    -days 3650 \
    -extensions v3_req \
    -extfile certs/postgres/san.cnf

# Copy CA
cp certs/ca.crt certs/postgres/ca.crt

# PostgreSQL requiere permisos específicos
chmod 600 certs/postgres/server.key
chmod 644 certs/postgres/server.crt
chmod 644 certs/postgres/ca.crt

# Cambiar owner si corremos como root (Docker)
if [ "$EUID" -eq 0 ]; then
    chown 999:999 certs/postgres/server.key certs/postgres/server.crt certs/postgres/ca.crt
fi

echo "✅ Certificados PostgreSQL generados"

# === REDIS ===
echo "🔴 Generando certificados para Redis..."

# Server key
openssl genrsa -out certs/redis/redis.key 2048
chmod 600 certs/redis/redis.key

# Create SAN config for Redis
cat > certs/redis/san.cnf <<EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C = MX
ST = NuevoLeon
L = Monterrey
O = HeartGuard
OU = Cache
CN = redis

[v3_req]
keyUsage = keyEncipherment, dataEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = redis
DNS.2 = localhost
DNS.3 = heartguard-redis
IP.1 = 127.0.0.1
IP.2 = 172.18.0.3
EOF

# Server CSR with SAN
openssl req -new -key certs/redis/redis.key \
    -out certs/redis/redis.csr \
    -config certs/redis/san.cnf

# Server certificate with SAN
openssl x509 -req -in certs/redis/redis.csr \
    -CA certs/ca.crt -CAkey certs/ca.key \
    -CAcreateserial -out certs/redis/redis.crt \
    -days 3650 \
    -extensions v3_req \
    -extfile certs/redis/san.cnf

# Copy CA
cp certs/ca.crt certs/redis/ca.crt

# Redis permisos
chmod 600 certs/redis/redis.key
chmod 644 certs/redis/redis.crt
chmod 644 certs/redis/ca.crt

# Cambiar owner si corremos como root (Docker usa uid 999 para redis)
if [ "$EUID" -eq 0 ]; then
    chown 999:999 certs/redis/redis.key certs/redis/redis.crt certs/redis/ca.crt
fi

echo "✅ Certificados Redis generados"

# === CLIENTE ===
echo "👤 Generando certificados de cliente..."

# Client key
openssl genrsa -out certs/client.key 2048
chmod 600 certs/client.key

# Client CSR
openssl req -new -key certs/client.key \
    -out certs/client.csr \
    -subj "/C=MX/ST=NuevoLeon/L=Monterrey/O=HeartGuard/OU=Backend/CN=heartguard-backend"

# Client certificate
openssl x509 -req -in certs/client.csr \
    -CA certs/ca.crt -CAkey certs/ca.key \
    -CAcreateserial -out certs/client.crt \
    -days 3650

chmod 644 certs/client.crt

echo "✅ Certificados de cliente generados"

# Limpiar CSR, seriales y configs temporales
rm -f certs/postgres/server.csr certs/postgres/san.cnf
rm -f certs/redis/redis.csr certs/redis/san.cnf
rm -f certs/client.csr certs/ca.srl

echo ""
echo "🎉 ¡Certificados SSL/TLS generados exitosamente!"
echo ""
echo "📁 Estructura de certificados:"
echo "   certs/"
echo "   ├── ca.crt (CA pública)"
echo "   ├── ca.key (CA privada - ¡PROTEGER!)"
echo "   ├── client.crt (cliente)"
echo "   ├── client.key (cliente privada)"
echo "   ├── postgres/"
echo "   │   ├── server.crt"
echo "   │   ├── server.key"
echo "   │   └── ca.crt"
echo "   └── redis/"
echo "       ├── redis.crt"
echo "       ├── redis.key"
echo "       └── ca.crt"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Estos son certificados AUTO-FIRMADOS para desarrollo/testing"
echo "   - Para producción REAL usa Let's Encrypt o una CA confiable"
echo "   - NO commitear certs/*.key a git (ya está en .gitignore)"
echo "   - Rotar certificados cada 90 días en producción"
echo ""
echo "🚀 Ahora puedes iniciar los servicios con: make prod-deploy"
