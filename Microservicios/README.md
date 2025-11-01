# Guía de Despliegue de Microservicios

Este documento detalla los pasos para desplegar y probar la arquitectura de microservicios, asumiendo una configuración de dos máquinas virtuales (VM) separadas.

## Arquitectura

La arquitectura se compone de dos instancias:

1.  **VM de Backend**: Ejecuta la infraestructura principal de datos, incluyendo la base de datos PostgreSQL, Redis e InfluxDB.
2.  **VM de Microservicios**: Ejecuta los servicios de la aplicación en Python, los cuales se conectan a la VM de Backend para la persistencia de datos.

---

## Parte 1: Configuración de la VM de Backend

Antes de iniciar los microservicios, asegúrate de que la infraestructura del backend esté en ejecución.

### Pasos

1.  **Obtén la IP Privada**: Identifica la dirección IP de esta VM (por ejemplo, `10.0.0.5`). Esta IP será necesaria para configurar los microservicios.

2.  **Levanta los Servicios del Backend**: En el directorio raíz del proyecto, ejecuta el siguiente comando para iniciar PostgreSQL, Redis e InfluxDB:
    ```bash
    docker-compose up -d
    ```

3.  **Inicializa la Base de Datos**: Asegúrate de que la base de datos `heartguard` esté creada y que el esquema de `db/init.sql` se haya ejecutado.

---

## Parte 2: Configuración y Ejecución de la VM de Microservicios

Sigue estos pasos en la segunda VM, donde se ejecutarán los servicios de Python.

### Paso 1: Clonar el Repositorio

Clona el código fuente en la VM de Microservicios.

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_REPOSITORIO>/Microservicios
```

### Paso 2: Configurar el Entorno (`.env`)

Los microservicios necesitan saber cómo conectarse a la VM de Backend. Para ello, crearás un archivo `.env`.

1.  **Copia el archivo de ejemplo**:
    ```bash
    cp .env.example .env
    ```

2.  **Edita el archivo `.env`**: Abre el archivo `.env` con un editor (como `nano` o `vim`) y modifica las siguientes variables:

    *   **`BACKEND_INSTANCE_HOST`**: **Este es el paso más importante**. Reemplaza `127.0.0.1` por la dirección IP de tu VM de Backend.
        ```dotenv
        # IP address or hostname of the main backend instance
        BACKEND_INSTANCE_HOST=10.0.0.5 # <- REEMPLAZA ESTO CON LA IP DE TU VM DE BACKEND
        ```

    *   **`POSTGRES_PASSWORD`**: Asegúrate de que coincida con la contraseña de la base de datos del backend. Según `db/init.sql`, el valor es `dev_change_me`.

    *   **Genera nuevos secretos**: Por seguridad, es fundamental que generes valores únicos y aleatorios para los secretos. Abre una terminal y ejecuta los siguientes comandos. Copia y pega el resultado en las variables correspondientes de tu archivo `.env`.

        ```bash
        # Para JWT_SECRET
        openssl rand -hex 32

        # Para RABBITMQ_DEFAULT_PASS
        openssl rand -hex 32

        # Para INFLUX_TOKEN (debe coincidir con el del backend)
        openssl rand -hex 32
        ```
        Tu archivo `.env` debería verse similar a esto (con tus propios secretos):
        ```dotenv
        JWT_SECRET=tusecreto_super_aleatorio_generado_aqui
        RABBITMQ_DEFAULT_PASS=otro_secreto_aleatorio_para_rabbitmq
        INFLUX_TOKEN=token_secreto_para_influx
        BACKEND_INSTANCE_HOST=10.0.0.5
        # ... resto de las variables
        ```

### Paso 3: Levantar los Microservicios

Una vez que el archivo `.env` esté configurado, puedes construir y levantar todos los contenedores de los microservicios.

```bash
# Desde la carpeta Microservicios/
docker-compose up -d --build
```
El flag `--build` asegura que las imágenes de Docker se construyan con todos los cambios recientes.

### Paso 4: Verificar que los Contenedores estén en Ejecución

Para confirmar que todos los servicios se iniciaron correctamente y están saludables, ejecuta:

```bash
docker-compose ps
```
Deberías ver una lista de todos los servicios (`gateway`, `auth_service`, etc.) con el estado `Up` o `running (healthy)`.

---

## Parte 3: Pruebas de Conectividad

Ahora que todo está en ejecución, puedes realizar una prueba completa para verificar que el **Gateway** recibe peticiones, las redirige al **auth_service**, y este a su vez se conecta correctamente a la **base de datos remota**.

### Prueba: Registrar un Nuevo Usuario

Ejecuta el siguiente comando `curl` desde la terminal de tu VM de Microservicios. Este comando envía una petición para registrar un nuevo usuario a través del `gateway`.

```bash
curl -X POST http://localhost:5000/auth/register \
-H "Content-Type: application/json" \
-d '{
    "name": "Usuario de Prueba",
    "email": "test@example.com",
    "password": "Password123!"
}'
```

#### Resultado Esperado

Si todo está configurado correctamente, deberías recibir una respuesta `HTTP 201 Created` con los datos del nuevo usuario y los tokens JWT. Esto confirma que:
1.  El `gateway` está funcionando y redirigió la petición.
2.  El `auth_service` procesó la lógica de negocio.
3.  El `auth_service` se conectó exitosamente a la base de datos en la VM de Backend y creó el nuevo registro en la tabla `users`.

¡Con esto, habrás validado que toda la arquitectura está funcionando como se esperaba!
