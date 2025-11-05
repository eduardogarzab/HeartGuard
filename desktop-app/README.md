# HeartGuard Desktop App

Aplicación de escritorio en Java para HeartGuard que permite a usuarios y pacientes autenticarse y registrarse.

## Requisitos

- Java 11 o superior
- Maven 3.6 o superior
- Microservicios Gateway y Auth ejecutándose

## Configuración

La aplicación se conecta al Gateway en:
- **Gateway URL**: `http://localhost:8000`

El Gateway a su vez se conecta al backend en la IP `136.115.53.140`.

## Compilación

```bash
mvn clean package
```

## Ejecución

```bash
java -jar target/desktop-app-1.0.0.jar
```

O usando Maven:

```bash
mvn exec:java -Dexec.mainClass="com.heartguard.desktop.Main"
```

## Características

- **Login de Usuario**: Para personal del staff (médicos, enfermeras, etc.)
- **Login de Paciente**: Para pacientes del sistema
- **Registro de Usuario**: Creación de cuentas de staff
- **Registro de Paciente**: Creación de cuentas de pacientes
- **Interfaz moderna**: Usando FlatLaf Look and Feel

## Estructura

```
src/main/java/com/heartguard/desktop/
├── Main.java                    # Punto de entrada
├── api/
│   ├── ApiClient.java          # Cliente HTTP para el Gateway
│   └── ApiException.java       # Excepciones de API
├── models/
│   ├── User.java               # Modelo de usuario
│   ├── Patient.java            # Modelo de paciente
│   └── LoginResponse.java      # Respuesta de login
└── ui/
    ├── LoginFrame.java         # Pantalla principal de login
    ├── RegisterUserFrame.java  # Registro de usuario
    └── RegisterPatientFrame.java # Registro de paciente
```

## Pruebas

1. Asegúrate de que los microservicios estén ejecutándose
2. Ejecuta la aplicación
3. Selecciona el tipo de cuenta (Usuario o Paciente)
4. Prueba login y registro para ambos tipos
