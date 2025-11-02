# Configuración de Seguridad - HeartGuard

## ✅ Configuración Actual (SEGURA)

### Gateway (Puerto 8000) - PÚBLICO
```
Host: 0.0.0.0 (todas las interfaces)
Puerto: 8000
CORS: Habilitado (origins: "*")
Accesible desde: Internet/Web/Mobile
```

**Razón**: Este ES el punto de entrada único para todos los clientes externos.

### Auth Service (Puerto 5001) - PRIVADO
```
Host: 127.0.0.1 (solo localhost)
Puerto: 5001
CORS: Deshabilitado
Accesible desde: Solo localhost (Gateway puede conectar)
```

**Razón**: Servicio interno que NO debe ser accesible desde Internet.

### PostgreSQL (Puerto 5432) - PRIVADO
```
Host: 0.0.0.0 (Docker interno)
Puerto: 5432
Accesible desde: Solo red interna Docker
```

**Razón**: Base de datos nunca debe ser accesible públicamente.

## 🔒 Verificación de Seguridad

### Verificar configuración actual:
```bash
# Mostrar qué interfaces están escuchando
netstat -tlnp | grep -E "(8000|5001|5432)"

# Resultado esperado:
# tcp  0  0.0.0.0:8000     ... LISTEN  (Gateway - PÚBLICO)
# tcp  127.0.0.1:5001     ... LISTEN  (Auth - PRIVADO)
# tcp  0.0.0.0:5432      ... LISTEN  (Postgres - Docker interno)
```

### Pruebas de acceso:
```bash
# ✅ Gateway desde Internet (DEBE funcionar)
curl http://<IP-PUBLICA>:8000/health/

# ✅ Auth desde localhost (DEBE funcionar)
curl http://127.0.0.1:5001/health/

# ❌ Auth desde Internet (DEBE FALLAR)
curl http://<IP-PUBLICA>:5001/health/
# Error: Connection refused (CORRECTO)

# ❌ PostgreSQL desde Internet (DEBE FALLAR)
psql -h <IP-PUBLICA> -U heartguard_app -d heartguard
# Error: Connection refused (CORRECTO)
```

## 🔥 Reglas de Firewall Recomendadas

### Para servidor Linux (iptables/ufw):

```bash
# Permitir Gateway (público)
sudo ufw allow 8000/tcp comment "HeartGuard Gateway - Public API"

# Bloquear Auth Service desde exterior
sudo ufw deny 5001/tcp comment "HeartGuard Auth - Internal Only"

# Bloquear PostgreSQL desde exterior
sudo ufw deny 5432/tcp comment "PostgreSQL - Internal Only"

# Bloquear Superadmin desde exterior
sudo ufw deny 8080/tcp comment "Superadmin - VPN Only"
```

### Para Azure/AWS (Security Groups):

```
Inbound Rules:
┌──────────┬──────────┬────────────┬─────────────────────┐
│ Protocol │ Port     │ Source     │ Description         │
├──────────┼──────────┼────────────┼─────────────────────┤
│ TCP      │ 8000     │ 0.0.0.0/0  │ Gateway (Público)   │
│ TCP      │ 5001     │ 127.0.0.1  │ Auth (Solo local)   │
│ TCP      │ 5432     │ 10.0.0.0/8 │ Postgres (VPC)      │
│ TCP      │ 8080     │ VPN IP     │ Superadmin (VPN)    │
│ TCP      │ 22       │ Admin IPs  │ SSH (Admin)         │
└──────────┴──────────┴────────────┴─────────────────────┘
```

## 🌐 Flujo de Comunicación

```
[Internet] 
    ↓
    ↓ HTTPS (recomendado con nginx/traefik)
    ↓
[Gateway :8000] ← CORS habilitado, acceso público
    ↓
    ↓ HTTP localhost
    ↓
[Auth Service :5001] ← SIN CORS, solo localhost
    ↓
    ↓ PostgreSQL protocol
    ↓
[PostgreSQL :5432] ← Red interna Docker
```

### ✅ Petición Válida (desde navegador web):

```
1. Cliente Web → Gateway (http://IP-PUBLICA:8000/auth/login/user)
   ✅ Permitido (Gateway escucha en 0.0.0.0)
   ✅ CORS headers presentes

2. Gateway → Auth Service (http://127.0.0.1:5001/auth/login/user)
   ✅ Permitido (conexión localhost a localhost)
   ✅ No necesita CORS (server-to-server)

3. Auth Service → PostgreSQL (localhost:5432)
   ✅ Permitido (Docker interno)

4. Gateway ← Auth Service (respuesta con tokens)
   ✅ Respuesta exitosa

5. Cliente Web ← Gateway (respuesta con tokens + CORS headers)
   ✅ Cliente recibe respuesta
```

### ❌ Petición Bloqueada (intento de ataque):

```
1. Atacante → Auth Service (http://IP-PUBLICA:5001/auth/login/user)
   ❌ BLOQUEADO (Auth solo escucha en 127.0.0.1)
   ❌ Connection refused

2. Atacante → PostgreSQL (IP-PUBLICA:5432)
   ❌ BLOQUEADO (Firewall/Security Group)
   ❌ Connection timeout
```

## 📝 Checklist de Seguridad

### Desarrollo
- [x] Gateway escucha en 0.0.0.0:8000
- [x] Auth Service escucha en 127.0.0.1:5001
- [x] Auth Service SIN CORS habilitado
- [x] Gateway CON CORS habilitado
- [x] PostgreSQL en red Docker interna

### Producción (Pendiente)
- [ ] Configurar CORS del Gateway con lista específica de dominios permitidos
- [ ] Implementar HTTPS con certificados SSL/TLS (nginx/traefik)
- [ ] Configurar firewall con reglas específicas
- [ ] Configurar rate limiting en Gateway
- [ ] Implementar WAF (Web Application Firewall)
- [ ] Habilitar logs de auditoría
- [ ] Configurar alertas de seguridad
- [ ] Implementar backup automatizado cifrado

## 🛠️ Configuración Actual en Código

### Gateway - Expuesto con CORS
```python
# services/gateway/src/gateway/extensions.py
CORS(app, resources={
    r"/*": {
        "origins": "*",  # ⚠️ Cambiar en producción
        "methods": ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
    }
})

# Gateway escucha en todas las interfaces
app.run(host='0.0.0.0', port=8000)
```

### Auth Service - Privado sin CORS
```python
# services/auth/src/auth/app.py
def create_app() -> Flask:
    app = Flask(__name__)
    configure_app(app)
    init_extensions(app)
    # NO habilitamos CORS - este servicio es solo interno
    register_blueprints(app)
    register_error_handlers(app)
    return app

# Auth Service escucha SOLO en localhost
app.run(host='127.0.0.1', port=5001)
```

## 🔍 Comandos de Verificación

```bash
# Verificar servicios activos
./check-services.sh

# Ver interfaces de red
netstat -tlnp | grep -E "(8000|5001)"

# Probar acceso desde localhost
curl http://127.0.0.1:5001/health/  # DEBE funcionar
curl http://127.0.0.1:8000/health/  # DEBE funcionar

# Probar acceso desde IP externa (simular Internet)
curl http://10.0.0.4:5001/health/  # DEBE FALLAR
curl http://10.0.0.4:8000/health/  # DEBE funcionar
```

## 📊 Resumen de Puertos

| Servicio      | Puerto | Host       | CORS     | Público |
|---------------|--------|------------|----------|---------|
| Gateway       | 8000   | 0.0.0.0    | ✅ Sí    | ✅ Sí   |
| Auth Service  | 5001   | 127.0.0.1  | ❌ No    | ❌ No   |
| PostgreSQL    | 5432   | 0.0.0.0*   | N/A      | ❌ No   |
| Superadmin    | 8080   | 0.0.0.0    | ❌ No    | ⚠️ VPN  |

*PostgreSQL escucha en 0.0.0.0 dentro de Docker, pero el firewall debe bloquearlo desde Internet.

## ⚠️ Notas Importantes

1. **Gateway es el ÚNICO servicio que debe ser accesible desde Internet**
2. **Auth Service NUNCA debe ser accesible públicamente**
3. **PostgreSQL NUNCA debe ser accesible desde fuera de la red interna**
4. **En producción, cambiar CORS origins de "*" a lista específica de dominios**
5. **Usar HTTPS en producción (nginx/traefik con Let's Encrypt)**
6. **Implementar rate limiting para prevenir DDoS**

## 📞 Contacto

Para más información:
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Arquitectura completa
- [DEPLOYMENT_STATUS.md](./DEPLOYMENT_STATUS.md) - Estado del despliegue

---

**Última actualización**: 2 de Noviembre, 2025  
**Responsable**: Security Team
