class Credencial:

    def __init__(self, identificador, contrasena, rol, eliminado=False):
        if not (isinstance(identificador, str) and identificador.strip()):
            raise ValueError("El identificador no puede estar vacío.")
        if not (isinstance(contrasena, str) and contrasena.strip()):
            raise ValueError("La contraseña no puede estar vacía.")
        if rol not in ("administrador", "estudiante", "tutor_academico",
                       "tutor_empresarial", "coordinador_vinculacion"):
            raise ValueError(f"Rol '{rol}' inválido.")

        self.identificador = identificador
        self.contrasena = contrasena  # se almacena cifrada (hash con sal); ver modelo/seguridad.py
        self.rol = rol
        self.eliminado = eliminado

    def __repr__(self):
        return f"Credencial(identificador='{self.identificador}', rol='{self.rol}')"
