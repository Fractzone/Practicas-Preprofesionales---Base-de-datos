"""
Cifrado de contraseñas.

Las contraseñas NUNCA se guardan en texto plano: se almacena un hash derivado con
PBKDF2-HMAC-SHA256 (incluido en la librería estándar de Python, sin dependencias
externas) junto con una sal aleatoria por contraseña. El formato almacenado es:

    pbkdf2_sha256$<iteraciones>$<sal_hex>$<hash_hex>

La verificación se hace en tiempo constante con hmac.compare_digest para evitar
ataques de temporización.
"""
import hashlib
import hmac
import os

_ALGORITMO = "pbkdf2_sha256"
_ITERACIONES = 120_000
_TAM_SAL = 16


def hash_password(plano, iteraciones=_ITERACIONES):
    """Devuelve el hash con sal de una contraseña en texto plano."""
    if not isinstance(plano, str) or not plano:
        raise ValueError("La contraseña a cifrar no puede estar vacía.")
    sal = os.urandom(_TAM_SAL)
    derivado = hashlib.pbkdf2_hmac("sha256", plano.encode("utf-8"), sal, iteraciones)
    return f"{_ALGORITMO}${iteraciones}${sal.hex()}${derivado.hex()}"


def es_hash(valor):
    """True si el valor ya tiene el formato de un hash generado por este módulo."""
    return isinstance(valor, str) and valor.startswith(_ALGORITMO + "$")


def verificar_password(plano, hash_almacenado):
    """Compara una contraseña en texto plano contra el hash almacenado."""
    if not es_hash(hash_almacenado):
        # Compatibilidad defensiva: si encontrara un valor sin cifrar, lo compara
        # directamente (no debería ocurrir con datos creados por la aplicación).
        return plano == hash_almacenado
    try:
        _algoritmo, iteraciones, sal_hex, derivado_hex = hash_almacenado.split("$")
        derivado = hashlib.pbkdf2_hmac(
            "sha256", plano.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones))
        return hmac.compare_digest(derivado.hex(), derivado_hex)
    except (ValueError, TypeError):
        return False
