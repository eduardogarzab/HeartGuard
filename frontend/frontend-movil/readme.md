# HeartGuard - Aplicación de Monitoreo de Salud (Android)

Esta es la aplicación móvil oficial para el sistema de monitoreo de salud familiar **HeartGuard**. La aplicación permite a los usuarios iniciar sesión, ver alertas de salud en tiempo real y consultar el historial de signos vitales.

## 🚀 Funcionalidades

* **Autenticación Segura**: Pantalla de inicio de sesión para que los usuarios accedan a su información de forma segura.
* **Dashboard de Alertas**: Muestra una lista de las alertas de salud más recientes.
* **Historial de Signos Vitales**: Presenta un registro histórico de los signos vitales del usuario.
* **Consumo de API REST**: Se conecta a un backend para obtener todos los datos en tiempo real.
* **Interfaz de Usuario Moderna**: Construida con componentes modernos de Android para una experiencia fluida.

## 🛠️ Arquitectura y Tecnologías Utilizadas

* **Lenguaje**: [Kotlin](https://kotlinlang.org/)
* **Arquitectura**: MVVM (Model-View-ViewModel)
* **Componentes de Jetpack**: ViewModel, LiveData/StateFlow, Navigation Component, View Binding.
* **Programación Asíncrona**: Kotlin Coroutines
* **Red (Networking)**: Retrofit y OkHttp con un `Interceptor` para inyectar tokens de autenticación.
* **Interfaz de Usuario**: RecyclerView y ListAdapter.
* **Gestión de Sesiones**: SharedPreferences.

## 🏗️ Estructura del Proyecto

```
com.example.proyecto/
│
├── data/                  # Lógica de acceso a datos (API, Modelos, Repositorio).
├── ui/                    # Capa de presentación (Vistas y ViewModels).
└── utils/                 # Clases de utilidad (SessionManager, AuthInterceptor).
```

## ⚙️ Configuración y Puesta en Marcha

### Prerrequisitos

* Android Studio Iguana | 2023.2.1 o superior.
* JDK 17.
* Dispositivo Android o Emulador con API 24+.
* Tener el [backend de HeartGuard](https://github.com/eduardogarzab/HeartGuard) corriendo y accesible desde la red.

---

### **Opción 1: Ejecutar con Android Studio (Recomendado)**

1.  **Clonar el repositorio** (si no lo has hecho).
2.  **Abrir el proyecto** en Android Studio.
3.  **Configurar la URL del Backend**:
    * Abre el archivo `app/src/main/java/com/example/proyecto/data/api/ApiClient.kt`.
    * Modifica la constante `BASE_URL` para que apunte a la dirección IP de tu servidor backend.

    ```kotlin
    // Ejemplo de configuración:
    private const val BASE_URL = "[http://192.168.100.34:8081/](http://192.168.100.34:8081/)"
    ```
    > **Nota importante**: Si usas un emulador de Android y el backend se ejecuta en tu misma máquina (`localhost`), debes usar la IP `10.0.2.2` para que el emulador pueda acceder a él. Ejemplo: `http://10.0.2.2:8081/`.

4.  **Sincronizar Gradle**: Espera a que Android Studio descargue las dependencias. Si es necesario, haz clic en "Sync Project with Gradle Files".
5.  **Ejecutar la aplicación**:
    * Selecciona un dispositivo o emulador disponible.
    * Haz clic en el botón **Run 'app'** (▶️).

---

### **Opción 2: Ejecutar desde la Terminal (Línea de Comandos)**

Puedes compilar e instalar la aplicación directamente desde la terminal usando el Gradle Wrapper (`gradlew`).

#### **En Windows (CMD o PowerShell)**

1.  Abre una terminal y navega hasta la raíz del proyecto (la carpeta que contiene `gradlew.bat`).
2.  **Para compilar el APK de depuración:**
    * Ejecuta el siguiente comando. El APK se guardará en `app/build/outputs/apk/debug/`.
    ```cmd
    gradlew.bat assembleDebug
    ```

3.  **Para compilar e instalar en un dispositivo/emulador conectado:**
    * Asegúrate de tener un solo dispositivo o emulador activo y reconocido por ADB.
    ```cmd
    gradlew.bat installDebug
    ```

#### **En macOS o Linux (Terminal)**

1.  Abre una terminal y navega hasta la raíz del proyecto (la carpeta que contiene `gradlew`).
2.  **Dar permisos de ejecución al script (solo la primera vez):**
    ```bash
    chmod +x gradlew
    ```
3.  **Para compilar el APK de depuración:**
    * Ejecuta el siguiente comando. El APK se guardará en `app/build/outputs/apk/debug/`.
    ```bash
    ./gradlew assembleDebug
    ```
4.  **Para compilar e instalar en un dispositivo/emulador conectado:**
    * Asegúrate de tener un solo dispositivo o emulador activo y reconocido por ADB.
    ```bash
    ./gradlew installDebug
    ```
