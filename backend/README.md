# HeartGuard Superadmin API (Go)

## Descripción

API para superadministración: organizaciones, invitaciones, membresías, usuarios, API keys y auditoría.  
**Autenticación de demo:**  
- `X-Demo-Superadmin: 1`  
- `Authorization: Bearer let-me-in`

## Requisitos

- **Go** 1.22+
- **PostgreSQL** 14+ ya inicializado
- Variable `DATABASE_URL` en `.env`

## Setup

```bash
cp .env.example .env
nano .env
make dev
```

## Health Check

```bash
curl -i http://localhost:8080/healthz
```

## Autenticación demo

- Header:  
    ```bash
    -H "X-Demo-Superadmin: 1"
    ```
- Token:  
    ```bash
    -H "Authorization: Bearer let-me-in"
    ```

## Endpoints principales

- **Organizaciones:** CRUD
- **Invitaciones:** crear / consumir
- **Miembros:** añadir / eliminar
- **Usuarios:** listar / cambiar status
- **API keys:** crear / asignar permisos / eliminar / listar
- **Auditoría:** listar logs con filtros

## Smoke Test

1. **Listar organizaciones:**
     ```bash
     curl -s -H "X-Demo-Superadmin: 1" http://localhost:8080/v1/superadmin/organizations
     ```
2. **Crear organización:**
     ```bash
     curl -s -X POST -H "X-Demo-Superadmin: 1" -H "Content-Type: application/json" \
         -d '{"code":"FAM-TEST","name":"Familia Test"}' \
         http://localhost:8080/v1/superadmin/organizations
     ```
3. **Ver auditoría:**
     ```bash
     curl -s -H "X-Demo-Superadmin: 1" http://localhost:8080/v1/superadmin/audit-logs
     ```
4. **Crear API key:**
     ```bash
     openssl rand -hex 32
     curl -s -X POST -H "X-Demo-Superadmin: 1" -H "Content-Type: application/json" \
         -d '{"label":"demo","raw_key":"prueba123456789123456789123456789123456789"}' \
         http://localhost:8080/v1/superadmin/api-keys
     ```
5. **Buscar usuarios:**
     ```bash
     curl -s -H "X-Demo-Superadmin: 1" "http://localhost:8080/v1/superadmin/users?q=admin&limit=10"
     ```

## Troubleshooting

- **API key inválida:**  `raw_key` mínimo 32 caracteres

- **DATABASE_URL faltante:**  
    ```bash
    export $(grep -v '^#' .env | xargs)
    ```
- **Módulos Go faltantes:**  
    ```bash
    go mod tidy
    ```
- **jq faltante:**  
    ```bash
    sudo apt install jq
    ```
