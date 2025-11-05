"""
Configuración del Patient Service
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuración base del servicio"""
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://heartguard_app:dev_change_me@136.115.53.140:5432/heartguard')
    
    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', 'change-me-secret-key-12345')
    JWT_ALGORITHM = 'HS256'
    
    # Server
    PORT = int(os.getenv('PORT', 5004))
    HOST = os.getenv('HOST', '0.0.0.0')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


# Configuraciones por entorno
class DevelopmentConfig(Config):
    """Configuración de desarrollo"""
    DEBUG = True


class ProductionConfig(Config):
    """Configuración de producción"""
    DEBUG = False


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Obtiene la configuración según el entorno"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
