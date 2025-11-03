# Guía de Pruebas - HeartGuard Desktop App

Esta guía te ayudará a ejecutar y probar la aplicación de escritorio de HeartGuard junto con los microservicios necesarios.

## 📋 Prerequisitos

Antes de comenzar, asegúrate de tener instalado:

1. **Python 3.8+** - Para los microservicios
2. **Java 11+** - Para la aplicación de escritorio
3. **Apache Maven 3.6+** - Para compilar la aplicación Java
4. **PostgreSQL** - El backend en `136.115.53.140:5432` debe estar accesible

## 🚀 Paso 1: Iniciar los Microservicios

Los microservicios (Auth y Gateway) deben estar ejecutándose para que la aplicación funcione.

### Opción A: Usar el script automático (Recomendado)

```powershell
.\start-services.ps1
```

Este script:
- Verificará las dependencias de Python
- Instalará los paquetes necesarios
- Iniciará Auth Service en el puerto 5001
- Iniciará Gateway Service en el puerto 8000

### Opción B: Iniciar manualmente

#### 1. Auth Service

```powershell
cd services\auth
pip install -r requirements.txt
$env:FLASK_APP="src\auth\app.py"
flask run --host=0.0.0.0 --port=5001
```

#### 2. Gateway Service (en otra terminal)

```powershell
cd services\gateway
pip install -r requirements.txt
$env:FLASK_APP="src\gateway\app.py"
flask run --host=0.0.0.0 --port=8000
```

### Verificar que los servicios están corriendo

Abre tu navegador y verifica:
- Auth Service: http://localhost:5001/health
- Gateway Service: http://localhost:8000/health

Deberías ver una respuesta JSON con `"status": "ok"`.

## 🖥️ Paso 2: Compilar y Ejecutar la Aplicación Java

### Opción A: Usar el script automático (Recomendado)

```powershell
.\run-desktop-app.ps1
```

Este script:
- Verificará Java y Maven
- Compilará la aplicación
- Ejecutará el JAR generado

### Opción B: Compilar y ejecutar manualmente

```powershell
cd desktop-app
mvn clean package
java -jar target\desktop-app-1.0.0.jar
```

## 🧪 Paso 3: Probar la Aplicación

### Prueba 1: Registro de Usuario (Staff)

1. En la pantalla de login, selecciona **"Usuario (Staff)"**
2. Haz clic en **"Registrarse"**
3. Completa el formulario:
   - **Email**: `doctor.test@heartguard.com`
   - **Contraseña**: `password123`
   - **Confirmar Contraseña**: `password123`
   - **Nombre**: `Juan`
   - **Apellido**: `Pérez`
   - **Teléfono**: `5551234567`
   - **ID Organización**: `1`
   - **ID Rol**: `1`
4. Haz clic en **"Registrar"**
5. Deberías ver un mensaje de éxito

### Prueba 2: Login de Usuario

1. En la pantalla de login, selecciona **"Usuario (Staff)"**
2. Ingresa las credenciales:
   - **Email**: `doctor.test@heartguard.com`
   - **Contraseña**: `password123`
3. Haz clic en **"Iniciar Sesión"**
4. Deberías ver un mensaje de bienvenida con tus datos

### Prueba 3: Registro de Paciente

1. En la pantalla de login, selecciona **"Paciente"**
2. Haz clic en **"Registrarse"**
3. Completa el formulario:
   - **Email**: `paciente.test@heartguard.com`
   - **Contraseña**: `password123`
   - **Confirmar Contraseña**: `password123`
   - **Nombre**: `María`
   - **Apellido**: `González`
   - **Teléfono**: `5559876543`
   - **Fecha de Nacimiento**: `1985-05-20`
   - **Género**: Selecciona una opción
   - **ID Organización**: `1`
4. Haz clic en **"Registrar"**
5. Deberías ver un mensaje de éxito

### Prueba 4: Login de Paciente

1. En la pantalla de login, selecciona **"Paciente"**
2. Ingresa las credenciales:
   - **Email**: `paciente.test@heartguard.com`
   - **Contraseña**: `password123`
3. Haz clic en **"Iniciar Sesión"**
4. Deberías ver un mensaje de bienvenida

## 🔍 Verificación de Conexiones

### Verificar conexión al backend

Los microservicios se conectan al backend PostgreSQL en `136.115.53.140:5432`. Para verificar la conexión:

```powershell
# Desde PowerShell, puedes probar la conexión con:
Test-NetConnection -ComputerName 136.115.53.140 -Port 5432
```

### Logs de los servicios

Los servicios mostrarán logs en las terminales donde se ejecutan. Revisa estos logs si encuentras errores:

- **Auth Service**: Muestra logs de autenticación, registro y acceso a BD
- **Gateway Service**: Muestra logs de peticiones HTTP y comunicación con Auth

## ⚠️ Solución de Problemas

### Error: "Error de conexión"

**Causa**: Los microservicios no están ejecutándose o no son accesibles.

**Solución**:
1. Verifica que ambos servicios estén corriendo (Paso 1)
2. Verifica los puertos con: `netstat -ano | findstr "5001 8000"`
3. Verifica que no haya firewall bloqueando los puertos

### Error: "DATABASE_URL es requerido"

**Causa**: El archivo `.env` en `services/auth/` no está configurado correctamente.

**Solución**:
1. Verifica que existe el archivo `services/auth/.env`
2. Asegúrate de que contiene: `DATABASE_URL=postgresql://postgres:postgres@136.115.53.140:5432/heartguard`

### Error: "could not connect to server"

**Causa**: El backend PostgreSQL no es accesible.

**Solución**:
1. Verifica que la IP `136.115.53.140` sea correcta
2. Verifica conectividad: `Test-NetConnection -ComputerName 136.115.53.140 -Port 5432`
3. Verifica que el firewall permita conexiones salientes al puerto 5432

### Error al compilar Java: "package does not exist"

**Causa**: Maven no descargó las dependencias correctamente.

**Solución**:
```powershell
cd desktop-app
mvn clean
mvn dependency:resolve
mvn package
```

### La interfaz se ve anticuada

**Causa**: FlatLaf no se cargó correctamente.

**Solución**: La aplicación debería funcionar con el Look & Feel del sistema como fallback. Revisa los logs en la consola.

## 📊 Verificación de Datos en la Base de Datos

Si tienes acceso directo a PostgreSQL, puedes verificar que los registros se crearon:

```sql
-- Ver usuarios creados
SELECT id, email, first_name, last_name FROM users ORDER BY created_at DESC LIMIT 5;

-- Ver pacientes creados
SELECT id, email, first_name, last_name FROM patients ORDER BY created_at DESC LIMIT 5;
```

## 🎯 Flujo Completo de Prueba

1. ✅ Iniciar microservicios
2. ✅ Verificar health checks
3. ✅ Compilar aplicación Java
4. ✅ Ejecutar aplicación
5. ✅ Registrar un usuario
6. ✅ Hacer login con ese usuario
7. ✅ Registrar un paciente
8. ✅ Hacer login con ese paciente
9. ✅ Verificar en logs que las peticiones fueron exitosas
10. ✅ (Opcional) Verificar en BD que los registros existen

## 📝 Notas Adicionales

- Los tokens JWT tienen una duración de 60 minutos (configurable en `services/auth/.env`)
- Las contraseñas se hashean con bcrypt antes de almacenarse
- La aplicación Java guarda el token de acceso para futuras peticiones
- El Gateway actúa como proxy y centraliza todas las peticiones al Auth Service

## 🆘 Soporte

Si encuentras problemas, revisa:

1. Los logs de los microservicios en las terminales
2. Los logs de la aplicación Java en la consola
3. La conectividad de red con `Test-NetConnection`
4. Que todos los prerequisitos estén instalados correctamente

## 🎉 ¡Éxito!

Si completaste todas las pruebas exitosamente, la aplicación está funcionando correctamente y conectada al backend remoto.
