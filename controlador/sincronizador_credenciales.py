from modelo.credencial import Credencial

class SincronizadorCredenciales:
    ENTIDAD = 'login'

    @staticmethod
    def agregar(persistencia, identificador, contrasena, rol):
        persistencia.actualizar(
            SincronizadorCredenciales.ENTIDAD,
            Credencial(identificador, contrasena, rol))

    @staticmethod
    def existe_activo(persistencia, identificador):
        credencial = persistencia.obtener(SincronizadorCredenciales.ENTIDAD, identificador)
        return credencial is not None and not credencial.eliminado

    @staticmethod
    def eliminar(persistencia, identificador):
        credencial = persistencia.obtener(SincronizadorCredenciales.ENTIDAD, identificador)
        if credencial is not None:
            persistencia.marcar_eliminado(SincronizadorCredenciales.ENTIDAD, identificador)
