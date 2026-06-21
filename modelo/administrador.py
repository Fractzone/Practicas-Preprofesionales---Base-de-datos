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

    @staticmethod
    def buscar_por_usuario(diccionario_administradores, usuario):
        return diccionario_administradores.get(usuario, None)

    def __repr__(self):
        return f"Administrador(usuario='{self.usuario}', email='{self.email}')"


class RepositorioAdministrador:
    ENTIDAD = 'administrador'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.administradores = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.administradores = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.administradores)

    def listar(self):
        return list(filter(lambda a: not a.eliminado, self.administradores.values()))

    def buscar(self, usuario):
        admin = Administrador.buscar_por_usuario(self.administradores, usuario)
        return admin if admin is not None and not admin.eliminado else None

    def agregar(self, usuario, contrasena, email):
        if not all([usuario, contrasena, email]):
            raise ValueError("Por favor, complete todos los campos.")
        if usuario in self.administradores:
            raise ValueError(f"El administrador con usuario '{usuario}' ya está registrado.")
        nuevo = Administrador(usuario, contrasena, email)
        self.administradores[nuevo.usuario] = nuevo
        self.guardar()
        return nuevo

    def eliminar(self, usuario):
        admin = self.administradores.get(usuario)
        if admin is None or admin.eliminado:
            raise ValueError("No existe un administrador registrado con el usuario ingresado.")
        admin.eliminado = True
        self.guardar()
