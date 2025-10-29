# signal_service/worker.py
import os
import json
import time
import redis
import logging
from dotenv import load_dotenv

# Configurar el logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Cargar variables de entorno desde .env
load_dotenv()

# Es crucial importar la lógica del repositorio DESPUÉS de cargar el .env
from app.repository import stream_repository

# --- Configuración ---
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_QUEUE_KEY = 'data_ingest'
BATCH_SIZE = 1000  # Número de mensajes a procesar antes de escribir en la BD
MAX_BATCH_TIME_SECONDS = 5  # Tiempo máximo de espera antes de escribir un lote incompleto

# --- Conexiones ---
def connect_to_redis():
    """Intenta conectarse a Redis con reintentos."""
    while True:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True)
            r.ping()
            logging.info("Conectado a Redis exitosamente.")
            return r
        except redis.exceptions.ConnectionError as e:
            logging.error(f"No se pudo conectar a Redis: {e}. Reintentando en 5 segundos...")
            time.sleep(5)

redis_conn = connect_to_redis()

# --- Lógica del Worker ---
def process_queue():
    """
    Bucle principal del worker que escucha la cola de Redis y procesa los mensajes.
    """
    batch_data = []
    last_insert_time = time.time()

    logging.info(f"Worker iniciado. Escuchando la cola '{REDIS_QUEUE_KEY}'...")

    while True:
        try:
            # brpop es una operación de bloqueo con timeout.
            # Esperará hasta 5 segundos por un nuevo elemento.
            # Si no hay nada, devuelve None y el bucle continúa.
            message = redis_conn.brpop(REDIS_QUEUE_KEY, timeout=MAX_BATCH_TIME_SECONDS)

            if message:
                _, raw_data = message
                try:
                    # Parsear el mensaje JSON
                    data = json.loads(raw_data)
                    stream_id = data.get('stream_id')

                    # Transformar los datos para la inserción en lote
                    for item in data.get('data', []):
                        batch_data.append({
                            'stream_id': stream_id,
                            'timestamp': item['ts'],
                            'value': item['val']
                        })
                except (json.JSONDecodeError, KeyError) as e:
                    logging.error(f"Error al procesar el mensaje: {raw_data}. Error: {e}")
                    continue # Saltar mensaje malformado

            # Comprobar si se debe realizar la inserción en la base de datos
            time_since_last_insert = time.time() - last_insert_time
            if (len(batch_data) >= BATCH_SIZE) or \
               (batch_data and time_since_last_insert >= MAX_BATCH_TIME_SECONDS):

                logging.info(f"Insertando lote de {len(batch_data)} registros...")
                try:
                    stream_repository.batch_insert_timeseries_data(batch_data)
                    logging.info("Lote insertado exitosamente.")
                    batch_data = [] # Limpiar el lote
                    last_insert_time = time.time()
                except Exception as e:
                    logging.error(f"Fallo al insertar el lote en la base de datos: {e}")
                    # En un sistema de producción, se podría implementar una política de reintentos
                    # o mover el lote a una cola de "letras muertas" (dead-letter queue).

        except redis.exceptions.ConnectionError:
            logging.error("Se perdió la conexión con Redis. Intentando reconectar...")
            redis_conn = connect_to_redis()
        except Exception as e:
            logging.error(f"Ocurrió un error inesperado en el bucle del worker: {e}")
            time.sleep(5) # Esperar un poco antes de continuar para evitar ciclos de error rápidos

if __name__ == "__main__":
    process_queue()
