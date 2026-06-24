from modelo.validaciones import Validaciones

class Administrador:
    ROL = "administrador"

    def __init__(self, usuario, contrasena, email, eliminado=False):
        if not Validaciones.validar_usuario(usuario):
            raise ValueError("El usuario debe tener entre 3 y 20 caracteres alfanuméricos.")
        if not Validaciones.validar_contrasena(contrasena):
            raise ValueError("La contraseña debe tener entre 4 y 10 caracteres.")
        if not Validaciones.validar_email(email):
            raise ValueError("El correo electrónico no tiene un formato válido (ejemplo@dominio.com).")

        self.usuario = usuario
        self.contrasena = contrasena
        self.email = email
        self.eliminado = eliminado

    def __repr__(self):
        return f"Administrador(usuario='{self.usuario}', email='{self.email}')"


class RepositorioAdministrador:
    ENTIDAD = 'administrador'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def recargar(self):
        # Compatibilidad: ya no hay caché en memoria; cada método consulta la BD.
        pass

    def actualizar(self, administrador):
        self.persistencia.actualizar(self.ENTIDAD, administrador)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, usuario):
        admin = self.persistencia.obtener(self.ENTIDAD, usuario)
        return admin if admin is not None and not admin.eliminado else None

    def agregar(self, usuario, contrasena, email):
        if not all([usuario, contrasena, email]):
            raise ValueError("Por favor, complete todos los campos.")
        if self.persistencia.existe(self.ENTIDAD, usuario):
            raise ValueError(f"El administrador con usuario '{usuario}' ya está registrado.")
        nuevo = Administrador(usuario, contrasena, email)
        self.persistencia.insertar(self.ENTIDAD, nuevo)
        return nuevo

    def eliminar(self, usuario):
        if self.buscar(usuario) is None:
            raise ValueError("No existe un administrador registrado con el usuario ingresado.")
        self.persistencia.marcar_eliminado(self.ENTIDAD, usuario)
