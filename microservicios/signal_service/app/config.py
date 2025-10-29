# signal_service/app/config.py
from pathlib import Path
from dotenv import load_dotenv

def load_config():
    """
    Loads environment variables from the shared and service-specific .env files.

    It finds the root of the microservices directory and loads the shared
    .env file first, then loads the service-specific .env file, allowing
    service-specific settings to override the shared ones.
    """
    # Path to the current file (config.py)
    current_file_path = Path(__file__).resolve()

    # Navigate up to the service's root directory (microservicios/signal_service/)
    service_root = current_file_path.parent.parent

    # Navigate up to the microservices root directory (microservicios/)
    microservices_root = service_root.parent

    # Path to the shared .env file
    shared_env_path = microservices_root / ".env"

    # Path to the service-specific .env file
    service_env_path = service_root / ".env"

    # Load the shared .env file if it exists
    if shared_env_path.exists():
        load_dotenv(dotenv_path=shared_env_path)

    # Load the service-specific .env file, overriding any shared values
    if service_env_path.exists():
        load_dotenv(dotenv_path=service_env_path, override=True)

# Automatically load config when this module is imported
load_config()
