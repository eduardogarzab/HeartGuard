# 🏥 HeartGuard Backend - Guía de Instalación en Fedora

Esta guía te llevará paso a paso para instalar y ejecutar el backend de HeartGuard en Fedora.

## 📋 Requisitos Previos

- **Fedora 37+** (recomendado Fedora 38/39)
- **Acceso sudo** para instalar paquetes
- **Conexión a internet** para descargar dependencias
- **Mínimo 4GB RAM** y **10GB espacio libre**

## 🛠️ Paso 1: Instalar Docker

### 1.1 Actualizar el sistema
```bash
sudo dnf update -y
```

### 1.2 Instalar Docker
```bash
# Instalar Docker
sudo dnf install -y docker docker-compose

# Habilitar Docker para iniciar automáticamente
sudo systemctl enable docker
sudo systemctl start docker

# Agregar tu usuario al grupo docker (requiere logout/login)
sudo usermod -aG docker $USER

# Verificar instalación
docker --version
docker-compose --version
```

### 1.3 Verificar Docker
```bash
# Probar Docker (después de logout/login)
docker run hello-world
```

## 🐹 Paso 2: Instalar Go

### 2.1 Descargar Go
```bash
# Ir al directorio temporal
cd /tmp

# Descargar Go 1.21 (última versión estable)
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# Verificar descarga
ls -la go1.21.5.linux-amd64.tar.gz
```

### 2.2 Instalar Go
```bash
# Eliminar instalación anterior (si existe)
sudo rm -rf /usr/local/go

# Extraer Go
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# Agregar Go al PATH
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
echo 'export GOPATH=$HOME/go' >> ~/.bashrc
echo 'export PATH=$PATH:$GOPATH/bin' >> ~/.bashrc

# Recargar configuración
source ~/.bashrc

# Verificar instalación
go version
```

### 2.3 Configurar Go
```bash
# Crear directorio de trabajo
mkdir -p $HOME/go/{bin,pkg,src}

# Verificar configuración
go env GOPATH
go env GOROOT
```

## 📦 Paso 3: Instalar Dependencias del Sistema

```bash
# Instalar herramientas necesarias
sudo dnf install -y git curl wget netstat-nat lsof

# Instalar herramientas de desarrollo
sudo dnf groupinstall -y "Development Tools"

# Verificar instalaciones
git --version
curl --version
```

## 📁 Paso 4: Clonar y Preparar el Proyecto

### 4.1 Clonar el repositorio
```bash
# Ir al directorio de proyectos
cd ~/Documents/  # o donde prefieras

# Clonar el repositorio
git clone https://github.com/tu-usuario/HeartGuard.git
cd HeartGuard/backend
```

### 4.2 Verificar archivos
```bash
# Verificar que todos los archivos estén presentes
ls -la
# Deberías ver: main.go, crud.go, monitoring.go, init.sql, docker-compose.yml, etc.
```

## 🚀 Paso 5: Ejecutar el Backend

### 5.1 Construir sin caché (primera vez)
```bash
# Construir todas las imágenes Docker sin usar caché
docker-compose build --no-cache

# Este proceso puede tomar 5-10 minutos la primera vez
```

### 5.2 Levantar los servicios
```bash
# Levantar todos los servicios en segundo plano
docker-compose up -d

# Verificar que todos los servicios estén corriendo
docker-compose ps
```

### 5.3 Verificar logs
```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs backend-go
docker-compose logs postgres
docker-compose logs redis
docker-compose logs influxdb
```

## ✅ Paso 6: Verificar que Todo Funcione

### 6.1 Verificar puertos
```bash
# Verificar que los puertos estén en uso
sudo netstat -tlnp | grep -E ':(8080|5432|6379|8086)'

# O usando lsof
sudo lsof -i :8080  # Backend Go
sudo lsof -i :5432  # PostgreSQL
sudo lsof -i :6379  # Redis
sudo lsof -i :8086  # InfluxDB
```

### 6.2 Probar la API
```bash
# Probar endpoint principal
curl -I http://localhost:8080/api

# Probar endpoint de salud
curl http://localhost:8080/api/health

# Probar login (debería fallar sin credenciales)
curl -X POST http://localhost:8080/admin/login
```

### 6.3 Acceder a la interfaz web
```bash
# Abrir navegador
firefox http://localhost:8080 &
# O
google-chrome http://localhost:8080 &
```

**Credenciales de acceso:**
- **Email:** `admin@heartguard.com`
- **Password:** `admin123`

## 🔧 Comandos Útiles de Docker Compose

### Comandos básicos
```bash
# Ver estado de servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Ver logs de un servicio específico
docker-compose logs -f backend-go

# Reiniciar un servicio
docker-compose restart backend-go

# Reiniciar todos los servicios
docker-compose restart
```

### Comandos de construcción
```bash
# Construir sin caché (cuando hay cambios)
docker-compose build --no-cache

# Construir solo un servicio
docker-compose build --no-cache backend-go

# Reconstruir y levantar
docker-compose up -d --build
```

### Comandos de limpieza
```bash
# Parar todos los servicios
docker-compose down

# Parar y eliminar volúmenes (CUIDADO: elimina datos)
docker-compose down -v

# Parar y eliminar imágenes
docker-compose down --rmi all

# Limpiar todo (servicios, volúmenes, imágenes)
docker-compose down -v --rmi all
```

## 🐛 Solución de Problemas

### Problema: "Docker no está corriendo"
```bash
# Iniciar Docker
sudo systemctl start docker

# Verificar estado
sudo systemctl status docker

# Habilitar inicio automático
sudo systemctl enable docker
```

### Problema: "Puerto ya está en uso"
```bash
# Ver qué está usando el puerto
sudo lsof -i :8080

# Parar el proceso (reemplazar PID)
sudo kill -9 <PID>

# O cambiar puerto en docker-compose.yml
```

### Problema: "Base de datos no conecta"
```bash
# Ver logs de PostgreSQL
docker-compose logs postgres

# Reiniciar base de datos
docker-compose restart postgres

# Verificar conexión
docker-compose exec postgres psql -U heartguard -d heartguard -c "SELECT 1;"
```

### Problema: "Backend no responde"
```bash
# Ver logs del backend
docker-compose logs backend-go

# Reconstruir backend
docker-compose build --no-cache backend-go
docker-compose up -d backend-go

# Verificar variables de entorno
docker-compose exec backend-go env
```

### Problema: "Archivos estáticos no cargan"
```bash
# Verificar que los archivos existan
ls -la static/css/style.css
ls -la static/js/app.js

# Reconstruir imagen
docker-compose build --no-cache backend-go
```

## 🔄 Flujo de Desarrollo

### Cuando hagas cambios en el código:
```bash
# 1. Parar servicios
docker-compose down

# 2. Reconstruir sin caché
docker-compose build --no-cache

# 3. Levantar servicios
docker-compose up -d

# 4. Verificar logs
docker-compose logs -f backend-go
```

### Para desarrollo continuo:
```bash
# Mantener logs abiertos en una terminal
docker-compose logs -f

# En otra terminal, hacer cambios y reconstruir
docker-compose build --no-cache backend-go
docker-compose up -d backend-go
```

## 📊 Verificación Final

Después de seguir todos los pasos, deberías poder:

1. ✅ **Acceder a http://localhost:8080**
2. ✅ **Hacer login con admin@heartguard.com / admin123**
3. ✅ **Ver el dashboard con estadísticas**
4. ✅ **Navegar por todas las secciones**
5. ✅ **Ver datos en las tablas**
6. ✅ **Usar todas las funcionalidades**

## 🆘 Obtener Ayuda

Si tienes problemas:

1. **Verifica los logs:** `docker-compose logs`
2. **Revisa el estado:** `docker-compose ps`
3. **Prueba el script de testing:** `./test_web.sh`
4. **Verifica los puertos:** `sudo netstat -tlnp`

## 📝 Notas Importantes

- **Primera ejecución:** Puede tomar 10-15 minutos
- **Memoria:** El sistema usa ~2GB de RAM
- **Espacio:** Los volúmenes Docker ocupan ~3GB
- **Puertos:** Asegúrate de que 8080, 5432, 6379, 8086 estén libres
- **Firewall:** Si tienes firewall, abre los puertos necesarios

---

**🎉 ¡Felicidades! Tu backend de HeartGuard está listo para usar.**

Para más información, consulta el archivo `README_WEB.md` o ejecuta `./test_web.sh` para verificar que todo funcione correctamente.
