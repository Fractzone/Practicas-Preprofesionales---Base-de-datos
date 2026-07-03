from datetime import date, datetime

from sqlalchemy import (
    MetaData, Table, Column, ForeignKey, CheckConstraint, Identity, Index,
    Integer, String, Text, Boolean, Numeric, Date,
    text, inspect,
)
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import registry
from persistencia.config_bd import CONFIG_BD
from modelo.seguridad import hash_password, es_hash
from modelo.administrador import Administrador
from modelo.credencial import Credencial
from modelo.estudiante import Estudiante
from modelo.coordinadores import TutorAcademico, TutorEmpresarial, CoordinadorVinculacion
from modelo.proceso import Oferta, Postulacion, Practica
from modelo.formulario import Formulario1, Formulario2, Formulario3

"""
Configuraciones para los formatos
"""
FORMATO_FECHA = "%d/%m/%Y"
_SCHEMA = CONFIG_BD.get("schema", "public")

ROLES = ("administrador", "estudiante", "tutor_academico",
         "tutor_empresarial", "coordinador_vinculacion")
ESTADOS_POSTULACION = ("Pendiente", "Validada", "Enviada", "Aceptada", "Rechazada")
ESTADOS_PRACTICA = ("En progreso", "En Ejecución", "Evaluación Solicitada",
                    "Pendiente Nota", "Finalizada / Aprobada")
ESTADOS_SOLICITUD = ("Pendiente", "Aprobada", "Rechazada")
TIPOS_SOLICITUD = ("Autorización de Empresa Propia", "Emisión de Certificado/Oficio")
ESTADOS_FORM1 = ("Pendiente", "Aprobado")
ESTADOS_FORM2 = ("Completado",)
ESTADOS_FORM3 = ("Completado",)

metadata = MetaData(schema=_SCHEMA)
mapper_registry = registry(metadata=metadata)

#Traductor para los CHECK
def _in(columna, valores):
    lista = ", ".join("'" + v.replace("'", "''") + "'" for v in valores)
    return f"{columna} IN ({lista})"

class FechaTexto(TypeDecorator):
    impl = Date
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None or value == "":
            return None
        if isinstance(value, str):
            return datetime.strptime(value, FORMATO_FECHA).date()
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, (date, datetime)):
            return value.strftime(FORMATO_FECHA)
        return value

#Cifra la contraseña
class ContrasenaHash(TypeDecorator):
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, str) and value and not es_hash(value):
            return hash_password(value)
        return value

def _falso():
    return text("FALSE")

tabla_administrador = Table(
    "administrador", metadata,
    Column("usuario", String(20), primary_key=True),
    Column("contrasena", ContrasenaHash(255), nullable=False),
    Column("email", String(120), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
)

tabla_login = Table(
    "login", metadata,
    Column("identificador", String(20), primary_key=True),
    Column("contrasena", ContrasenaHash(255), nullable=False),
    Column("rol", String(30), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint(_in("rol", ROLES), name="ck_login_rol"),
)

tabla_estudiante = Table(
    "estudiante", metadata,
    Column("cedula", String(10), primary_key=True),
    Column("contrasena", ContrasenaHash(255), nullable=False),
    Column("apellidos", String(100), nullable=False),
    Column("nombres", String(100), nullable=False),
    Column("telefono", String(10), nullable=False),
    Column("email", String(120), nullable=False, unique=True),
    Column("carrera", String(100), nullable=False),
    Column("ciclo", Integer, nullable=False),
    Column("num_practicas_realizadas", Integer, nullable=False, server_default=text("0")),
    Column("total_horas_realizadas", Integer, nullable=False, server_default=text("0")),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint("ciclo BETWEEN 1 AND 10", name="ck_estudiante_ciclo"),
    CheckConstraint("num_practicas_realizadas >= 0", name="ck_estudiante_num_practicas"),
    CheckConstraint("total_horas_realizadas >= 0", name="ck_estudiante_total_horas"),
)

tabla_tutor_academico = Table(
    "tutor_academico", metadata,
    Column("cedula", String(10), primary_key=True),
    Column("contrasena", ContrasenaHash(255), nullable=False),
    Column("nombres", String(100), nullable=False),
    Column("apellidos", String(100), nullable=False),
    Column("telefono", String(10), nullable=False),
    Column("email", String(120), nullable=False, unique=True),
    Column("carrera", String(100), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
)

tabla_tutor_empresarial = Table(
    "tutor_empresarial", metadata,
    Column("cedula", String(10), primary_key=True),
    Column("contrasena", ContrasenaHash(255), nullable=False),
    Column("nombres", String(100), nullable=False),
    Column("apellidos", String(100), nullable=False),
    Column("telefono", String(10), nullable=False),
    Column("email", String(120), nullable=False, unique=True),
    Column("cargo", String(100), nullable=False),
    Column("ruc_empresa", String(13), nullable=False, unique=True),
    Column("nombre_empresa", String(150), nullable=False),
    Column("direccion_empresa", String(255), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
)

tabla_coordinador_vinculacion = Table(
    "coordinador_vinculacion", metadata,
    Column("cedula", String(10), primary_key=True),
    Column("contrasena", ContrasenaHash(255), nullable=False),
    Column("nombres", String(100), nullable=False),
    Column("apellidos", String(100), nullable=False),
    Column("telefono", String(10), nullable=False),
    Column("email", String(120), nullable=False, unique=True),
    Column("fecha_nacimiento", FechaTexto, nullable=False),
    Column("direccion", String(255), nullable=False),
    Column("carrera", String(100), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
)

tabla_oferta = Table(
    "oferta", metadata,
    Column("id_oferta", Integer, Identity(always=True), primary_key=True),
    Column("descripcion", Text, nullable=False),
    Column("puesto", String(100), nullable=False),
    Column("fecha_publicacion", FechaTexto),
    Column("ruc_empresa", String(13),
           ForeignKey(tabla_tutor_empresarial.c.ruc_empresa), nullable=False, index=True),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
)

tabla_postulacion = Table(
    "postulacion", metadata,
    Column("id_postulacion", Integer, Identity(always=True), primary_key=True),
    Column("fecha", FechaTexto),
    Column("estado_validacion", String(20), nullable=False),
    Column("cedula_estudiante", String(10),
           ForeignKey(tabla_estudiante.c.cedula), nullable=False, index=True),
    Column("id_oferta", Integer,
           ForeignKey(tabla_oferta.c.id_oferta), nullable=False, index=True),
    Column("id_coordinador", String(10),
           ForeignKey(tabla_coordinador_vinculacion.c.cedula)),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint(_in("estado_validacion", ESTADOS_POSTULACION),
                    name="ck_postulacion_estado"),
)
Index("idx_postulacion_estado_validacion", tabla_postulacion.c.estado_validacion)

tabla_practica = Table(
    "practica", metadata,
    Column("id_practica", Integer, Identity(always=True), primary_key=True),
    Column("fecha_inicio", FechaTexto),
    Column("fecha_fin", FechaTexto),
    Column("estado", String(30), nullable=False),
    Column("id_postulacion", Integer,
           ForeignKey(tabla_postulacion.c.id_postulacion), nullable=False, index=True),
    Column("id_tutor_academico", String(10),
           ForeignKey(tabla_tutor_academico.c.cedula)),
    Column("id_tutor_empresarial", String(10),
           ForeignKey(tabla_tutor_empresarial.c.cedula)),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint(_in("estado", ESTADOS_PRACTICA), name="ck_practica_estado"),
)

tabla_solicitud = Table(
    "solicitud", metadata,
    Column("id", Integer, Identity(always=True), primary_key=True),
    Column("tipo", String(60), nullable=False),
    Column("motivo", Text, nullable=False),
    Column("estado", String(20), nullable=False),
    Column("cedula_estudiante", String(10),
           ForeignKey(tabla_estudiante.c.cedula), nullable=False, index=True),
    Column("fecha", FechaTexto),
    Column("datos_empresa", JSONB),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint(_in("estado", ESTADOS_SOLICITUD), name="ck_solicitud_estado"),
    CheckConstraint(_in("tipo", TIPOS_SOLICITUD), name="ck_solicitud_tipo"),
)

tabla_formulario1 = Table(
    "formulario1", metadata,
    Column("id_formulario1", Integer, Identity(always=True), primary_key=True),
    Column("id_practica", Integer,
           ForeignKey(tabla_practica.c.id_practica), nullable=False, index=True),
    Column("tipo_documento", String(40), nullable=False),
    Column("numero_documento", String(50), nullable=False),
    Column("tipo_practica", String(30), nullable=False),
    Column("remuneracion", Numeric(10, 2), nullable=False),
    Column("fecha_inicial", FechaTexto),
    Column("fecha_final_aprox", FechaTexto),
    Column("horas_aprox", Integer, nullable=False),
    Column("actividades", JSONB, nullable=False),
    Column("estado_aprobacion", String(20), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint(_in("estado_aprobacion", ESTADOS_FORM1), name="ck_form1_estado"),
    CheckConstraint("remuneracion >= 0", name="ck_form1_remuneracion"),
    CheckConstraint("horas_aprox > 0", name="ck_form1_horas"),
)

tabla_formulario2 = Table(
    "formulario2", metadata,
    Column("id_formulario2", Integer, Identity(always=True), primary_key=True),
    Column("id_practica", Integer,
           ForeignKey(tabla_practica.c.id_practica), nullable=False, index=True),
    Column("fecha_real_inicio", FechaTexto),
    Column("fecha_real_fin", FechaTexto),
    Column("horas_cumplidas", Integer, nullable=False),
    Column("calificaciones_rubrica", JSONB, nullable=False),
    Column("productos_relevantes", Text, nullable=False),
    Column("aspectos_relevantes", Text, nullable=False),
    Column("estado", String(20), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint("horas_cumplidas > 0", name="ck_form2_horas"),
    CheckConstraint(_in("estado", ESTADOS_FORM2), name="ck_form2_estado"),
)

tabla_formulario3 = Table(
    "formulario3", metadata,
    Column("id_formulario3", Integer, Identity(always=True), primary_key=True),
    Column("id_practica", Integer,
           ForeignKey(tabla_practica.c.id_practica), nullable=False, index=True),
    Column("campo_ocupacional", String(150), nullable=False),
    Column("calificacion_sobre_100", Numeric(5, 2), nullable=False),
    Column("evaluacion_escenario", JSONB, nullable=False),
    Column("estado", String(20), nullable=False),
    Column("eliminado", Boolean, nullable=False, server_default=_falso()),
    CheckConstraint("calificacion_sobre_100 BETWEEN 0 AND 100", name="ck_form3_calificacion"),
    CheckConstraint(_in("estado", ESTADOS_FORM3), name="ck_form3_estado"),
)

#Configura el mapeo de clase->Talba y biseversa
mapper_registry.map_imperatively(Administrador, tabla_administrador)
mapper_registry.map_imperatively(Credencial, tabla_login)
mapper_registry.map_imperatively(Estudiante, tabla_estudiante)
mapper_registry.map_imperatively(TutorAcademico, tabla_tutor_academico)
mapper_registry.map_imperatively(TutorEmpresarial, tabla_tutor_empresarial)
mapper_registry.map_imperatively(CoordinadorVinculacion, tabla_coordinador_vinculacion)
mapper_registry.map_imperatively(Oferta, tabla_oferta)
mapper_registry.map_imperatively(Postulacion, tabla_postulacion)
mapper_registry.map_imperatively(Practica, tabla_practica)
mapper_registry.map_imperatively(Formulario1, tabla_formulario1)
mapper_registry.map_imperatively(Formulario2, tabla_formulario2)
mapper_registry.map_imperatively(Formulario3, tabla_formulario3)

mapper_registry.configure()

#Diccionario para que las funciones sepan como actuar segun la operacion
ENTIDADES = {
    "administrador": (tabla_administrador, Administrador, "usuario"),
    "login": (tabla_login, Credencial, "identificador"),
    "estudiante": (tabla_estudiante, Estudiante, "cedula"),
    "tutor_academico": (tabla_tutor_academico, TutorAcademico, "cedula"),
    "tutor_empresarial": (tabla_tutor_empresarial, TutorEmpresarial, "cedula"),
    "coordinador_vinculacion": (tabla_coordinador_vinculacion, CoordinadorVinculacion, "cedula"),
    "oferta": (tabla_oferta, Oferta, "id_oferta"),
    "postulacion": (tabla_postulacion, Postulacion, "id_postulacion"),
    "practica": (tabla_practica, Practica, "id_practica"),
    "solicitud": (tabla_solicitud, None, "id"),
    "formulario1": (tabla_formulario1, Formulario1, "id_formulario1"),
    "formulario2": (tabla_formulario2, Formulario2, "id_formulario2"),
    "formulario3": (tabla_formulario3, Formulario3, "id_formulario3"),
}


def _ddl_vistas(s):
    return [
        f'''CREATE OR REPLACE VIEW "{s}".vista_postulacion_detalle AS
            SELECT p.id_postulacion, p.estado_validacion, p.fecha, p.eliminado,
                   p.cedula_estudiante,
                   e.nombres AS est_nombres, e.apellidos AS est_apellidos,
                   e.ciclo AS est_ciclo, e.num_practicas_realizadas AS est_num_practicas,
                   e.carrera AS est_carrera,
                   p.id_oferta, o.puesto AS oferta_puesto, o.descripcion AS oferta_descripcion,
                   o.ruc_empresa, te.nombre_empresa
            FROM "{s}".postulacion p
            JOIN "{s}".estudiante e ON p.cedula_estudiante = e.cedula
            JOIN "{s}".oferta o ON p.id_oferta = o.id_oferta
            JOIN "{s}".tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa''',
        f'''CREATE OR REPLACE VIEW "{s}".vista_practica_detalle AS
            SELECT pr.id_practica, pr.estado, pr.fecha_inicio, pr.fecha_fin, pr.eliminado,
                   pr.id_postulacion, pr.id_tutor_academico, pr.id_tutor_empresarial,
                   e.cedula AS est_cedula, e.nombres AS est_nombres, e.apellidos AS est_apellidos,
                   e.carrera AS est_carrera,
                   ta.nombres AS acad_nombres, ta.apellidos AS acad_apellidos,
                   te.nombres AS emp_nombres, te.apellidos AS emp_apellidos, te.nombre_empresa
            FROM "{s}".practica pr
            JOIN "{s}".postulacion p ON pr.id_postulacion = p.id_postulacion
            JOIN "{s}".estudiante e ON p.cedula_estudiante = e.cedula
            LEFT JOIN "{s}".tutor_academico ta ON pr.id_tutor_academico = ta.cedula
            LEFT JOIN "{s}".tutor_empresarial te ON pr.id_tutor_empresarial = te.cedula''',
        f'''CREATE OR REPLACE VIEW "{s}".vista_oferta_detalle AS
            SELECT o.id_oferta, o.puesto, o.descripcion, o.fecha_publicacion, o.eliminado,
                   o.ruc_empresa, te.nombre_empresa
            FROM "{s}".oferta o
            JOIN "{s}".tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa''',
    ]


def _crear(clase, atributos):
    try:
        objeto = inspect(clase).class_manager.new_instance()
    except Exception:
        objeto = clase.__new__(clase)
    for nombre, valor in atributos.items():
        setattr(objeto, nombre, valor)
    return objeto


def sembrar_datos_ejemplo(gestor):
    credenciales = {}

    estudiantes = {
        "1032222224": _crear(Estudiante, {
            "cedula": "1032222224", "contrasena": "est123",
            "apellidos": "Mendez", "nombres": "Carlos",
            "telefono": "0991111111", "email": "carlos.mendez@ucuenca.edu.ec",
            "carrera": "Ingeniería de Software", "ciclo": 7,
            "num_practicas_realizadas": 0, "total_horas_realizadas": 0,
            "eliminado": False}),
        "2451212126": _crear(Estudiante, {
            "cedula": "2451212126", "contrasena": "est123",
            "apellidos": "Paz", "nombres": "Lucia",
            "telefono": "0992222222", "email": "lucia.paz@ucuenca.edu.ec",
            "carrera": "Ingeniería de Software", "ciclo": 8,
            "num_practicas_realizadas": 1, "total_horas_realizadas": 240,
            "eliminado": False}),
        "1846543211": _crear(Estudiante, {
            "cedula": "1846543211", "contrasena": "est123",
            "apellidos": "Vargas", "nombres": "Diego",
            "telefono": "0993333333", "email": "diego.vargas@ucuenca.edu.ec",
            "carrera": "Ingeniería Civil", "ciclo": 9,
            "num_practicas_realizadas": 0, "total_horas_realizadas": 0,
            "eliminado": False}),
    }
    for cedula in estudiantes:
        credenciales[cedula] = Credencial(cedula, "est123", Estudiante.ROL)
    gestor._guardar_lote("estudiante", estudiantes)

    tutores_academicos = {
        "0123456782": _crear(TutorAcademico, {
            "cedula": "0123456782", "contrasena": "ta123",
            "nombres": "Hugo", "apellidos": "Añazco",
            "telefono": "0919265583", "email": "hugo.anazco@ucuenca.edu.ec",
            "carrera": "Ingeniería de Software", "eliminado": False}),
        "0912345675": _crear(TutorAcademico, {
            "cedula": "0912345675", "contrasena": "ta123",
            "nombres": "Eric", "apellidos": "Martinez",
            "telefono": "0992371889", "email": "eric.martinez@ucuenca.edu.ec",
            "carrera": "Ingeniería Civil", "eliminado": False}),
    }
    for cedula in tutores_academicos:
        credenciales[cedula] = Credencial(cedula, "ta123", TutorAcademico.ROL)
    gestor._guardar_lote("tutor_academico", tutores_academicos)

    tutores_empresariales = {
        "0107778889": _crear(TutorEmpresarial, {
            "cedula": "0107778889", "contrasena": "te123",
            "nombres": "Roberto", "apellidos": "Arias",
            "telefono": "0995377124", "email": "roberto@autofact.com",
            "cargo": "Gerente de TI", "ruc_empresa": "0101010106001",
            "nombre_empresa": "AutoFact",
            "direccion_empresa": "Av. de las Américas & Simón Bolívar",
            "eliminado": False}),
        "0108889990": _crear(TutorEmpresarial, {
            "cedula": "0108889990", "contrasena": "te123",
            "nombres": "Camila", "apellidos": "Ortiz",
            "telefono": "0908699931", "email": "camila@optisolver.com",
            "cargo": "Líder de Desarrollo", "ruc_empresa": "0920202025001",
            "nombre_empresa": "OptiSolver",
            "direccion_empresa": "Calle Larga & Hermano Miguel",
            "eliminado": False}),
    }
    for cedula in tutores_empresariales:
        credenciales[cedula] = Credencial(cedula, "te123", TutorEmpresarial.ROL)
    gestor._guardar_lote("tutor_empresarial", tutores_empresariales)

    coordinadores = {
        "0755555554": _crear(CoordinadorVinculacion, {
            "cedula": "0755555554", "contrasena": "cv123",
            "nombres": "Manuel", "apellidos": "Perez",
            "telefono": "0994444444", "email": "manuel.perez@ucuenca.edu.ec",
            "fecha_nacimiento": "15/05/1980", "direccion": "Cuenca, Azuay",
            "carrera": "Ingeniería de Software", "eliminado": False}),
    }
    for cedula in coordinadores:
        credenciales[cedula] = Credencial(cedula, "cv123", CoordinadorVinculacion.ROL)
    gestor._guardar_lote("coordinador_vinculacion", coordinadores)

    oferta_backend = _crear(Oferta, {
        "descripcion": "Desarrollo de API REST", "puesto": "Pasante Backend",
        "fecha_publicacion": "01/03/2026", "ruc_empresa": "0101010106001",
        "eliminado": False})
    oferta_frontend = _crear(Oferta, {
        "descripcion": "Creación de interfaces web", "puesto": "Pasante Frontend",
        "fecha_publicacion": "02/10/2026", "ruc_empresa": "0920202025001",
        "eliminado": False})
    gestor.insertar("oferta", oferta_backend)
    gestor.insertar("oferta", oferta_frontend)

    postulacion1 = _crear(Postulacion, {
        "fecha": "04/03/2026", "estado_validacion": "Pendiente",
        "cedula_estudiante": "1032222224", "id_oferta": oferta_backend.id_oferta,
        "id_coordinador": None, "eliminado": False})
    postulacion2 = _crear(Postulacion, {
        "fecha": "11/10/2026", "estado_validacion": "Pendiente",
        "cedula_estudiante": "2451212126", "id_oferta": oferta_frontend.id_oferta,
        "id_coordinador": None, "eliminado": False})
    gestor.insertar("postulacion", postulacion1)
    gestor.insertar("postulacion", postulacion2)

    gestor._guardar_lote("login", credenciales)
