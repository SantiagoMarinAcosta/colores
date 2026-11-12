"""Configuración de NumeriArte por entorno."""
import os


class Config:
    """Configuración base compartida."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "numeriarte-desarrollo")
    DEBUG = False
    TESTING = False
    # Número de muestras del mural cuando la solicitud no indica uno.
    MUESTRAS_MURAL_DEFECTO = 121


class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    pass


CONFIGURACIONES = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def obtener_configuracion(nombre=None):
    """Devuelve la clase de configuración solicitada (por defecto, producción)."""
    nombre = nombre or os.environ.get("FLASK_ENV_NUMERIARTE", "production")
    return CONFIGURACIONES.get(nombre, ProductionConfig)
