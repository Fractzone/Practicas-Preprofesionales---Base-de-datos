"""
En este archivo proceso junto las clases que se usan durante el proceso de practicas que son Oferta, Postulacion, Practica y Solicitud
ya que al relacionarse entre si creo un solo archivo que las englobe.
"""
from modelo.validaciones import Validaciones


class Oferta:

    def __init__(self, id_oferta, descripcion, puesto, fecha_publicacion, ruc_empresa, eliminado=False):
        self.id_oferta = id_oferta
        self.descripcion = descripcion
        self.puesto = puesto
        self.fecha_publicacion = fecha_publicacion
        self.ruc_empresa = ruc_empresa
        self.eliminado = eliminado

    def __repr__(self):
        return f"Oferta(id='{self.id_oferta}', puesto='{self.puesto}', empresa='{self.ruc_empresa}')"


class RepositorioOferta:
    ENTIDAD = 'oferta'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def actualizar(self, oferta):
        self.persistencia.actualizar(self.ENTIDAD, oferta)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, id_oferta):
        oferta = self.persistencia.obtener(self.ENTIDAD, id_oferta)
        return oferta if oferta is not None and not oferta.eliminado else None

    def de_empresa(self, ruc_empresa):
        return self.persistencia.listar(self.ENTIDAD, where="ruc_empresa = %s", params=(ruc_empresa,))

    def detalle_disponibles(self):
        """Ofertas activas con el nombre de su empresa (JOIN vía vista)."""
        s = self.persistencia.schema
        return self.persistencia.consultar(
            f'SELECT * FROM "{s}".vista_oferta_detalle '
            f'WHERE eliminado = FALSE ORDER BY id_oferta')

    def agregar(self, descripcion, puesto, fecha_publicacion, ruc_empresa):
        if not ruc_empresa:
            raise ValueError("Seleccione una empresa.")
        if not all([puesto, descripcion]):
            raise ValueError("Complete el puesto y la descripción.")
        nueva = Oferta(None, descripcion, puesto, fecha_publicacion, ruc_empresa)
        self.persistencia.insertar(self.ENTIDAD, nueva)  # la base asigna id_oferta
        return nueva


class Postulacion:

    def __init__(self, id_postulacion, fecha, estado_validacion, cedula_estudiante, id_oferta, id_coordinador, eliminado=False):
        self.id_postulacion = id_postulacion
        self.fecha = fecha
        self.estado_validacion = estado_validacion
        self.cedula_estudiante = cedula_estudiante
        self.id_oferta = id_oferta
        self.id_coordinador = id_coordinador
        self.eliminado = eliminado

    def __repr__(self):
        return f"Postulacion(id='{self.id_postulacion}', estado='{self.estado_validacion}', estudiante='{self.cedula_estudiante}')"


class RepositorioPostulacion:
    ENTIDAD = 'postulacion'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def actualizar(self, postulacion):
        self.persistencia.actualizar(self.ENTIDAD, postulacion)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, id_postulacion):
        postulacion = self.persistencia.obtener(self.ENTIDAD, id_postulacion)
        return postulacion if postulacion is not None and not postulacion.eliminado else None

    def de_estudiante(self, cedula):
        return self.persistencia.listar(self.ENTIDAD, where="cedula_estudiante = %s", params=(cedula,))

    def de_ofertas(self, ids_oferta):
        return self.persistencia.listar(self.ENTIDAD, where="id_oferta = ANY(%s)", params=(list(ids_oferta),))

    def por_estado(self, estado):
        return self.persistencia.listar(self.ENTIDAD, where="estado_validacion = %s", params=(estado,))

    def validadas_de_oferta(self, id_oferta):
        return self.persistencia.listar(
            self.ENTIDAD,
            where="estado_validacion = %s AND id_oferta = %s",
            params=("Validada", id_oferta))

    def detalle_pendientes(self):
        """Postulaciones pendientes con datos de estudiante y oferta (JOIN vía vista)."""
        s = self.persistencia.schema
        return self.persistencia.consultar(
            f'SELECT * FROM "{s}".vista_postulacion_detalle '
            f'WHERE estado_validacion = %s AND eliminado = FALSE ORDER BY id_postulacion',
            ("Pendiente",))

    def tiene_activa_para_oferta(self, cedula, id_oferta):
        activas = self.persistencia.listar(
            self.ENTIDAD,
            where="cedula_estudiante = %s AND id_oferta = %s AND estado_validacion <> %s",
            params=(cedula, id_oferta, "Rechazada"))
        return bool(activas)

    def agregar(self, fecha, estado, cedula_estudiante, id_oferta, id_coordinador):
        nueva = Postulacion(None, fecha, estado, cedula_estudiante, id_oferta, id_coordinador)
        self.persistencia.insertar(self.ENTIDAD, nueva)  # la base asigna id_postulacion
        return nueva


class Practica:
    EN_PROGRESO = "En progreso"
    EN_EJECUCION = "En Ejecución"
    EVALUACION_SOLICITADA = "Evaluación Solicitada"
    PENDIENTE_NOTA = "Pendiente Nota"
    FINALIZADA = "Finalizada / Aprobada"
    ESTADOS_ACTIVA = (EN_PROGRESO, EN_EJECUCION, EVALUACION_SOLICITADA, PENDIENTE_NOTA)

    def __init__(self, id_practica, fecha_inicio, fecha_fin, estado, id_postulacion, id_tutor_academico, id_tutor_empresarial, eliminado=False):
        self.id_practica = id_practica
        self.fecha_inicio = fecha_inicio
        self.fecha_fin = fecha_fin
        self.estado = estado
        self.id_postulacion = id_postulacion
        self.id_tutor_academico = id_tutor_academico
        self.id_tutor_empresarial = id_tutor_empresarial
        self.eliminado = eliminado

    def __repr__(self):
        return f"Practica(id='{self.id_practica}', estado='{self.estado}', postulacion='{self.id_postulacion}')"


class RepositorioPractica:
    ENTIDAD = 'practica'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def actualizar(self, practica):
        self.persistencia.actualizar(self.ENTIDAD, practica)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, id_practica):
        practica = self.persistencia.obtener(self.ENTIDAD, id_practica)
        return practica if practica is not None and not practica.eliminado else None

    def en_estados(self, estados):
        return self.persistencia.listar(self.ENTIDAD, where="estado = ANY(%s)", params=(list(estados),))

    def activa_de_postulaciones(self, ids_postulacion, estados):
        practicas = self.persistencia.listar(
            self.ENTIDAD,
            where="estado = ANY(%s) AND id_postulacion = ANY(%s)",
            params=(list(estados), list(ids_postulacion)))
        return practicas[0] if practicas else None

    def de_postulaciones(self, ids_postulacion):
        return self.persistencia.listar(
            self.ENTIDAD, where="id_postulacion = ANY(%s)", params=(list(ids_postulacion),))

    def de_tutor_empresarial(self, cedula):
        return self.persistencia.listar(
            self.ENTIDAD, where="id_tutor_empresarial = %s", params=(cedula,))

    def detalle_en_estados(self, estados):
        """Prácticas en ciertos estados con estudiante y tutores (JOIN vía vista)."""
        s = self.persistencia.schema
        return self.persistencia.consultar(
            f'SELECT * FROM "{s}".vista_practica_detalle '
            f'WHERE estado = ANY(%s) AND eliminado = FALSE ORDER BY id_practica',
            (list(estados),))

    def detalle_por_tutor_empresarial(self, cedula, estados):
        """Prácticas activas de una empresa con estudiante y tutor académico (JOIN vía vista)."""
        s = self.persistencia.schema
        return self.persistencia.consultar(
            f'SELECT * FROM "{s}".vista_practica_detalle '
            f'WHERE id_tutor_empresarial = %s AND estado = ANY(%s) AND eliminado = FALSE '
            f'ORDER BY id_practica',
            (cedula, list(estados)))

    def agregar(self, fecha_inicio, fecha_fin, estado, id_postulacion, id_tutor_academico, id_tutor_empresarial):
        nueva = Practica(None, fecha_inicio, fecha_fin, estado, id_postulacion,
                         id_tutor_academico, id_tutor_empresarial)
        self.persistencia.insertar(self.ENTIDAD, nueva)  # la base asigna id_practica
        return nueva


class RepositorioSolicitud:
    ENTIDAD = 'solicitud'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def actualizar(self, solicitud):
        self.persistencia.actualizar(self.ENTIDAD, solicitud)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, id_solicitud):
        solicitud = self.persistencia.obtener(self.ENTIDAD, id_solicitud)
        return solicitud if solicitud is not None and not solicitud.get("eliminado", False) else None

    def de_estudiante(self, cedula):
        return self.persistencia.listar(self.ENTIDAD, where="cedula_estudiante = %s", params=(cedula,))

    def por_estado(self, estado):
        return self.persistencia.listar(self.ENTIDAD, where="estado = %s", params=(estado,))

    @staticmethod
    def _validar_datos_empresa(datos):
        if not Validaciones.validar_texto_no_vacio(
                datos.get("nombre_empresa", ""), datos.get("direccion_empresa", "")):
            raise ValueError("El nombre y la dirección de la empresa no pueden estar vacíos.")
        if not Validaciones.validar_ruc(datos.get("ruc_empresa", "")):
            raise ValueError("El RUC de la empresa debe tener 13 dígitos y terminar en '001'.")
        if not Validaciones.validar_telefono(datos.get("telefono", "")):
            raise ValueError("El teléfono debe tener 10 dígitos y comenzar con '09'.")
        if not Validaciones.validar_email(datos.get("email", "")):
            raise ValueError("El correo electrónico no tiene un formato válido (ejemplo@dominio.com).")

    def agregar(self, tipo, motivo, cedula_estudiante, fecha, datos_empresa=None):
        if not motivo:
            raise ValueError("Debe ingresar el motivo o detalle de la solicitud.")
        if datos_empresa is not None:
            self._validar_datos_empresa(datos_empresa)
        nueva = {"tipo": tipo, "motivo": motivo, "estado": "Pendiente",
                 "cedula_estudiante": cedula_estudiante, "fecha": fecha, "datos_empresa": datos_empresa,
                 "eliminado": False}
        self.persistencia.insertar(self.ENTIDAD, nueva)  # la base asigna "id"
        return nueva
