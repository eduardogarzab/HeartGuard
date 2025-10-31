# Media Service - Google Cloud Storage Integration

## 📋 Resumen

El servicio de media ahora está integrado con **Google Cloud Storage (GCS)** para almacenar y servir archivos de forma segura mediante URLs firmadas.

---

## ✅ Estado de la Integración

- ✅ **Credenciales**: Configuradas en `/run/secrets/gcp-sa`
- ✅ **Bucket**: `heartguard-system`
- ✅ **Upload**: Funcionando con contenido base64
- ✅ **Signed URLs**: Generándose correctamente (válidas por 60 minutos)
- ✅ **Download**: Archivos accesibles mediante signed URLs
- ✅ **Biblioteca**: google-cloud-storage >= 2.10.0

---

## 🔧 Configuración

### Variables de Entorno

```bash
# En .env
GCS_BUCKET=heartguard-system
MEDIA_MAX_FILE_SIZE_MB=50
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-sa
```

### Credenciales de GCS

Las credenciales se almacenan en:
```
/home/jserangelli/Eduardo/HeartGuard/Microservicios/secrets/gcp-sa.json
```

**Proyecto GCP:**
- Project ID: `gleaming-realm-469419-a9`
- Service Account: `751259101579-compute@developer.gserviceaccount.com`

**Permisos Requeridos:**
- `storage.objects.create` - Crear objetos
- `storage.objects.get` - Leer objetos
- `storage.objects.delete` - Eliminar objetos
- `storage.buckets.get` - Acceder a información del bucket

---

## 📤 Subir Archivos

### Endpoint

```
POST /media/upload
```

### Formato del Payload

```json
{
  "filename": "image.jpg",
  "mime_type": "image/jpeg",
  "size_bytes": 12048,
  "owner_id": "usr-123",
  "content": "BASE64_ENCODED_CONTENT"
}
```

### Ejemplo con cURL (JSON)

```bash
# 1. Encode file to base64
CONTENT_BASE64=$(base64 -w 0 /path/to/file.jpg)

# 2. Upload
curl -X POST "http://34.70.7.33:5000/media/upload" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"filename\": \"photo.jpg\",
    \"mime_type\": \"image/jpeg\",
    \"size_bytes\": 11554,
    \"owner_id\": \"usr-test\",
    \"content\": \"$CONTENT_BASE64\"
  }"
```

### Ejemplo con cURL (XML)

```bash
# Create XML payload
cat > upload.xml << EOF
<upload>
  <filename>photo.jpg</filename>
  <mime_type>image/jpeg</mime_type>
  <size_bytes>11554</size_bytes>
  <owner_id>usr-test</owner_id>
  <content>$(base64 -w 0 /path/to/file.jpg)</content>
</upload>
EOF

# Upload
curl -X POST "http://34.70.7.33:5000/media/upload" \
  -H "Content-Type: application/xml" \
  -H "Accept: application/xml" \
  --data-binary "@upload.xml"
```

### Respuesta Exitosa

```json
{
  "status": "success",
  "code": 201,
  "data": {
    "media": {
      "id": "media-5",
      "filename": "photo.jpg",
      "mime_type": "image/jpeg",
      "size_bytes": 11554,
      "owner_id": "usr-test",
      "bucket": "heartguard-system",
      "created_at": "2025-10-31T01:00:00Z",
      "signed_url": "https://storage.googleapis.com/heartguard-system/media-5?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=..."
    }
  }
}
```

---

## 📥 Descargar Archivos

### Método 1: Usar Signed URL

```bash
# Get media info
RESPONSE=$(curl -s "http://34.70.7.33:5000/media/media-5" -H "Accept: application/json")

# Extract signed URL
SIGNED_URL=$(echo "$RESPONSE" | jq -r '.data.media.signed_url')

# Download file
curl -o downloaded_file.jpg "$SIGNED_URL"
```

### Método 2: Listar y Descargar

```bash
# List all media
curl -s "http://34.70.7.33:5000/media" -H "Accept: application/json" | jq .

# Get specific media with signed URL
curl -s "http://34.70.7.33:5000/media/media-5" -H "Accept: application/json" | jq .
```

---

## 🔒 Características de Seguridad

### URLs Firmadas (Signed URLs)

- ✅ **Validez**: 60 minutos por defecto
- ✅ **Firmadas**: Con private key de la service account
- ✅ **Acceso temporal**: No requiere autenticación adicional
- ✅ **Protocolo**: v4 (más seguro)

### Algoritmo

```
X-Goog-Algorithm: GOOG4-RSA-SHA256
X-Goog-Credential: service-account@project.iam.gserviceaccount.com
X-Goog-Date: 20251031T012711Z
X-Goog-Expires: 3600
X-Goog-SignedHeaders: host
X-Goog-Signature: [firma digital]
```

---

## 🧪 Pruebas

### Test Completo de Upload/Download

```bash
#!/bin/bash

# 1. Create test file
echo "Test content - HeartGuard" > test_file.txt

# 2. Encode to base64
CONTENT=$(base64 -w 0 test_file.txt)

# 3. Upload
RESPONSE=$(curl -s -X POST "http://34.70.7.33:5000/media/upload" \
  -H "Content-Type: application/json" \
  -d "{
    \"filename\": \"test.txt\",
    \"mime_type\": \"text/plain\",
    \"size_bytes\": 30,
    \"owner_id\": \"usr-test\",
    \"content\": \"$CONTENT\"
  }")

echo "Upload response:"
echo "$RESPONSE" | jq .

# 4. Extract signed URL
SIGNED_URL=$(echo "$RESPONSE" | jq -r '.data.media.signed_url')

# 5. Download
echo -e "\nDownloading from signed URL..."
curl -s -o downloaded.txt "$SIGNED_URL"

# 6. Verify
echo -e "\nDownloaded content:"
cat downloaded.txt
```

### Test con Imagen

```bash
# Upload image
CONTENT=$(base64 -w 0 image.jpg)

curl -X POST "http://34.70.7.33:5000/media/upload" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d "{
    \"filename\": \"photo.jpg\",
    \"mime_type\": \"image/jpeg\",
    \"size_bytes\": $(stat -f%z image.jpg),
    \"owner_id\": \"usr-001\",
    \"content\": \"$CONTENT\"
  }" | jq .
```

---

## 📊 Endpoints Disponibles

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/media/health` | Health check del servicio |
| GET | `/media` | Listar todos los archivos |
| GET | `/media/:id` | Obtener info de un archivo específico |
| POST | `/media/upload` | Subir nuevo archivo |
| DELETE | `/media/:id` | Eliminar archivo (requiere admin) |

---

## 🚨 Solución de Problemas

### Error: "Access Denied"

**Problema:**
```xml
<Error>
<Code>AccessDenied</Code>
<Message>Access denied.</Message>
</Error>
```

**Causas:**
1. Signed URL expiró (>60 minutos)
2. Archivo no existe en GCS
3. Credenciales incorrectas

**Solución:**
1. Generar nueva signed URL (GET /media/:id)
2. Verificar que el archivo fue subido correctamente
3. Revisar credenciales en `secrets/gcp-sa.json`

### Error: "Invalid content encoding"

**Problema:** Error 400 al subir archivo

**Solución:**
```bash
# Asegúrate de usar base64 -w 0 (sin line wrapping)
CONTENT=$(base64 -w 0 file.txt)
```

### Error: Bucket no existe

**Solución:**
```bash
# Verificar bucket
gsutil ls gs://heartguard-system

# Crear bucket si no existe
gsutil mb -p gleaming-realm-469419-a9 gs://heartguard-system
```

---

## 📈 Monitoreo

### Ver logs del servicio

```bash
docker logs microservicios-media_service-1 --tail 50
```

### Verificar archivos en GCS

```bash
# List objects in bucket
gsutil ls gs://heartguard-system/

# Get object details
gsutil stat gs://heartguard-system/media-5
```

### Health Check

```bash
curl http://34.70.7.33:5000/media/health | jq .
```

---

## 🔐 Seguridad en Producción

### Recomendaciones

1. ✅ **Credenciales**: Usar secrets de Docker (implementado)
2. ✅ **URLs firmadas**: Validez temporal (60 min)
3. ⚠️ **HTTPS**: Configurar en gateway para producción
4. ⚠️ **RBAC**: Implementar control de acceso por roles
5. ⚠️ **Virus scanning**: Considerar escaneo de archivos
6. ⚠️ **Rate limiting**: Limitar uploads por usuario

### Variables de Entorno Sensibles

```bash
# NO COMPARTIR
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-sa
```

---

## 📚 Referencias

- [Google Cloud Storage - Signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls)
- [Python Client Library](https://googleapis.dev/python/storage/latest/index.html)
- [Service Account Credentials](https://cloud.google.com/iam/docs/service-accounts)

---

## ✅ Checklist de Validación

- [x] Credenciales de GCS configuradas
- [x] Bucket `heartguard-system` accesible
- [x] Upload de archivos funcionando
- [x] Generación de signed URLs
- [x] Download mediante signed URLs
- [x] Soporte JSON y XML
- [x] Error handling implementado
- [ ] HTTPS en producción
- [ ] Rate limiting
- [ ] Virus scanning

---

**Estado:** ✅ **Operacional**  
**Última actualización:** 31 de Octubre, 2025  
**Contacto:** Equipo HeartGuard
