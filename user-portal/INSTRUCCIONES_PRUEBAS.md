# 🚀 Instrucciones para Probar el User Portal

## ⚠️ SOLUCIÓN AL ERROR 400 "Bad Request"

El error ocurre porque tu navegador envía cookies muy grandes. Sigue estos pasos:

### Paso 1: Detener la aplicación actual
```powershell
Stop-Process -Id 29492 -Force
```

### Paso 2: Limpiar cookies de tu navegador
1. Abre tu navegador (Chrome, Edge, Firefox)
2. Presiona **F12** para abrir Developer Tools
3. Ve a la pestaña **Application** (Chrome/Edge) o **Storage** (Firefox)
4. En el menú izquierdo, expande **Cookies**
5. Busca y elimina todas las cookies de `localhost:8081`
6. **Cierra todas las ventanas del navegador**

### Paso 3: Reiniciar la aplicación con la configuración correcta
```powershell
cd 'c:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard\user-portal'
java -jar .\target\heartguard-user-portal-0.0.1-SNAPSHOT.jar
```

### Paso 4: Abrir en modo incógnito/privado
1. Abre una **ventana de incógnito**:
   - Chrome/Edge: `Ctrl + Shift + N`
   - Firefox: `Ctrl + Shift + P`
2. Ve a: `http://localhost:8081/login`

---

## 🌐 Probar la Aplicación

### URLs disponibles:
- **Login**: http://localhost:8081/login
- **Raíz** (redirige a login): http://localhost:8081/

### Lo que verás:
✅ Página de login de HeartGuard con:
- Campo de correo electrónico
- Campo de contraseña
- Botón "Ingresar"

### Nota importante:
- El login NO funcionará sin el gateway corriendo
- Pero podrás ver toda la interfaz de usuario
- La página debe cargar SIN errores 400

---

## 🔧 Comandos Útiles

### Ver si la app está corriendo:
```powershell
Get-Process java
```

### Detener la aplicación:
```powershell
Stop-Process -Name java -Force
```

### Ver logs en tiempo real:
Simplemente mira la terminal donde ejecutaste el comando `java -jar`

---

## 🐛 Si Aún Ves Error 400

### Opción 1: Usar curl para probar (sin cookies)
```powershell
curl http://localhost:8081/login
```

### Opción 2: Verificar que el JAR tenga la configuración correcta
```powershell
# Extraer y verificar application.yml
cd 'c:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard\user-portal\target'
jar -xf heartguard-user-portal-0.0.1-SNAPSHOT.jar BOOT-INF/classes/application.yml
Get-Content BOOT-INF\classes\application.yml
```

Deberías ver:
```yaml
server:
  port: 8081
  tomcat:
    max-http-header-size: 65536
```

### Opción 3: Forzar recompilación completa
```powershell
cd 'c:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard\user-portal'
$env:Path = 'C:\Users\mendo\Downloads\maven-mvnd-1.0.3-windows-amd64\maven-mvnd-1.0.3-windows-amd64\bin;' + $env:Path
mvnd clean
mvnd -DskipTests package
java -jar .\target\heartguard-user-portal-0.0.1-SNAPSHOT.jar
```

---

## ✅ Confirmación de Éxito

Sabrás que todo funciona cuando:
1. Abres `http://localhost:8081/login` en tu navegador
2. Ves el formulario de login de HeartGuard
3. NO ves ningún error 400
4. Los logs muestran: `Initializing Spring DispatcherServlet 'dispatcherServlet'`

---

## 📞 ¿Necesitas Ayuda?

Si sigues viendo errores:
1. Copia el mensaje de error completo
2. Copia los últimos 20 líneas de los logs
3. Compártelos para ayudarte mejor
