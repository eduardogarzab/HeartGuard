# 🏥 HeartGuard Backend - Guía de Instalación en Fedora

Esta guía te llevará paso a paso para instalar y ejecutar el backend de HeartGuard en un sistema Fedora moderno.

## 📋 Requisitos Previos

- **Fedora 37+** (recomendado Fedora 38/39)
- **Acceso `sudo`** para instalar paquetes.
- **Conexión a internet** estable.
- **Mínimo 4GB de RAM** y **10GB de espacio en disco**.

---

## 🛠️ Paso 1: Instalar Docker y Docker Compose (Método Correcto)

El método de instalación de Docker ha cambiado. Los paquetes `docker` y `docker-compose` ya no se usan. Sigue estos pasos para instalar la versión oficial.

### 1.1 Actualizar el Sistema
Asegúrate de que todos tus paquetes estén al día.
```bash
sudo dnf update -y
```

### 1.2 Añadir el Repositorio Oficial de Docker
Esto es necesario para obtener la versión comunitaria (`-ce`) más reciente.
```bash
# Instalar utilidades para manejar repositorios
sudo dnf -y install dnf-utils

# Añadir el repositorio de Docker
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
```

### 1.3 Instalar Docker Engine y el Plugin de Compose
Instalamos los paquetes con los nombres correctos desde el nuevo repositorio.
```bash
# Instala Docker Engine, CLI, Containerd y el plugin oficial de Compose
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### 1.4 Iniciar y Habilitar Docker
```bash
# Iniciar el servicio de Docker
sudo systemctl start docker

# Habilitar Docker para que inicie automáticamente con el sistema
sudo systemctl enable docker

# (Recomendado) Agregar tu usuario al grupo 'docker' para usarlo sin 'sudo'
# IMPORTANTE: Debes CERRAR SESIÓN y volver a iniciarla para que el cambio aplique.
sudo usermod -aG docker $USER
```

### 1.5 Verificar la Instalación
Una vez que hayas reiniciado tu sesión, comprueba que todo funciona. **Nota que `docker-compose` ahora es `docker compose` (con un espacio)**.
```bash
# Verificar la versión de Docker Engine
docker --version

# Verificar la versión del plugin de Compose
docker compose version

# Probar que Docker funciona correctamente
docker run hello-world
```

---

## 🐹 Paso 2: Instalar Go

### 2.1 Instalar Go
```bash
# Ir al directorio temporal
cd /tmp

# Instalar wget si no lo tienes
sudo dnf install -y wget

# Descargar Go 1.21 (puedes verificar la última versión en go.dev/dl) 
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# Eliminar cualquier instalación anterior para asegurar una instalación limpia
sudo rm -rf /usr/local/go

# Extraer el archivo en la ubicación recomendada
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz
```

### 2.2 Configurar las Variables de Entorno de Go
Estos comandos añaden Go a tu PATH de forma permanente.
```bash
# Añadir las rutas al archivo de configuración de tu shell (funciona para bash y zsh)
echo '# GoLang Paths' >> ~/.bashrc
echo 'export GOPATH=$HOME/go' >> ~/.bashrc
echo 'export PATH=$PATH:/usr/local/go/bin:$GOPATH/bin' >> ~/.bashrc

# Aplicar los cambios a tu sesión actual
source ~/.bashrc

# Crear el directorio de trabajo de Go
mkdir -p $GOPATH/{bin,pkg,src}

# Verificar la instalación y configuración
go version
go env GOROOT
go env GOPATH
```

---

## 📦 Paso 3: Instalar Dependencias del Sistema

El paquete `netstat-nat` era incorrecto. `netstat` viene dentro de `net-tools`.

```bash
# Instalar herramientas de desarrollo y utilidades necesarias
sudo dnf groupinstall -y "Development Tools"
sudo dnf install -y git curl wget lsof net-tools

# Verificar instalaciones
git --version
curl --version
```

---

## 📁 Paso 4: Clonar y Preparar el Proyecto

```bash
# Ve a un directorio de tu elección, por ejemplo, Documentos
cd ~/Documents/

# Clona el repositorio 
git clone https://github.com/eduardogarzab/HeartGuard.git
cd HeartGuard/backend

# Verifica que los archivos principales estén presentes
ls -la
```

---

## 🚀 Paso 5: Ejecutar el Backend


### 5.1 Construir las Imágenes Docker
```bash
# Construir todas las imágenes sin usar caché (ideal para la primera vez)
docker compose build --no-cache
```

### 5.2 Levantar los Servicios
```bash
# Levantar todos los servicios en segundo plano (-d para 'detached')
docker compose up -d

# Verificar que todos los contenedores estén corriendo ('Up' o 'running')
docker compose ps
```

### 5.3 Revisar los Logs
```bash
# Ver los logs de un servicio específico para asegurar que inició bien
docker compose logs -f backend-go
```

---

## ✅ Paso 6: Verificar que Todo Funcione

### 6.1 Verificar Puertos
```bash
# Verificar que los puertos principales estén escuchando
sudo netstat -tlnp | grep -E ':(8080|5432|6379|8086)'
```

### 6.2 Probar la API desde la Terminal
```bash
# Probar que la API responde (deberías obtener una respuesta HTTP 200 OK)
curl -I http://localhost:8080/api
```

### 6.3 Acceder a la Interfaz Web
Abre tu navegador y ve a **http://localhost:8080**. Deberías ver la pantalla de login.

- **Email:** `admin@heartguard.com`
- **Contraseña:** `admin123`

---

## 🔧 Comandos Útiles de Docker Compose (Sintaxis Corregida)

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs de todos los servicios en tiempo real
docker compose logs -f

# Ver logs de un servicio específico
docker compose logs -f backend-go

# Reiniciar todos los servicios
docker compose restart

# Detener todos los servicios
docker compose down

# Detener servicios Y ELIMINAR VOLÚMENES (¡borra los datos de la BD!)
docker compose down -v

# Reconstruir y levantar los servicios (cuando haces cambios en el código)
docker compose up -d --build
```

## 🐛 Solución de Problemas Comunes

### Problema: "Puerto ya está en uso"
```bash
# Ver qué proceso está usando el puerto (ej: 8080)
sudo lsof -i :8080

# Detener el proceso (reemplazar <PID> con el número de la columna PID)
sudo kill -9 <PID>
```

### Problema: "Base de datos no conecta"
```bash
# Ver logs de PostgreSQL
docker compose logs postgres

# Reiniciar el contenedor de la base de datos
docker compose restart postgres
```

### Problema: "Permiso denegado al ejecutar docker"
Si no reiniciaste sesión después de añadir tu usuario al grupo `docker`, usa `sudo` o reinicia tu sesión.
```bash
# Opción 1: Usar sudo
sudo docker compose ps

# Opción 2: Iniciar una nueva sesión de shell que reconozca tu nuevo grupo
newgrp docker
```
---

**🎉 ¡Felicidades! Tu backend de HeartGuard está listo para usar.**