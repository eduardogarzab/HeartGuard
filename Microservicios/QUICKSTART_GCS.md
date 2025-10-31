# Quick Start - Media Service con GCS

## ⚡ Inicio Rápido

### Subir archivo (Método Recomendado)

```bash
cd /home/jserangelli/Eduardo/HeartGuard/Microservicios
./upload_to_media.sh archivo.jpg usr-owner-id
```

**Ejemplo específico:**
```bash
./upload_to_media.sh misterjesa.jpeg usr-mendo-test
```

---

## 📋 Alternativa con cURL

```bash
# 1. Encode file to base64
CONTENT=$(base64 -w 0 archivo.jpg)

# 2. Upload
curl -X POST http://34.70.7.33:5000/media/upload \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"archivo.jpg\",
    \"mime_type\": \"image/jpeg\",
    \"size_bytes\": 12048,
    \"owner_id\": \"usr-123\",
    \"content\": \"$CONTENT\"
  }" | jq .

# 3. Download (la signed URL viene en la respuesta)
curl -o archivo_descargado.jpg "SIGNED_URL_AQUI"
```

---

## ✅ Verificar

```bash
# Ver archivos subidos
curl http://34.70.7.33:5000/media | jq .

# Health check
curl http://34.70.7.33:5000/media/health | jq .
```

---

## 📚 Documentación Completa

Para más detalles, ver: **`GCS_INTEGRATION.md`**

---

**Problema resuelto:** ✅ URLs firmadas ahora funcionan correctamente con Google Cloud Storage (antes daban "Access Denied").
