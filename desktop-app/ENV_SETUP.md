# Configuración de Variables de Entorno

## Configuración Inicial

1. Copia el archivo `.env.example` a `.env`:
   ```bash
   copy .env.example .env
   ```

2. Edita el archivo `.env` y reemplaza `your_license_key_here` con tu licencia real de JxBrowser:
   ```
   JXBROWSER_LICENSE_KEY=tu_licencia_aqui
   ```

## Variables Disponibles

### JXBROWSER_LICENSE_KEY (Requerida)
Licencia de JxBrowser necesaria para usar el navegador embebido en la aplicación.

- **Obtener licencia**: https://www.teamdev.com/jxbrowser
- **Formato**: String de 100+ caracteres
- **Uso**: Renderiza mapas interactivos y contenido web dentro de la aplicación

## Seguridad

⚠️ **IMPORTANTE**: 
- El archivo `.env` contiene información sensible y **NO debe ser incluido en el control de versiones**
- Ya está configurado en `.gitignore` para evitar commits accidentales
- Comparte el archivo `.env.example` como plantilla, nunca el `.env` real

## Solución de Problemas

### Error: "JXBROWSER_LICENSE_KEY no encontrada en .env"
1. Verifica que el archivo `.env` existe en la raíz del proyecto `desktop-app/`
2. Asegúrate de que la variable está definida correctamente: `JXBROWSER_LICENSE_KEY=...`
3. No debe haber espacios alrededor del `=`

### La aplicación no encuentra el archivo .env
El archivo debe estar en la raíz del proyecto `desktop-app/`, al mismo nivel que `pom.xml`
