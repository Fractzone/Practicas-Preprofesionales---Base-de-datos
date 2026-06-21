import os

RUTA_RECURSOS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "recursos"))

def ruta_recurso(subcarpeta, nombre_archivo):
    return os.path.join(RUTA_RECURSOS, subcarpeta, nombre_archivo)
