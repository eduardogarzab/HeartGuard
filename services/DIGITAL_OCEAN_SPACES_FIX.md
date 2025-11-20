# Solución: Problema de Conectividad a Digital Ocean Spaces

## Problema Identificado

La aplicación desktop no podía subir fotos al microservicio `media`, con el error:
```
ApiException{statusCode=504, error=photo_upload_error, message='media-service no respondio a tiempo'}
```

## Causa Raíz

La VM de microservicios (`heartguard-microservicios` - IP: `129.212.181.53` / `134.199.133.131`) no podía conectarse a **Digital Ocean Spaces** (`atl1.digitaloceanspaces.com` - IP: `134.199.128.128`).

### Análisis Detallado

1. **Problema de Enrutamiento**: La VM tiene asignada la IP `134.199.133.131` en la red `134.199.128.0/20`, y Digital Ocean Spaces usa la IP `134.199.128.128` en el mismo rango.

2. **Comportamiento Incorrecto**: El sistema operativo intentaba alcanzar `134.199.128.128` como si estuviera en la misma red local (capa 2 / Ethernet), enviando paquetes ARP directamente por `eth0`.

3. **ARP Failure**: El comando `ip neigh show` mostraba:
   ```
   134.199.128.128 dev eth0 FAILED
   ```

4. **Ruta Incorrecta**: El tráfico no pasaba por el gateway de Internet, intentando conexión directa que fallaba porque Digital Ocean Spaces no está en la misma red física.

## Soluciones Implementadas

### 1. ✅ Ruta Específica para Digital Ocean Spaces

Agregada ruta estática para forzar que el tráfico a Digital Ocean Spaces salga por el gateway de Internet:

```bash
ip route add 134.199.128.128/32 via 129.212.176.1 dev eth0
```

**Resultado**: El tráfico ahora pasa correctamente por el gateway y llega a Digital Ocean Spaces con latencia <4ms.

### 2. ✅ Persistencia con Systemd

Creado servicio systemd (`/etc/systemd/system/digitalocean-spaces-route.service`) para configurar la ruta automáticamente al iniciar el sistema.

**Script**: `/root/HeartGuard/services/setup-spaces-route.sh`

### 3. ✅ Timeouts Optimizados en boto3

Modificado `/root/HeartGuard/services/media/src/media/storage/spaces_client.py` para incluir:

```python
boto_config = Config(
    connect_timeout=10,    # 10 segundos para conectar
    read_timeout=30,       # 30 segundos para leer/escribir
    retries={
        'max_attempts': 3,  # 3 reintentos automáticos
        'mode': 'standard'
    }
)
```

### 4. ✅ Corrección de Bugs en Código

- **Media Service**: Agregado `from typing import Any` en `media/blueprints/media.py`
- **Gateway Proxy**: Corregido manejo de streams de archivos para evitar agotamiento

## Verificación

```bash
# Verificar ruta
ip route get 134.199.128.128

# Probar conectividad
ping -c 3 134.199.128.128

# Probar HTTPS
curl -I https://heartguard-bucket.atl1.digitaloceanspaces.com

# Verificar servicio systemd
systemctl status digitalocean-spaces-route.service

# Re-aplicar ruta manualmente si es necesario
/root/HeartGuard/services/setup-spaces-route.sh
```

## Comandos Útiles para Diagnóstico

```bash
# Ver tabla de rutas
ip route show

# Ver vecinos ARP
ip neigh show

# Ver qué ruta se usa para una IP específica
ip route get <IP>

# Probar conectividad con timeout
curl --connect-timeout 10 --max-time 30 https://atl1.digitaloceanspaces.com

# Ver logs del servicio de ruta
journalctl -u digitalocean-spaces-route.service -f
```

## Estado Actual

✅ **Conectividad ICMP**: Exitosa (~1-4ms)  
✅ **Conectividad HTTPS**: Exitosa  
✅ **Ruta Persistente**: Configurada con systemd  
✅ **Timeouts**: Optimizados (10s connect, 30s read)  
✅ **Reintentos**: Configurados (3 intentos automáticos)  

## Próximos Pasos Recomendados

1. **Reiniciar servicios** para aplicar los cambios en el código:
   ```bash
   cd /root/HeartGuard/services
   make restart
   ```

2. **Probar subida de foto** desde el desktop app

3. **Monitorear logs** del media service durante las pruebas:
   ```bash
   docker logs -f heartguard-media-service
   # O si está corriendo en Flask directamente:
   tail -f /var/log/media-service.log
   ```

## Notas Importantes

- La ruta específica es necesaria porque Digital Ocean asigna IPs del mismo rango `/20` a diferentes servicios que no están en la misma red local
- El servicio systemd se ejecuta automáticamente al inicio y es idempotente (puede ejecutarse múltiples veces sin problemas)
- Los timeouts de boto3 son apropiados para conexiones con latencia variable
- Si cambias de región en Digital Ocean Spaces, actualiza el script y la IP

---

**Fecha de Resolución**: 2025-11-20  
**Versión**: 1.0
