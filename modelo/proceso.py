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

    @staticmethod
    def buscar_por_id(diccionario_ofertas, id_buscado):
        return diccionario_ofertas.get(id_buscado, None)

    def __repr__(self):
        return f"Oferta(id='{self.id_oferta}', puesto='{self.puesto}', empresa='{self.ruc_empresa}')"


class RepositorioOferta:
    ENTIDAD = 'oferta'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.ofertas = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.ofertas = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.ofertas)

    def listar(self):
        return list(filter(lambda o: not o.eliminado, self.ofertas.values()))

    def buscar(self, id_oferta):
        oferta = Oferta.buscar_por_id(self.ofertas, id_oferta)
        return oferta if oferta is not None and not oferta.eliminado else None

    def de_empresa(self, ruc_empresa):
        return list(filter(lambda o: o.ruc_empresa == ruc_empresa and not o.eliminado, self.ofertas.values()))

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.ofertas.keys()))),
            default=0) + 1)

    def agregar(self, descripcion, puesto, fecha_publicacion, ruc_empresa):
        if not ruc_empresa:
            raise ValueError("Seleccione una empresa.")
        if not all([puesto, descripcion]):
            raise ValueError("Complete el puesto y la descripción.")
        nuevo_id = self.siguiente_id()
        nueva = Oferta(nuevo_id, descripcion, puesto, fecha_publicacion, ruc_empresa)
        self.ofertas[nuevo_id] = nueva
        self.guardar()
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

    @staticmethod
    def buscar_por_id(diccionario_postulaciones, id_buscado):
        return diccionario_postulaciones.get(id_buscado, None)

    def __repr__(self):
        return f"Postulacion(id='{self.id_postulacion}', estado='{self.estado_validacion}', estudiante='{self.cedula_estudiante}')"


class RepositorioPostulacion:
    ENTIDAD = 'postulacion'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.postulaciones = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.postulaciones = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.postulaciones)

    def listar(self):
        return list(filter(lambda p: not p.eliminado, self.postulaciones.values()))

    def buscar(self, id_postulacion):
        postulacion = Postulacion.buscar_por_id(self.postulaciones, id_postulacion)
        return postulacion if postulacion is not None and not postulacion.eliminado else None

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.postulaciones.keys()))),
            default=0) + 1)

    def de_estudiante(self, cedula):
        return list(filter(lambda p: p.cedula_estudiante == cedula and not p.eliminado, self.postulaciones.values()))

    def de_ofertas(self, ids_oferta):
        return list(filter(lambda p: p.id_oferta in ids_oferta and not p.eliminado, self.postulaciones.values()))

    def por_estado(self, estado):
        return list(filter(lambda p: p.estado_validacion == estado and not p.eliminado, self.postulaciones.values()))

    def validadas_de_oferta(self, id_oferta):
        return list(filter(
            lambda p: p.estado_validacion == "Validada" and p.id_oferta == id_oferta and not p.eliminado,
            self.postulaciones.values()))

    def tiene_activa_para_oferta(self, cedula, id_oferta):
        return any(filter(
            lambda p: p.cedula_estudiante == cedula and p.id_oferta == id_oferta and
                      p.estado_validacion != "Rechazada" and not p.eliminado,
            self.postulaciones.values()))

    def agregar(self, fecha, estado, cedula_estudiante, id_oferta, id_coordinador):
        nuevo_id = self.siguiente_id()
        nueva = Postulacion(nuevo_id, fecha, estado, cedula_estudiante, id_oferta, id_coordinador)
        self.postulaciones[nuevo_id] = nueva
        self.guardar()
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

    @staticmethod
    def buscar_por_id(diccionario_practicas, id_buscado):
        return diccionario_practicas.get(id_buscado, None)

    def __repr__(self):
        return f"Practica(id='{self.id_practica}', estado='{self.estado}', postulacion='{self.id_postulacion}')"


class RepositorioPractica:
    ENTIDAD = 'practica'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.practicas = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.practicas = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.practicas)

    def listar(self):
        return list(filter(lambda p: not p.eliminado, self.practicas.values()))

    def buscar(self, id_practica):
        practica = Practica.buscar_por_id(self.practicas, id_practica)
        return practica if practica is not None and not practica.eliminado else None

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.practicas.keys()))),
            default=0) + 1)

    def en_estados(self, estados):
        return list(filter(lambda p: p.estado in estados and not p.eliminado, self.practicas.values()))

    def activa_de_postulaciones(self, ids_postulacion, estados):
        return next(filter(
            lambda pr: pr.estado in estados and pr.id_postulacion in ids_postulacion and not pr.eliminado,
            self.practicas.values()), None)

    def por_tutor_academico(self, cedula, estados):
        return list(filter(
            lambda pr: pr.id_tutor_academico == cedula and pr.estado in estados and not pr.eliminado,
            self.practicas.values()))

    def por_tutor_empresarial(self, cedula, estados):
        return list(filter(
            lambda pr: pr.id_tutor_empresarial == cedula and pr.estado in estados and not pr.eliminado,
            self.practicas.values()))

    def de_postulaciones(self, ids_postulacion):
        return list(filter(
            lambda pr: pr.id_postulacion in ids_postulacion and not pr.eliminado,
            self.practicas.values()))

    def de_tutor_empresarial(self, cedula):
        return list(filter(
            lambda pr: pr.id_tutor_empresarial == cedula and not pr.eliminado,
            self.practicas.values()))

    def agregar(self, fecha_inicio, fecha_fin, estado, id_postulacion, id_tutor_academico, id_tutor_empresarial):
        nuevo_id = self.siguiente_id()
        nueva = Practica(nuevo_id, fecha_inicio, fecha_fin, estado, id_postulacion,
                         id_tutor_academico, id_tutor_empresarial)
        self.practicas[nuevo_id] = nueva
        self.guardar()
        return nueva


class RepositorioSolicitud:
    ENTIDAD = 'solicitud'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.solicitudes = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.solicitudes = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.solicitudes)

    def listar(self):
        return list(filter(lambda s: not s.get("eliminado", False), self.solicitudes.values()))

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.solicitudes.keys()))),
            default=0) + 1)

    def buscar(self, id_solicitud):
        solicitud = self.solicitudes.get(id_solicitud, None)
        return solicitud if solicitud is not None and not solicitud.get("eliminado", False) else None

    def de_estudiante(self, cedula):
        return list(filter(lambda s: s.get("cedula_estudiante") == cedula and not s.get("eliminado", False),
                           self.solicitudes.values()))

    def por_estado(self, estado):
        return list(filter(lambda s: s.get("estado") == estado and not s.get("eliminado", False),
                           self.solicitudes.values()))

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
        nuevo_id = self.siguiente_id()
        nueva = {"id": nuevo_id, "tipo": tipo, "motivo": motivo, "estado": "Pendiente",
                 "cedula_estudiante": cedula_estudiante, "fecha": fecha, "datos_empresa": datos_empresa,
                 "eliminado": False}
        self.solicitudes[nuevo_id] = nueva
        self.guardar()
        return nueva
