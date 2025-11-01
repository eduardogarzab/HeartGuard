# ✅ LA APLICACIÓN ESTÁ CORRIENDO

La aplicación se ha compilado y arrancado correctamente en:
- **URL**: http://localhost:8081
- **Puerto**: 8081
- **PID**: 18680

---

## 🔴 IMPORTANTE: Debes Limpiar las Cookies ANTES de Abrir el Navegador

### ⚠️ El error 400 es causado por cookies viejas muy grandes en tu navegador

---

## 📋 INSTRUCCIONES PASO A PASO (Copia y Pega)

### OPCIÓN 1: Usar Modo Incógnito/Privado (MÁS FÁCIL) ✅

**Esta es la forma más rápida y segura:**

1. **Abre tu navegador en modo incógnito:**
   - **Chrome/Edge**: Presiona `Ctrl + Shift + N`
   - **Firefox**: Presiona `Ctrl + Shift + P`

2. **En la ventana incógnito, escribe esta URL:**
   ```
   http://localhost:8081/login
   ```

3. **Presiona Enter**

4. **Deberías ver la página de login de HeartGuard** ✅

---

### OPCIÓN 2: Limpiar Cookies Manualmente

Si prefieres no usar modo incógnito:

#### Para Chrome/Edge:
1. Abre Chrome o Edge (navegador normal)
2. Presiona `F12` para abrir Developer Tools
3. Ve a la pestaña **Application** (en la parte superior)
4. En el menú izquierdo, expande **Cookies**
5. Haz clic en `http://localhost:8081`
6. Haz clic derecho en el área de cookies → **Clear**
7. Cierra Developer Tools (`F12` de nuevo)
8. Ve a: `http://localhost:8081/login`

#### Para Firefox:
1. Abre Firefox
2. Presiona `F12` para abrir Developer Tools
3. Ve a la pestaña **Storage** (en la parte superior)
4. En el menú izquierdo, expande **Cookies**
5. Haz clic en `http://localhost:8081`
6. Haz clic derecho → **Delete All**
7. Cierra Developer Tools (`F12` de nuevo)
8. Ve a: `http://localhost:8081/login`

---

## 🧪 PROBAR CON POWERSHELL (Sin navegador)

Si quieres ver que funciona sin navegador, copia y pega este comando:

```powershell
Invoke-WebRequest -Uri http://localhost:8081/login -UseBasicParsing | Select-Object StatusCode, @{Name='HTML Preview';Expression={$_.Content.Substring(0,200)}}
```

Deberías ver:
- **StatusCode: 200** ✅
- **HTML Preview: <!DOCTYPE html>...**

---

## ✅ QUÉ VAS A VER

Cuando funcione correctamente, verás:

1. **Título de la página**: "HeartGuard - Iniciar sesión"
2. **Encabezado grande**: "HeartGuard"
3. **Subtítulo**: "Portal de Usuario Final"
4. **Formulario con**:
   - Campo de correo electrónico
   - Campo de contraseña
   - Botón azul "Ingresar"

---

## 🐛 SI AÚN VES ERROR 400

Prueba en este orden:

### 1. Verifica que la app está corriendo:
```powershell
Get-Process -Id 18680
```

### 2. Prueba con curl (sin cookies):
```powershell
Invoke-WebRequest -Uri http://localhost:8081/login -UseBasicParsing
```

### 3. Si curl funciona pero el navegador no:
- **Cierra TODAS las ventanas del navegador**
- **Reinicia el navegador**
- **Abre en modo incógnito**

### 4. Última opción - Reiniciar todo:
```powershell
# Detener la app
Stop-Process -Id 18680 -Force

# Limpiar puerto (por si quedó algo)
Start-Sleep -Seconds 2

# Reiniciar la app
cd 'c:\Users\mendo\Downloads\code\UDEM\integracion\HeartGuard\user-portal'
java -jar .\target\heartguard-user-portal-0.0.1-SNAPSHOT.jar
```

---

## 📝 COMANDOS ÚTILES

### Ver si la app sigue corriendo:
```powershell
Get-Process -Id 18680
```

### Detener la app:
```powershell
Stop-Process -Id 18680 -Force
```

### Ver logs de la app:
Simplemente mira la terminal donde ejecutaste `java -jar`
Los logs aparecen en tiempo real ahí.

---

## 🎯 SIGUIENTE PASO

Una vez que veas la página de login correctamente:

1. **NO** podrás hacer login porque no hay gateway corriendo
2. Pero habrás confirmado que el portal funciona ✅
3. Si quieres probar login completo, necesitamos levantar el gateway

**Dime cuando veas la página de login y te ayudo con lo siguiente.**

---

## 📞 ¿NECESITAS AYUDA?

Si sigues viendo error 400 después de seguir TODOS los pasos:

1. Cierra TODAS las ventanas del navegador
2. Abre modo incógnito
3. Ve a: http://localhost:8081/login
4. Toma un screenshot y compártelo
5. Copia y pega aquí el resultado de este comando:
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8081/login -UseBasicParsing
   ```
