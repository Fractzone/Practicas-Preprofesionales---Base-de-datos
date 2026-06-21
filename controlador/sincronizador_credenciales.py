from modelo.credencial import Credencial

class SincronizadorCredenciales:
    ENTIDAD = 'login'

    @staticmethod
    def agregar(persistencia, identificador, contrasena, rol):
        credenciales = persistencia.cargar(SincronizadorCredenciales.ENTIDAD)
        credenciales[identificador] = Credencial(identificador, contrasena, rol)
        persistencia.guardar(SincronizadorCredenciales.ENTIDAD, credenciales)

    @staticmethod
    def existe_activo(persistencia, identificador):
        credenciales = persistencia.cargar(SincronizadorCredenciales.ENTIDAD)
        credencial = credenciales.get(identificador)
        return credencial is not None and not credencial.eliminado

    @staticmethod
    def eliminar(persistencia, identificador):
        credenciales = persistencia.cargar(SincronizadorCredenciales.ENTIDAD)
        credencial = credenciales.get(identificador)
        if credencial is not None:
            credencial.eliminado = True
            persistencia.guardar(SincronizadorCredenciales.ENTIDAD, credenciales)
