"""
Utilidades compartidas por los controladores.
"""


def parsear_id(texto, nombre="ID"):
    """Convierte el texto de un campo de la interfaz en un identificador entero.

    Los identificadores subrogados (oferta, postulación, práctica, formularios,
    solicitud) los genera la base de datos como enteros (columnas IDENTITY). Esta
    función valida la entrada del usuario y lanza un ValueError claro si no es un
    número entero, para que el controlador lo muestre como error de validación.
    """
    texto = (texto or "").strip()
    if not texto:
        raise ValueError(f"Ingrese el {nombre}.")
    try:
        return int(texto)
    except (ValueError, TypeError):
        raise ValueError(f"El {nombre} debe ser un número entero válido.")
