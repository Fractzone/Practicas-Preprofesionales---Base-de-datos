"""
Gestor de persistencia respaldado por PostgreSQL (sobre SQLAlchemy 2.0).

Punto único de acceso a la base de datos. El esquema y el mapeo objeto↔tabla se
declaran con SQLAlchemy Core (objetos `Table`) y el mapeo a las clases del modelo
se hace de forma **imperativa** (`registry.map_imperatively`): las clases de
`modelo/` permanecen intactas (no importan SQLAlchemy ni heredan de ninguna base),
de modo que la separación por capas se conserva.

SQLAlchemy se encarga de:
  - Crear el esquema/tablas/índices/restricciones (FK, UNIQUE, CHECK, IDENTITY).
  - Materializar las filas como objetos del modelo SIN llamar a `__init__` (no se
    revalidan datos ya guardados), igual que la implementación manual anterior.
  - Convertir tipos mediante `TypeDecorator`:
        * FechaTexto  -> las fechas viajan como texto "dd/MM/yyyy" en la aplicación
                         y como DATE en la base.
        * ContrasenaHash -> las contraseñas se cifran (hash con sal) al escribir.
        * JSONB       -> tipo nativo de PostgreSQL para diccionarios/listas.

La API pública de esta clase NO cambia (obtener, existe, listar, insertar,
actualizar, marcar_eliminado(s)(_por), consultar, transaccion, ...), por lo que
los repositorios y controladores no se ven afectados.

Transacciones
-------------
Cada operación de escritura confirma por sí sola, salvo que se ejecute dentro de
`with gestor.transaccion():`, en cuyo caso todas las escrituras del bloque se
confirman juntas (o se revierten con rollback si algo falla). Admite anidamiento
(solo el bloque más externo confirma).

El borrado es lógico (columna `eliminado`); la cascada lógica vive en el código
(controlador/eliminacion_cascada.py).
"""
from contextlib import contextmanager
from datetime import date, datetime

from sqlalchemy import (
    create_engine, MetaData, Table, Column, ForeignKey, CheckConstraint, Identity, Index,
    Integer, String, Text, Boolean, Numeric, Date,
    select, insert, update, text, func, literal, inspect,
)
from sqlalchemy.engine import URL
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import registry, sessionmaker

from persistencia.config_bd import CONFIG_BD

from modelo.seguridad import hash_password, es_hash
from modelo.administrador import Administrador
from modelo.credencial import Credencial
from modelo.estudiante import Estudiante
from modelo.coordinadores import TutorAcademico, TutorEmpresarial, CoordinadorVinculacion
from modelo.proceso import Oferta, Postulacion, Practica
from modelo.formulario import Formulario1, Formulario2, Formulario3


FORMATO_FECHA = "%d/%m/%Y"
_SCHEMA = CONFIG_BD.get("schema", "public")

# Conjuntos de estados válidos (espejo de las máquinas de estado del modelo).
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


def _in(columna, valores):
    """Expresión SQL `columna IN ('a','b',...)` para una restricción CHECK."""
    lista = ", ".join("'" + v.replace("'", "''") + "'" for v in valores)
    return f"{columna} IN ({lista})"


# --------------------------------------------------------------------------- #
# Tipos personalizados (reemplazan la conversión manual hacia/desde la base)
# --------------------------------------------------------------------------- #
class FechaTexto(TypeDecorator):
    """Almacena DATE en la base, pero expone las fechas como texto 'dd/MM/yyyy'
    en la aplicación (formato que usa toda la interfaz)."""
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


class ContrasenaHash(TypeDecorator):
    """Cifra la contraseña (hash con sal) al escribir, si aún no está cifrada.
    Al leer devuelve el hash almacenado tal cual (la verificación se hace en
    modelo/seguridad.py)."""
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, str) and value and not es_hash(value):
            return hash_password(value)
        return value


# --------------------------------------------------------------------------- #
# Definición del esquema (SQLAlchemy Core) y mapeo imperativo a las clases
# --------------------------------------------------------------------------- #
metadata = MetaData(schema=_SCHEMA)
mapper_registry = registry(metadata=metadata)


def _falso():
    """server_default para columnas BOOLEAN `eliminado`."""
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
    # ruc_empresa UNIQUE: regla "una empresa = un tutor empresarial"; es la columna
    # referenciada por oferta.ruc_empresa.
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
# Índice adicional por estado (consultas de pendientes/validadas).
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


# Mapeo imperativo: asocia cada tabla con su clase del modelo sin tocar la clase.
# 'solicitud' no tiene clase (se maneja como dict plano), por eso no se mapea.
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

# Configura los mappers de inmediato: deja listos los descriptores de cada columna
# para que asignar atributos (en __init__ o al materializar con _crear) funcione
# desde el primer uso, sin depender de que se ejecute antes una consulta ORM.
mapper_registry.configure()


# Catálogo de entidades: tabla, clase (o None si es dict) y nombre de la clave.
ENTIDADES = {
    "administrador":            (tabla_administrador, Administrador, "usuario"),
    "login":                    (tabla_login, Credencial, "identificador"),
    "estudiante":               (tabla_estudiante, Estudiante, "cedula"),
    "tutor_academico":          (tabla_tutor_academico, TutorAcademico, "cedula"),
    "tutor_empresarial":        (tabla_tutor_empresarial, TutorEmpresarial, "cedula"),
    "coordinador_vinculacion":  (tabla_coordinador_vinculacion, CoordinadorVinculacion, "cedula"),
    "oferta":                   (tabla_oferta, Oferta, "id_oferta"),
    "postulacion":              (tabla_postulacion, Postulacion, "id_postulacion"),
    "practica":                 (tabla_practica, Practica, "id_practica"),
    "solicitud":                (tabla_solicitud, None, "id"),
    "formulario1":              (tabla_formulario1, Formulario1, "id_formulario1"),
    "formulario2":              (tabla_formulario2, Formulario2, "id_formulario2"),
    "formulario3":              (tabla_formulario3, Formulario3, "id_formulario3"),
}


# Vistas que cruzan tablas para los listados de la interfaz (los JOIN viven en la
# base). Se crean/reemplazan después de las tablas; SQLAlchemy no gestiona vistas.
def _ddl_vistas(s):
    return [
        f'''CREATE OR REPLACE VIEW "{s}".vista_postulacion_detalle AS
            SELECT p.id_postulacion, p.estado_validacion, p.fecha, p.eliminado,
                   p.cedula_estudiante,
                   e.nombres  AS est_nombres,  e.apellidos AS est_apellidos,
                   e.ciclo    AS est_ciclo,    e.num_practicas_realizadas AS est_num_practicas,
                   e.carrera  AS est_carrera,
                   p.id_oferta, o.puesto AS oferta_puesto, o.descripcion AS oferta_descripcion,
                   o.ruc_empresa, te.nombre_empresa
            FROM "{s}".postulacion p
            JOIN "{s}".estudiante e         ON p.cedula_estudiante = e.cedula
            JOIN "{s}".oferta o             ON p.id_oferta = o.id_oferta
            JOIN "{s}".tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa''',
        f'''CREATE OR REPLACE VIEW "{s}".vista_practica_detalle AS
            SELECT pr.id_practica, pr.estado, pr.fecha_inicio, pr.fecha_fin, pr.eliminado,
                   pr.id_postulacion, pr.id_tutor_academico, pr.id_tutor_empresarial,
                   e.cedula AS est_cedula, e.nombres AS est_nombres, e.apellidos AS est_apellidos,
                   e.carrera AS est_carrera,
                   ta.nombres AS acad_nombres, ta.apellidos AS acad_apellidos,
                   te.nombres AS emp_nombres,  te.apellidos AS emp_apellidos, te.nombre_empresa
            FROM "{s}".practica pr
            JOIN "{s}".postulacion p           ON pr.id_postulacion = p.id_postulacion
            JOIN "{s}".estudiante e            ON p.cedula_estudiante = e.cedula
            LEFT JOIN "{s}".tutor_academico ta   ON pr.id_tutor_academico = ta.cedula
            LEFT JOIN "{s}".tutor_empresarial te ON pr.id_tutor_empresarial = te.cedula''',
        f'''CREATE OR REPLACE VIEW "{s}".vista_oferta_detalle AS
            SELECT o.id_oferta, o.puesto, o.descripcion, o.fecha_publicacion, o.eliminado,
                   o.ruc_empresa, te.nombre_empresa
            FROM "{s}".oferta o
            JOIN "{s}".tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa''',
    ]


# Motor y fábrica de sesiones compartidos (un único pool para toda la aplicación).
_engine = create_engine(
    URL.create(
        "postgresql+psycopg2",
        username=CONFIG_BD["user"],
        password=CONFIG_BD["password"],
        host=CONFIG_BD["host"],
        port=CONFIG_BD["port"],
        database=CONFIG_BD["dbname"],
    ),
    client_encoding="utf8",
    future=True,
)
_Session = sessionmaker(bind=_engine, future=True)


class GestorPersistencia:

    def __init__(self):
        self.schema = _SCHEMA
        self._en_transaccion = False
        self._session = _Session()
        self._asegurar_esquema()

    # ------------------------------------------------------------------ #
    # Utilidades internas
    # ------------------------------------------------------------------ #
    @staticmethod
    def _entidad(entidad):
        return ENTIDADES[entidad]

    @staticmethod
    def _leer_atributo(objeto, columna):
        if isinstance(objeto, dict):
            return objeto.get(columna)
        return getattr(objeto, columna, None)

    @staticmethod
    def _asignar(objeto, columna, valor):
        if isinstance(objeto, dict):
            objeto[columna] = valor
        else:
            setattr(objeto, columna, valor)

    @staticmethod
    def _bindize(sql, params):
        """Traduce los marcadores posicionales '%s' (estilo psycopg2 que usan los
        repositorios) a parámetros nombrados ':_pN' para SQLAlchemy `text()`."""
        partes = sql.split("%s")
        if len(partes) == 1:
            return sql, {}
        binds = {}
        salida = [partes[0]]
        for i, parte in enumerate(partes[1:]):
            nombre = f"_p{i}"
            binds[nombre] = params[i]
            salida.append(f":{nombre}")
            salida.append(parte)
        return "".join(salida), binds

    def _condicion(self, where, params, incluir_eliminados):
        """Construye la cláusula WHERE (como `text()` con sus binds) combinando el
        filtro de borrado lógico con el `where` opcional del repositorio."""
        clausulas = []
        binds = {}
        if not incluir_eliminados:
            clausulas.append("eliminado = FALSE")
        if where:
            sql, b = self._bindize(where, tuple(params))
            clausulas.append(sql)
            binds.update(b)
        if not clausulas:
            return None
        condicion = text(" AND ".join(clausulas))
        return condicion.bindparams(**binds) if binds else condicion

    def _asegurar_esquema(self):
        """Crea esquema, tablas, índices, restricciones y vistas si no existen
        (idempotente)."""
        with _engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))
        metadata.create_all(_engine, checkfirst=True)
        with _engine.begin() as conn:
            for ddl in _ddl_vistas(self.schema):
                conn.execute(text(ddl))

    def _commit_si_corresponde(self):
        """Confirma solo si no estamos dentro de un bloque transaccion()."""
        if not self._en_transaccion:
            self._session.commit()

    @contextmanager
    def transaccion(self):
        """Agrupa varias escrituras en una sola transacción atómica: se confirman
        todas al salir del bloque, o se revierten si ocurre cualquier excepción.
        Soporta anidamiento (solo el bloque más externo confirma)."""
        anterior = self._en_transaccion
        self._en_transaccion = True
        try:
            yield
            if not anterior:
                self._session.commit()
        except Exception:
            self._session.rollback()
            raise
        finally:
            self._en_transaccion = anterior

    def close(self):
        """Cierra la sesión (devuelve la conexión al pool)."""
        self._session.close()

    # ------------------------------------------------------------------ #
    # Interfaz de acceso a datos (usada por los repositorios)
    # ------------------------------------------------------------------ #
    def obtener(self, entidad, clave):
        """Devuelve el objeto/dict con esa clave primaria, o None (incluye los
        marcados como eliminados; el filtrado por 'eliminado' lo decide quien
        llama)."""
        tabla, clase, pk = self._entidad(entidad)
        if clase is not None:
            return self._session.get(clase, clave)
        fila = self._session.execute(
            select(tabla).where(tabla.c[pk] == clave)).mappings().first()
        return dict(fila) if fila is not None else None

    def existe(self, entidad, clave):
        """True si la clave primaria existe físicamente (incluye eliminados)."""
        tabla, _clase, pk = self._entidad(entidad)
        fila = self._session.execute(
            select(literal(1)).select_from(tabla).where(tabla.c[pk] == clave).limit(1)
        ).first()
        return fila is not None

    def listar(self, entidad, where=None, params=(), incluir_eliminados=False, orden=None):
        """Lista objetos/dicts de la entidad. Por defecto excluye los eliminados.
        `where` es una cláusula SQL adicional con marcadores %s y `params` sus
        valores (compatibilidad con la API anterior)."""
        tabla, clase, _pk = self._entidad(entidad)
        objetivo = clase if clase is not None else tabla
        stmt = select(objetivo)
        condicion = self._condicion(where, params, incluir_eliminados)
        if condicion is not None:
            stmt = stmt.where(condicion)
        if orden:
            stmt = stmt.order_by(text(orden))
        if clase is not None:
            return list(self._session.execute(stmt).scalars().all())
        return [dict(f) for f in self._session.execute(stmt).mappings().all()]

    def insertar(self, entidad, objeto):
        """Alta de una fila. Si la tabla tiene id generado por la base (IDENTITY),
        se recupera con RETURNING y se asigna de vuelta al objeto."""
        tabla, clase, _pk = self._entidad(entidad)
        try:
            if clase is not None:
                self._session.add(objeto)
                self._session.flush()  # asigna los ids generados (IDENTITY)
            else:
                generadas = {c.name for c in tabla.columns if c.identity is not None}
                valores = {c.name: objeto[c.name]
                           for c in tabla.columns
                           if c.name not in generadas and c.name in objeto}
                identidad = [tabla.c[n] for n in
                             (c.name for c in tabla.columns if c.identity is not None)]
                stmt = insert(tabla).values(**valores)
                if identidad:
                    stmt = stmt.returning(*identidad)
                    fila = self._session.execute(stmt).first()
                    if fila is not None:
                        for col, valor in zip(identidad, fila):
                            objeto[col.name] = valor
                else:
                    self._session.execute(stmt)
            self._commit_si_corresponde()
        except Exception:
            self._session.rollback()
            raise

    def actualizar(self, entidad, objeto):
        """Modifica una fila existente identificada por su clave primaria."""
        tabla, clase, pk = self._entidad(entidad)
        try:
            if clase is not None:
                self._session.merge(objeto)
            else:
                generadas = {c.name for c in tabla.columns if c.identity is not None}
                valores = {c.name: objeto[c.name]
                           for c in tabla.columns
                           if c.name != pk and c.name not in generadas and c.name in objeto}
                self._session.execute(
                    update(tabla).where(tabla.c[pk] == objeto[pk]).values(**valores))
            self._commit_si_corresponde()
        except Exception:
            self._session.rollback()
            raise

    def marcar_eliminado(self, entidad, clave):
        """Eliminación lógica: marca la fila como eliminada."""
        tabla, _clase, pk = self._entidad(entidad)
        try:
            self._session.execute(
                update(tabla).where(tabla.c[pk] == clave).values(eliminado=True))
            self._commit_si_corresponde()
        except Exception:
            self._session.rollback()
            raise

    def marcar_eliminados(self, entidad, claves):
        """Eliminación lógica en lote por clave primaria (para la cascada)."""
        self.marcar_eliminados_por(entidad, self._entidad(entidad)[2], claves)

    def marcar_eliminados_por(self, entidad, columna, valores):
        """Eliminación lógica en lote filtrando por una columna cualquiera
        (p. ej. todos los formularios de un conjunto de prácticas). Dentro de un
        bloque transaccion() varias de estas marcas se confirman atómicamente."""
        valores = list(valores)
        if not valores:
            return
        tabla, _clase, _pk = self._entidad(entidad)
        try:
            self._session.execute(
                update(tabla).where(tabla.c[columna].in_(valores)).values(eliminado=True))
            self._commit_si_corresponde()
        except Exception:
            self._session.rollback()
            raise

    def consultar(self, sql, params=()):
        """Ejecuta una consulta SQL libre (p. ej. con JOIN sobre las vistas) y
        devuelve una lista de dicts {columna: valor}. Las columnas DATE se
        devuelven formateadas a 'dd/MM/yyyy' para mostrarse en la interfaz."""
        sql2, binds = self._bindize(sql, tuple(params))
        consulta = text(sql2)
        if binds:
            consulta = consulta.bindparams(**binds)
        try:
            filas = self._session.execute(consulta).mappings().all()
        except Exception:
            self._session.rollback()
            raise
        resultado = []
        for fila in filas:
            registro = {}
            for nombre, valor in fila.items():
                if isinstance(valor, (date, datetime)):
                    registro[nombre] = valor.strftime(FORMATO_FECHA)
                else:
                    registro[nombre] = valor
            resultado.append(registro)
        return resultado

    # ------------------------------------------------------------------ #
    # Sembrado de datos (escritura en lote, solo para el primer arranque)
    # ------------------------------------------------------------------ #
    def _guardar_lote(self, entidad, diccionario_datos):
        """Inserta/actualiza en lote un diccionario {clave: objeto} de forma
        idempotente (ON CONFLICT DO UPDATE). Lo usa únicamente el sembrado de
        datos del primer arranque, y solo para entidades con clave natural."""
        if not diccionario_datos:
            return
        tabla, _clase, pk = self._entidad(entidad)
        nombres = [c.name for c in tabla.columns]
        filas = [{col: self._leer_atributo(objeto, col) for col in nombres}
                 for objeto in diccionario_datos.values()]
        stmt = pg_insert(tabla).values(filas)
        actualizaciones = {col: stmt.excluded[col] for col in nombres if col != pk}
        stmt = stmt.on_conflict_do_update(index_elements=[pk], set_=actualizaciones)
        try:
            self._session.execute(stmt)
            self._commit_si_corresponde()
        except Exception:
            self._session.rollback()
            raise

    def _contar(self, entidad):
        tabla, _clase, _pk = self._entidad(entidad)
        return self._session.execute(select(func.count()).select_from(tabla)).scalar_one()

    # ------------------------------------------------------------------ #
    # Inicialización de datos
    # ------------------------------------------------------------------ #
    @staticmethod
    def inicializar_datos_si_vacio():
        """Crea esquema/tablas y, si no hay credenciales, siembra el admin y un
        conjunto de datos de ejemplo para poder probar la aplicación."""
        gestor = GestorPersistencia()
        if gestor._contar("login") > 0:
            return

        with gestor.transaccion():
            administrador = Administrador("admin", "admin", "admin@uce.edu.ec")
            gestor._guardar_lote("administrador", {administrador.usuario: administrador})
            gestor._guardar_lote("login", {
                administrador.usuario: Credencial(
                    administrador.usuario, administrador.contrasena, Administrador.ROL)
            })
            gestor._sembrar_datos_ejemplo()

    @staticmethod
    def _crear(clase, atributos):
        """Instancia una clase del modelo sin pasar por sus validaciones. Para las
        clases mapeadas se usa el class_manager de SQLAlchemy (igual que al
        materializar una fila), de modo que la instancia tenga su estado ORM sin
        ejecutar __init__."""
        try:
            objeto = inspect(clase).class_manager.new_instance()
        except Exception:
            objeto = clase.__new__(clase)
        for nombre, valor in atributos.items():
            setattr(objeto, nombre, valor)
        return objeto

    def _sembrar_datos_ejemplo(self):
        """Inserta datos de ejemplo ajustados a la estructura del modelo. Se evita
        la validación del constructor usando _crear. Cada usuario recibe su
        credencial de acceso."""
        credenciales = {}

        # --- Estudiantes ---
        estudiantes = {
            "1032222224": self._crear(Estudiante, {
                "cedula": "1032222224", "contrasena": "est123",
                "apellidos": "Mendez", "nombres": "Carlos",
                "telefono": "0991111111", "email": "carlos.mendez@ucuenca.edu.ec",
                "carrera": "Ingeniería de Software", "ciclo": 7,
                "num_practicas_realizadas": 0, "total_horas_realizadas": 0,
                "eliminado": False}),
            "2451212126": self._crear(Estudiante, {
                "cedula": "2451212126", "contrasena": "est123",
                "apellidos": "Paz", "nombres": "Lucia",
                "telefono": "0992222222", "email": "lucia.paz@ucuenca.edu.ec",
                "carrera": "Ingeniería de Software", "ciclo": 8,
                "num_practicas_realizadas": 1, "total_horas_realizadas": 240,
                "eliminado": False}),
            "1846543211": self._crear(Estudiante, {
                "cedula": "1846543211", "contrasena": "est123",
                "apellidos": "Vargas", "nombres": "Diego",
                "telefono": "0993333333", "email": "diego.vargas@ucuenca.edu.ec",
                "carrera": "Ingeniería Civil", "ciclo": 9,
                "num_practicas_realizadas": 0, "total_horas_realizadas": 0,
                "eliminado": False}),
        }
        for cedula in estudiantes:
            credenciales[cedula] = Credencial(cedula, "est123", Estudiante.ROL)
        self._guardar_lote("estudiante", estudiantes)

        # --- Tutores académicos ---
        tutores_academicos = {
            "0123456782": self._crear(TutorAcademico, {
                "cedula": "0123456782", "contrasena": "ta123",
                "nombres": "Hugo", "apellidos": "Añazco",
                "telefono": "0919265583", "email": "hugo.anazco@ucuenca.edu.ec",
                "carrera": "Ingeniería de Software", "eliminado": False}),
            "0912345675": self._crear(TutorAcademico, {
                "cedula": "0912345675", "contrasena": "ta123",
                "nombres": "Eric", "apellidos": "Martinez",
                "telefono": "0992371889", "email": "eric.martinez@ucuenca.edu.ec",
                "carrera": "Ingeniería Civil", "eliminado": False}),
        }
        for cedula in tutores_academicos:
            credenciales[cedula] = Credencial(cedula, "ta123", TutorAcademico.ROL)
        self._guardar_lote("tutor_academico", tutores_academicos)

        # --- Tutores empresariales (empresa embebida) ---
        tutores_empresariales = {
            "0107778889": self._crear(TutorEmpresarial, {
                "cedula": "0107778889", "contrasena": "te123",
                "nombres": "Roberto", "apellidos": "Arias",
                "telefono": "0995377124", "email": "roberto@autofact.com",
                "cargo": "Gerente de TI", "ruc_empresa": "0101010106001",
                "nombre_empresa": "AutoFact",
                "direccion_empresa": "Av. de las Américas & Simón Bolívar",
                "eliminado": False}),
            "0108889990": self._crear(TutorEmpresarial, {
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
        self._guardar_lote("tutor_empresarial", tutores_empresariales)

        # --- Coordinador de vinculación ---
        coordinadores = {
            "0755555554": self._crear(CoordinadorVinculacion, {
                "cedula": "0755555554", "contrasena": "cv123",
                "nombres": "Manuel", "apellidos": "Perez",
                "telefono": "0994444444", "email": "manuel.perez@ucuenca.edu.ec",
                "fecha_nacimiento": "15/05/1980", "direccion": "Cuenca, Azuay",
                "carrera": "Ingeniería de Software", "eliminado": False}),
        }
        for cedula in coordinadores:
            credenciales[cedula] = Credencial(cedula, "cv123", CoordinadorVinculacion.ROL)
        self._guardar_lote("coordinador_vinculacion", coordinadores)

        # --- Ofertas (el id lo genera la base; lo recuperamos con insertar) ---
        oferta_backend = self._crear(Oferta, {
            "descripcion": "Desarrollo de API REST", "puesto": "Pasante Backend",
            "fecha_publicacion": "01/03/2026", "ruc_empresa": "0101010106001",
            "eliminado": False})
        oferta_frontend = self._crear(Oferta, {
            "descripcion": "Creación de interfaces web", "puesto": "Pasante Frontend",
            "fecha_publicacion": "02/10/2026", "ruc_empresa": "0920202025001",
            "eliminado": False})
        self.insertar("oferta", oferta_backend)
        self.insertar("oferta", oferta_frontend)

        # --- Postulaciones (pendientes de validación) ---
        postulacion1 = self._crear(Postulacion, {
            "fecha": "04/03/2026", "estado_validacion": "Pendiente",
            "cedula_estudiante": "1032222224", "id_oferta": oferta_backend.id_oferta,
            "id_coordinador": None, "eliminado": False})
        postulacion2 = self._crear(Postulacion, {
            "fecha": "11/10/2026", "estado_validacion": "Pendiente",
            "cedula_estudiante": "2451212126", "id_oferta": oferta_frontend.id_oferta,
            "id_coordinador": None, "eliminado": False})
        self.insertar("postulacion", postulacion1)
        self.insertar("postulacion", postulacion2)

        # --- Credenciales de acceso de todos los usuarios sembrados ---
        self._guardar_lote("login", credenciales)
