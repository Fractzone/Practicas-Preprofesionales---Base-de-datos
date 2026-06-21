import re
from datetime import datetime

"""
Este archivo de validacion lo cree de tal manera que sus metodos sean static para poder usarlos en cualquier clase sin 
tener que instanciar el objeto, devido a que las validaciones se usan a lo largo de todo el programa mas de una vez
"""

class Validaciones:

    @staticmethod
    def validar_cedula(cedula):
        return (isinstance(cedula, str) and len(cedula) == 10 and cedula.isdigit() and
                0 < int(cedula[:2]) <= 24 and int(cedula[2]) < 6 and
                int(cedula[9]) == (10 - sum([int(x) * (2 - i % 2) - 9 * (int(x) * (2 - i % 2) > 9) for i, x in enumerate(cedula[:9])]) % 10) % 10)

    @staticmethod
    def validar_telefono(telefono):
        return isinstance(telefono, str) and len(telefono) == 10 and telefono.isdigit() and telefono[:2] == "09"

    @staticmethod
    def validar_ruc(ruc):
        return isinstance(ruc, str) and len(ruc) == 13 and ruc.isdigit() and ruc[-3:] == "001"

    @staticmethod
    def validar_email(email):
        patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return isinstance(email, str) and bool(re.match(patron, email))

    @staticmethod
    def validar_edad(fecha_str, formato="%d/%m/%Y"):
        obtener_fecha = lambda fecha, fmt: (lambda: datetime.strptime(fecha, fmt))() if Validaciones._es_fecha_valida(fecha, fmt) else None
        return (lambda f_nac: f_nac is not None and 0 <= (datetime.now().year - f_nac.year -
                ((datetime.now().month, datetime.now().day) < (f_nac.month, f_nac.day))) <= 80)(obtener_fecha(fecha_str, formato))

    @staticmethod
    def _es_fecha_valida(fecha, fmt):
        try:
            datetime.strptime(fecha, fmt)
            return True
        except ValueError:
            return False

    @staticmethod
    def validar_usuario(usuario):
        return isinstance(usuario, str) and 3 <= len(usuario) <= 20 and bool(re.match(r"^[A-Za-z0-9_.-]+$", usuario))

    @staticmethod
    def validar_contrasena(contrasena):
        return isinstance(contrasena, str) and 4 <= len(contrasena) <= 10 and bool(contrasena.strip())

    @staticmethod
    def validar_texto_no_vacio(*campos):
        return all(map(lambda c: isinstance(c, str) and bool(c.strip()), campos))

    @staticmethod
    def validar_entero_positivo(valor):
        return isinstance(valor, int) and not isinstance(valor, bool) and valor > 0

    @staticmethod
    def validar_decimal_no_negativo(valor):
        return isinstance(valor, (int, float)) and not isinstance(valor, bool) and valor >= 0

    @staticmethod
    def validar_rango(valor, minimo, maximo):
        return isinstance(valor, (int, float)) and not isinstance(valor, bool) and minimo <= valor <= maximo

    @staticmethod
    def validar_fecha_no_pasada(fecha_str, formato="%d/%m/%Y"):
        return (Validaciones._es_fecha_valida(fecha_str, formato) and
                datetime.strptime(fecha_str, formato).date() >= datetime.now().date())

    @staticmethod
    def validar_fecha_no_futura(fecha_str, formato="%d/%m/%Y"):
        return (Validaciones._es_fecha_valida(fecha_str, formato) and
                datetime.strptime(fecha_str, formato).date() <= datetime.now().date())

    @staticmethod
    def validar_orden_fechas(fecha_inicio, fecha_fin, formato="%d/%m/%Y"):
        return (Validaciones._es_fecha_valida(fecha_inicio, formato) and
                Validaciones._es_fecha_valida(fecha_fin, formato) and
                datetime.strptime(fecha_fin, formato).date() >= datetime.strptime(fecha_inicio, formato).date())
