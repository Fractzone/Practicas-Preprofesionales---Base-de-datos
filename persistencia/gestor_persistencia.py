"""
Gestor de persistencia respaldado por PostgreSQL.

Punto único de acceso a la base de datos. El esquema declara integridad
referencial (claves foráneas), restricciones (NOT NULL, UNIQUE, CHECK), longitudes
(VARCHAR), tipos apropiados (DATE, NUMERIC, JSONB) e identificadores subrogados
generados por la base (columnas IDENTITY). El acceso a datos se hace con consultas
SQL puntuales: SELECT/INSERT/UPDATE con WHERE, INSERT ... RETURNING para los ids
generados, y UPDATE real (no upsert) para modificar filas existentes.

El borrado es lógico (columna `eliminado`); las claves foráneas son normales y la
cascada lógica vive en el código (controlador/eliminacion_cascada.py).

Transacciones
-------------
Cada operación de escritura confirma por sí sola, salvo que se ejecute dentro de
`with gestor.transaccion():`, en cuyo caso todas las escrituras del bloque se
confirman juntas (o se revierten con rollback si algo falla). Esto permite que las
operaciones de negocio que tocan varias tablas (aceptar estudiante + crear
práctica, asentar nota + acreditar horas, alta de usuario + credencial, borrado en
cascada) sean atómicas.

Estructura de MAPEO
-------------------
Cada entidad declara:
    - "tabla":   nombre de la tabla.
    - "clase":   clase del modelo a reconstruir (o None si es un dict plano, como
                 'solicitud').
    - "clave":   columna usada como clave primaria.
    - "columnas": lista de (nombre, tipo_sql, restriccion_inline). La restricción
                 inline incluye PRIMARY KEY, NOT NULL, UNIQUE, GENERATED ... IDENTITY, etc.
    - "checks":  lista de expresiones CHECK a nivel de tabla.
    - "fks":     lista de (columna_local, tabla_referenciada, columna_referenciada).
    - "indices": lista de listas de columnas a indexar.

Las fechas se manejan en la aplicación como texto "dd/MM/yyyy" pero se almacenan
como DATE; la conversión está centralizada en _hacia_bd/_desde_bd. Las contraseñas
se almacenan cifradas (hash con sal); ver modelo/seguridad.py.

Al leer una fila se reconstruye el objeto del modelo con `Cls.__new__(Cls)` y se
asignan los atributos directamente: NO se ejecuta `__init__`, evitando que las
validaciones del constructor se disparen sobre datos ya almacenados (es la misma
técnica que usan los ORM para materializar entidades desde la base).
"""

import json
from contextlib import contextmanager
from datetime import date, datetime

import psycopg2
from psycopg2.extras import Json

from persistencia.config_bd import CONFIG_BD

from modelo.seguridad import hash_password, es_hash
from modelo.administrador import Administrador
from modelo.credencial import Credencial
from modelo.estudiante import Estudiante
from modelo.coordinadores import TutorAcademico, TutorEmpresarial, CoordinadorVinculacion
from modelo.proceso import Oferta, Postulacion, Practica
from modelo.formulario import Formulario1, Formulario2, Formulario3


FORMATO_FECHA = "%d/%m/%Y"

# Conjuntos de estados válidos (espejo de las máquinas de estado del modelo).
ROLES = ("administrador", "estudiante", "tutor_academico",
         "tutor_empresarial", "coordinador_vinculacion")
ESTADOS_POSTULACION = ("Pendiente", "Validada", "Enviada", "Aceptada", "Rechazada")
ESTADOS_PRACTICA = ("En progreso", "En Ejecución", "Evaluación Solicitada",
                    "Pendiente Nota", "Finalizada / Aprobada")
ESTADOS_SOLICITUD = ("Pendiente", "Aprobada", "Rechazada")
TIPOS_SOLICITUD = ("Autorización de Empresa Propia", "Emisión de Certificado/Oficio")
ESTADOS_FORM1 = ("Pendiente", "Aprobado")
# Formulario 2 y 3 solo se crean ya completados (no tienen máquina de estados).
ESTADOS_FORM2 = ("Completado",)
ESTADOS_FORM3 = ("Completado",)


def _en(valores):
    """Construye una lista 'a','b','c' para una cláusula IN de un CHECK."""
    return ", ".join("'" + v.replace("'", "''") + "'" for v in valores)


# Definición de columnas por entidad: (nombre, tipo_sql, restriccion_inline).
# El orden de las entidades respeta las dependencias de claves foráneas
# (las tablas referenciadas se crean antes que las que las referencian).
MAPEO = {
    "administrador": {
        "tabla": "administrador",
        "clase": Administrador,
        "clave": "usuario",
        "columnas": [
            ("usuario", "VARCHAR(20)", "PRIMARY KEY"),
            ("contrasena", "VARCHAR(255)", "NOT NULL"),
            ("email", "VARCHAR(120)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [],
        "fks": [],
        "indices": [],
    },
    "login": {
        "tabla": "login",
        "clase": Credencial,
        "clave": "identificador",
        "columnas": [
            ("identificador", "VARCHAR(20)", "PRIMARY KEY"),
            ("contrasena", "VARCHAR(255)", "NOT NULL"),
            ("rol", "VARCHAR(30)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        # login.identificador no lleva FK: puede apuntar a administrador,
        # estudiante, tutores o coordinador (no hay una sola tabla destino).
        "checks": [f"rol IN ({_en(ROLES)})"],
        "fks": [],
        "indices": [],
    },
    "estudiante": {
        "tabla": "estudiante",
        "clase": Estudiante,
        "clave": "cedula",
        "columnas": [
            ("cedula", "VARCHAR(10)", "PRIMARY KEY"),
            ("contrasena", "VARCHAR(255)", "NOT NULL"),
            ("apellidos", "VARCHAR(100)", "NOT NULL"),
            ("nombres", "VARCHAR(100)", "NOT NULL"),
            ("telefono", "VARCHAR(10)", "NOT NULL"),
            ("email", "VARCHAR(120)", "NOT NULL UNIQUE"),
            ("carrera", "VARCHAR(100)", "NOT NULL"),
            ("ciclo", "INTEGER", "NOT NULL"),
            ("num_practicas_realizadas", "INTEGER", "NOT NULL DEFAULT 0"),
            ("total_horas_realizadas", "INTEGER", "NOT NULL DEFAULT 0"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [
            "ciclo BETWEEN 1 AND 10",
            "num_practicas_realizadas >= 0",
            "total_horas_realizadas >= 0",
        ],
        "fks": [],
        "indices": [],
    },
    "tutor_academico": {
        "tabla": "tutor_academico",
        "clase": TutorAcademico,
        "clave": "cedula",
        "columnas": [
            ("cedula", "VARCHAR(10)", "PRIMARY KEY"),
            ("contrasena", "VARCHAR(255)", "NOT NULL"),
            ("nombres", "VARCHAR(100)", "NOT NULL"),
            ("apellidos", "VARCHAR(100)", "NOT NULL"),
            ("telefono", "VARCHAR(10)", "NOT NULL"),
            ("email", "VARCHAR(120)", "NOT NULL UNIQUE"),
            ("carrera", "VARCHAR(100)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [],
        "fks": [],
        "indices": [],
    },
    "tutor_empresarial": {
        "tabla": "tutor_empresarial",
        "clase": TutorEmpresarial,
        "clave": "cedula",
        "columnas": [
            ("cedula", "VARCHAR(10)", "PRIMARY KEY"),
            ("contrasena", "VARCHAR(255)", "NOT NULL"),
            ("nombres", "VARCHAR(100)", "NOT NULL"),
            ("apellidos", "VARCHAR(100)", "NOT NULL"),
            ("telefono", "VARCHAR(10)", "NOT NULL"),
            ("email", "VARCHAR(120)", "NOT NULL UNIQUE"),
            ("cargo", "VARCHAR(100)", "NOT NULL"),
            # ruc_empresa UNIQUE: regla "una empresa = un tutor empresarial";
            # es la columna referenciada por oferta.ruc_empresa.
            ("ruc_empresa", "VARCHAR(13)", "NOT NULL UNIQUE"),
            ("nombre_empresa", "VARCHAR(150)", "NOT NULL"),
            ("direccion_empresa", "VARCHAR(255)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [],
        "fks": [],
        "indices": [],
    },
    "coordinador_vinculacion": {
        "tabla": "coordinador_vinculacion",
        "clase": CoordinadorVinculacion,
        "clave": "cedula",
        "columnas": [
            ("cedula", "VARCHAR(10)", "PRIMARY KEY"),
            ("contrasena", "VARCHAR(255)", "NOT NULL"),
            ("nombres", "VARCHAR(100)", "NOT NULL"),
            ("apellidos", "VARCHAR(100)", "NOT NULL"),
            ("telefono", "VARCHAR(10)", "NOT NULL"),
            ("email", "VARCHAR(120)", "NOT NULL UNIQUE"),
            ("fecha_nacimiento", "DATE", "NOT NULL"),
            ("direccion", "VARCHAR(255)", "NOT NULL"),
            ("carrera", "VARCHAR(100)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [],
        "fks": [],
        "indices": [],
    },
    "oferta": {
        "tabla": "oferta",
        "clase": Oferta,
        "clave": "id_oferta",
        "columnas": [
            ("id_oferta", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("descripcion", "TEXT", "NOT NULL"),
            ("puesto", "VARCHAR(100)", "NOT NULL"),
            ("fecha_publicacion", "DATE", ""),
            ("ruc_empresa", "VARCHAR(13)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [],
        "fks": [("ruc_empresa", "tutor_empresarial", "ruc_empresa")],
        "indices": [["ruc_empresa"]],
    },
    "postulacion": {
        "tabla": "postulacion",
        "clase": Postulacion,
        "clave": "id_postulacion",
        "columnas": [
            ("id_postulacion", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("fecha", "DATE", ""),
            ("estado_validacion", "VARCHAR(20)", "NOT NULL"),
            ("cedula_estudiante", "VARCHAR(10)", "NOT NULL"),
            ("id_oferta", "INTEGER", "NOT NULL"),
            ("id_coordinador", "VARCHAR(10)", ""),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [f"estado_validacion IN ({_en(ESTADOS_POSTULACION)})"],
        "fks": [
            ("cedula_estudiante", "estudiante", "cedula"),
            ("id_oferta", "oferta", "id_oferta"),
            ("id_coordinador", "coordinador_vinculacion", "cedula"),
        ],
        "indices": [["cedula_estudiante"], ["id_oferta"], ["estado_validacion"]],
    },
    "practica": {
        "tabla": "practica",
        "clase": Practica,
        "clave": "id_practica",
        "columnas": [
            ("id_practica", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("fecha_inicio", "DATE", ""),
            ("fecha_fin", "DATE", ""),
            ("estado", "VARCHAR(30)", "NOT NULL"),
            ("id_postulacion", "INTEGER", "NOT NULL"),
            ("id_tutor_academico", "VARCHAR(10)", ""),
            ("id_tutor_empresarial", "VARCHAR(10)", ""),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [f"estado IN ({_en(ESTADOS_PRACTICA)})"],
        "fks": [
            ("id_postulacion", "postulacion", "id_postulacion"),
            ("id_tutor_academico", "tutor_academico", "cedula"),
            ("id_tutor_empresarial", "tutor_empresarial", "cedula"),
        ],
        "indices": [["id_postulacion"]],
    },
    "solicitud": {
        "tabla": "solicitud",
        "clase": None,  # dict plano
        "clave": "id",
        "columnas": [
            ("id", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("tipo", "VARCHAR(60)", "NOT NULL"),
            ("motivo", "TEXT", "NOT NULL"),
            ("estado", "VARCHAR(20)", "NOT NULL"),
            ("cedula_estudiante", "VARCHAR(10)", "NOT NULL"),
            ("fecha", "DATE", ""),
            ("datos_empresa", "JSONB", ""),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [
            f"estado IN ({_en(ESTADOS_SOLICITUD)})",
            f"tipo IN ({_en(TIPOS_SOLICITUD)})",
        ],
        "fks": [("cedula_estudiante", "estudiante", "cedula")],
        "indices": [["cedula_estudiante"]],
    },
    "formulario1": {
        "tabla": "formulario1",
        "clase": Formulario1,
        "clave": "id_formulario1",
        "columnas": [
            ("id_formulario1", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("id_practica", "INTEGER", "NOT NULL"),
            ("tipo_documento", "VARCHAR(40)", "NOT NULL"),
            ("numero_documento", "VARCHAR(50)", "NOT NULL"),
            ("tipo_practica", "VARCHAR(30)", "NOT NULL"),
            ("remuneracion", "NUMERIC(10,2)", "NOT NULL"),
            ("fecha_inicial", "DATE", ""),
            ("fecha_final_aprox", "DATE", ""),
            ("horas_aprox", "INTEGER", "NOT NULL"),
            ("actividades", "JSONB", "NOT NULL"),
            ("estado_aprobacion", "VARCHAR(20)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [
            f"estado_aprobacion IN ({_en(ESTADOS_FORM1)})",
            "remuneracion >= 0",
            "horas_aprox > 0",
        ],
        "fks": [("id_practica", "practica", "id_practica")],
        "indices": [["id_practica"]],
    },
    "formulario2": {
        "tabla": "formulario2",
        "clase": Formulario2,
        "clave": "id_formulario2",
        "columnas": [
            ("id_formulario2", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("id_practica", "INTEGER", "NOT NULL"),
            ("fecha_real_inicio", "DATE", ""),
            ("fecha_real_fin", "DATE", ""),
            ("horas_cumplidas", "INTEGER", "NOT NULL"),
            ("calificaciones_rubrica", "JSONB", "NOT NULL"),
            ("productos_relevantes", "TEXT", "NOT NULL"),
            ("aspectos_relevantes", "TEXT", "NOT NULL"),
            ("estado", "VARCHAR(20)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [
            "horas_cumplidas > 0",
            f"estado IN ({_en(ESTADOS_FORM2)})",
        ],
        "fks": [("id_practica", "practica", "id_practica")],
        "indices": [["id_practica"]],
    },
    "formulario3": {
        "tabla": "formulario3",
        "clase": Formulario3,
        "clave": "id_formulario3",
        "columnas": [
            ("id_formulario3", "INTEGER", "GENERATED ALWAYS AS IDENTITY PRIMARY KEY"),
            ("id_practica", "INTEGER", "NOT NULL"),
            ("campo_ocupacional", "VARCHAR(150)", "NOT NULL"),
            ("calificacion_sobre_100", "NUMERIC(5,2)", "NOT NULL"),
            ("evaluacion_escenario", "JSONB", "NOT NULL"),
            ("estado", "VARCHAR(20)", "NOT NULL"),
            ("eliminado", "BOOLEAN", "NOT NULL DEFAULT FALSE"),
        ],
        "checks": [
            "calificacion_sobre_100 BETWEEN 0 AND 100",
            f"estado IN ({_en(ESTADOS_FORM3)})",
        ],
        "fks": [("id_practica", "practica", "id_practica")],
        "indices": [["id_practica"]],
    },
}


class GestorPersistencia:

    def __init__(self):
        self.schema = CONFIG_BD.get("schema", "public")
        self._en_transaccion = False
        self.conexion = psycopg2.connect(
            host=CONFIG_BD["host"],
            port=CONFIG_BD["port"],
            dbname=CONFIG_BD["dbname"],
            user=CONFIG_BD["user"],
            password=CONFIG_BD["password"],
            # Forzamos UTF-8 para que los mensajes de error de PostgreSQL
            # (cluster con lc_messages en español) lleguen decodificables.
            client_encoding="UTF8",
        )
        self._asegurar_esquema()

    # ------------------------------------------------------------------ #
    # Utilidades internas
    # ------------------------------------------------------------------ #
    def _tabla(self, nombre):
        return f'"{self.schema}".{nombre}'

    @staticmethod
    def _columnas(mapa):
        return [col for (col, _tipo, _restr) in mapa["columnas"]]

    @staticmethod
    def _es_identidad(restr):
        """True si la columna la genera la base de datos (IDENTITY)."""
        return "IDENTITY" in (restr or "").upper()

    @staticmethod
    def _columna_identidad(mapa):
        """Nombre de la columna IDENTITY de la entidad, o None si no tiene."""
        for (col, _tipo, restr) in mapa["columnas"]:
            if GestorPersistencia._es_identidad(restr):
                return col
        return None

    @staticmethod
    def _columnas_persistibles(mapa):
        """Columnas que escribe la aplicación (excluye las generadas por la base,
        como los ids IDENTITY)."""
        return [(c, t, r) for (c, t, r) in mapa["columnas"]
                if not GestorPersistencia._es_identidad(r)]

    def _asegurar_esquema(self):
        """Crea el esquema, las tablas (con restricciones) y los índices si aún
        no existen (idempotente)."""
        with self.conexion.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
            cur.execute(f'SET search_path TO "{self.schema}"')
            for mapa in MAPEO.values():
                definiciones = []
                for (col, tipo, restr) in mapa["columnas"]:
                    linea = f"{col} {tipo}"
                    if restr:
                        linea += f" {restr}"
                    definiciones.append(linea)
                for check in mapa.get("checks", []):
                    definiciones.append(f"CHECK ({check})")
                for (col_local, tabla_ref, col_ref) in mapa.get("fks", []):
                    definiciones.append(
                        f'CONSTRAINT fk_{mapa["tabla"]}_{col_local} '
                        f'FOREIGN KEY ({col_local}) '
                        f'REFERENCES {self._tabla(tabla_ref)}({col_ref})'
                    )
                cur.execute(
                    f'CREATE TABLE IF NOT EXISTS {self._tabla(mapa["tabla"])} '
                    f'({", ".join(definiciones)})'
                )
                for cols in mapa.get("indices", []):
                    nombre = f'idx_{mapa["tabla"]}_{"_".join(cols)}'
                    cur.execute(
                        f'CREATE INDEX IF NOT EXISTS {nombre} '
                        f'ON {self._tabla(mapa["tabla"])} ({", ".join(cols)})'
                    )
            self._asegurar_vistas(cur)
        self.conexion.commit()

    def _asegurar_vistas(self, cur):
        """Crea (o reemplaza) las vistas SQL que cruzan tablas para los listados
        de la interfaz. Concentran los JOIN en la base de datos."""
        s = f'"{self.schema}"'
        # Postulación + estudiante + oferta + empresa
        cur.execute(f'''
            CREATE OR REPLACE VIEW {s}.vista_postulacion_detalle AS
            SELECT p.id_postulacion, p.estado_validacion, p.fecha, p.eliminado,
                   p.cedula_estudiante,
                   e.nombres  AS est_nombres,  e.apellidos AS est_apellidos,
                   e.ciclo    AS est_ciclo,    e.num_practicas_realizadas AS est_num_practicas,
                   e.carrera  AS est_carrera,
                   p.id_oferta, o.puesto AS oferta_puesto, o.descripcion AS oferta_descripcion,
                   o.ruc_empresa, te.nombre_empresa
            FROM {s}.postulacion p
            JOIN {s}.estudiante e        ON p.cedula_estudiante = e.cedula
            JOIN {s}.oferta o            ON p.id_oferta = o.id_oferta
            JOIN {s}.tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa
        ''')
        # Práctica + estudiante + tutores
        cur.execute(f'''
            CREATE OR REPLACE VIEW {s}.vista_practica_detalle AS
            SELECT pr.id_practica, pr.estado, pr.fecha_inicio, pr.fecha_fin, pr.eliminado,
                   pr.id_postulacion, pr.id_tutor_academico, pr.id_tutor_empresarial,
                   e.cedula AS est_cedula, e.nombres AS est_nombres, e.apellidos AS est_apellidos,
                   e.carrera AS est_carrera,
                   ta.nombres AS acad_nombres, ta.apellidos AS acad_apellidos,
                   te.nombres AS emp_nombres,  te.apellidos AS emp_apellidos, te.nombre_empresa
            FROM {s}.practica pr
            JOIN {s}.postulacion p        ON pr.id_postulacion = p.id_postulacion
            JOIN {s}.estudiante e         ON p.cedula_estudiante = e.cedula
            LEFT JOIN {s}.tutor_academico ta    ON pr.id_tutor_academico = ta.cedula
            LEFT JOIN {s}.tutor_empresarial te  ON pr.id_tutor_empresarial = te.cedula
        ''')
        # Oferta + empresa
        cur.execute(f'''
            CREATE OR REPLACE VIEW {s}.vista_oferta_detalle AS
            SELECT o.id_oferta, o.puesto, o.descripcion, o.fecha_publicacion, o.eliminado,
                   o.ruc_empresa, te.nombre_empresa
            FROM {s}.oferta o
            JOIN {s}.tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa
        ''')

    @staticmethod
    def _leer_atributo(objeto, columna):
        if isinstance(objeto, dict):
            return objeto.get(columna)
        return getattr(objeto, columna, None)

    @staticmethod
    def _hacia_bd(valor, tipo):
        if tipo == "JSONB":
            return Json(valor) if valor is not None else None
        if tipo == "DATE":
            if valor is None or valor == "":
                return None
            if isinstance(valor, str):
                return datetime.strptime(valor, FORMATO_FECHA).date()
            return valor
        return valor

    @staticmethod
    def _desde_bd(valor, tipo):
        if tipo == "JSONB" and isinstance(valor, str):
            return json.loads(valor)
        if tipo == "DATE":
            if valor is None:
                return None
            if isinstance(valor, (date, datetime)):
                return valor.strftime(FORMATO_FECHA)
            return valor
        return valor

    @staticmethod
    def _reconstruir(mapa, fila):
        """Reconstruye el objeto (o dict) a partir de una fila {columna: valor}.
        Usa Cls.__new__ para no ejecutar __init__ ni revalidar datos ya guardados
        (misma técnica que usan los ORM para materializar entidades)."""
        clase = mapa["clase"]
        if clase is None:
            return {col: GestorPersistencia._desde_bd(fila[col], tipo)
                    for (col, tipo, _restr) in mapa["columnas"]}
        objeto = clase.__new__(clase)
        for (col, tipo, _restr) in mapa["columnas"]:
            setattr(objeto, col, GestorPersistencia._desde_bd(fila[col], tipo))
        return objeto

    @staticmethod
    def _asignar(objeto, columna, valor):
        if isinstance(objeto, dict):
            objeto[columna] = valor
        else:
            setattr(objeto, columna, valor)

    def _valor_bd(self, col, tipo, valor_objeto):
        """Convierte el valor de un atributo a su representación en la base.
        Las contraseñas se cifran (hash con sal) si aún no lo están."""
        valor = self._hacia_bd(valor_objeto, tipo)
        if col == "contrasena" and isinstance(valor, str) and valor and not es_hash(valor):
            valor = hash_password(valor)
        return valor

    def _valores(self, mapa, objeto, columnas):
        """Tupla de valores (convertidos a BD) para la lista de columnas dada."""
        return tuple(
            self._valor_bd(col, tipo, self._leer_atributo(objeto, col))
            for (col, tipo, _restr) in columnas
        )

    def _rollback_seguro(self):
        try:
            self.conexion.rollback()
        except Exception:
            pass

    def _commit_si_corresponde(self):
        """Confirma solo si no estamos dentro de un bloque transaccion()."""
        if not self._en_transaccion:
            self.conexion.commit()

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
                self.conexion.commit()
        except Exception:
            self._rollback_seguro()
            raise
        finally:
            self._en_transaccion = anterior

    # ------------------------------------------------------------------ #
    # Interfaz SQL puntual (usada por los repositorios)
    # ------------------------------------------------------------------ #
    def obtener(self, entidad, clave):
        """Devuelve el objeto/dict con esa clave primaria, o None (incluye los
        marcados como eliminados; el filtrado por 'eliminado' lo decide quien
        llama, igual que antes)."""
        mapa = MAPEO[entidad]
        columnas = self._columnas(mapa)
        with self.conexion.cursor() as cur:
            cur.execute(
                f'SELECT {", ".join(columnas)} FROM {self._tabla(mapa["tabla"])} '
                f'WHERE {mapa["clave"]} = %s',
                (clave,))
            tupla = cur.fetchone()
        if tupla is None:
            return None
        return self._reconstruir(mapa, dict(zip(columnas, tupla)))

    def existe(self, entidad, clave):
        """True si la clave primaria existe físicamente (incluye eliminados)."""
        mapa = MAPEO[entidad]
        with self.conexion.cursor() as cur:
            cur.execute(
                f'SELECT 1 FROM {self._tabla(mapa["tabla"])} '
                f'WHERE {mapa["clave"]} = %s',
                (clave,))
            return cur.fetchone() is not None

    def listar(self, entidad, where=None, params=(), incluir_eliminados=False, orden=None):
        """Lista objetos/dicts de la entidad. Por defecto excluye los eliminados.
        `where` es una cláusula SQL adicional con marcadores %s y `params` sus
        valores."""
        mapa = MAPEO[entidad]
        columnas = self._columnas(mapa)
        clausulas = []
        if not incluir_eliminados:
            clausulas.append("eliminado = FALSE")
        if where:
            clausulas.append(where)
        sql = f'SELECT {", ".join(columnas)} FROM {self._tabla(mapa["tabla"])}'
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        if orden:
            sql += f" ORDER BY {orden}"
        with self.conexion.cursor() as cur:
            cur.execute(sql, tuple(params))
            filas = cur.fetchall()
        return [self._reconstruir(mapa, dict(zip(columnas, f))) for f in filas]

    def insertar(self, entidad, objeto):
        """INSERT de una sola fila (alta). Si la tabla tiene id generado por la
        base (IDENTITY), se omite esa columna, se recupera el id con RETURNING y
        se asigna de vuelta al objeto."""
        mapa = MAPEO[entidad]
        persistibles = self._columnas_persistibles(mapa)
        nombres = [c for (c, _t, _r) in persistibles]
        marcadores = ", ".join(["%s"] * len(nombres))
        id_generado = self._columna_identidad(mapa)
        sql = (f'INSERT INTO {self._tabla(mapa["tabla"])} ({", ".join(nombres)}) '
               f'VALUES ({marcadores})')
        if id_generado:
            sql += f' RETURNING {id_generado}'
        try:
            with self.conexion.cursor() as cur:
                cur.execute(sql, self._valores(mapa, objeto, persistibles))
                if id_generado:
                    self._asignar(objeto, id_generado, cur.fetchone()[0])
            self._commit_si_corresponde()
        except Exception:
            self._rollback_seguro()
            raise

    def actualizar(self, entidad, objeto):
        """UPDATE real de una fila existente, identificada por su clave primaria.
        Modifica todas las columnas escribibles (no la PK ni las generadas)."""
        mapa = MAPEO[entidad]
        clave = mapa["clave"]
        columnas_set = [(c, t, r) for (c, t, r) in self._columnas_persistibles(mapa)
                        if c != clave]
        asignaciones = ", ".join(f"{c} = %s" for (c, _t, _r) in columnas_set)
        sql = (f'UPDATE {self._tabla(mapa["tabla"])} SET {asignaciones} '
               f'WHERE {clave} = %s')
        valores = self._valores(mapa, objeto, columnas_set) + (self._leer_atributo(objeto, clave),)
        try:
            with self.conexion.cursor() as cur:
                cur.execute(sql, valores)
            self._commit_si_corresponde()
        except Exception:
            self._rollback_seguro()
            raise

    def marcar_eliminado(self, entidad, clave):
        """Eliminación lógica: marca la fila como eliminada."""
        mapa = MAPEO[entidad]
        sql = (f'UPDATE {self._tabla(mapa["tabla"])} SET eliminado = TRUE '
               f'WHERE {mapa["clave"]} = %s')
        try:
            with self.conexion.cursor() as cur:
                cur.execute(sql, (clave,))
            self._commit_si_corresponde()
        except Exception:
            self._rollback_seguro()
            raise

    def marcar_eliminados(self, entidad, claves):
        """Eliminación lógica en lote por clave primaria (para la cascada)."""
        self.marcar_eliminados_por(entidad, MAPEO[entidad]["clave"], claves)

    def marcar_eliminados_por(self, entidad, columna, valores):
        """Eliminación lógica en lote filtrando por una columna cualquiera
        (p. ej. todos los formularios de un conjunto de prácticas). Dentro de un
        bloque transaccion() varias de estas marcas se confirman atómicamente."""
        valores = list(valores)
        if not valores:
            return
        mapa = MAPEO[entidad]
        sql = (f'UPDATE {self._tabla(mapa["tabla"])} SET eliminado = TRUE '
               f'WHERE {columna} = ANY(%s)')
        try:
            with self.conexion.cursor() as cur:
                cur.execute(sql, (valores,))
            self._commit_si_corresponde()
        except Exception:
            self._rollback_seguro()
            raise

    def consultar(self, sql, params=()):
        """Ejecuta una consulta SQL libre (p. ej. con JOIN) y devuelve una lista
        de dicts {columna: valor}. Las columnas DATE se devuelven formateadas a
        'dd/MM/yyyy' para mostrarse directamente en la interfaz."""
        try:
            with self.conexion.cursor() as cur:
                cur.execute(sql, tuple(params))
                nombres = [d[0] for d in cur.description]
                filas = cur.fetchall()
        except Exception:
            self._rollback_seguro()
            raise
        resultado = []
        for fila in filas:
            registro = {}
            for nombre, valor in zip(nombres, fila):
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
        """Inserta/actualiza en lote un diccionario {clave: objeto}, de forma
        idempotente (ON CONFLICT DO UPDATE). Lo usa únicamente el sembrado de
        datos de ejemplo del primer arranque, y solo para entidades con clave
        natural (sin id generado)."""
        mapa = MAPEO[entidad]
        columnas = mapa["columnas"]
        nombres = [c for (c, _t, _r) in columnas]
        marcadores = ", ".join(["%s"] * len(nombres))
        asignaciones = ", ".join(
            f"{col} = EXCLUDED.{col}" for col in nombres if col != mapa["clave"])
        sql = (
            f'INSERT INTO {self._tabla(mapa["tabla"])} ({", ".join(nombres)}) '
            f'VALUES ({marcadores}) '
            f'ON CONFLICT ({mapa["clave"]}) DO UPDATE SET {asignaciones}'
        )
        filas = [self._valores(mapa, objeto, columnas)
                 for objeto in diccionario_datos.values()]
        try:
            with self.conexion.cursor() as cur:
                if filas:
                    cur.executemany(sql, filas)
            self._commit_si_corresponde()
        except Exception:
            self._rollback_seguro()
            raise

    def _contar(self, entidad):
        mapa = MAPEO[entidad]
        with self.conexion.cursor() as cur:
            cur.execute(f'SELECT COUNT(*) FROM {self._tabla(mapa["tabla"])}')
            return cur.fetchone()[0]

    # ------------------------------------------------------------------ #
    # Inicialización de datos
    # ------------------------------------------------------------------ #
    @staticmethod
    def inicializar_datos_si_vacio():
        """Crea esquema/tablas y, si no hay credenciales, siembra el admin y
        un conjunto de datos de ejemplo para poder probar la aplicación."""
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
        """Instancia una clase del modelo sin pasar por sus validaciones."""
        objeto = clase.__new__(clase)
        for nombre, valor in atributos.items():
            setattr(objeto, nombre, valor)
        return objeto

    def _sembrar_datos_ejemplo(self):
        """Inserta datos de ejemplo (adaptados del .sql de referencia) ajustados
        a la estructura del modelo Python. Se evita la validación del
        constructor usando _crear, para que las cédulas/datos de muestra no
        provoquen errores. Cada usuario recibe su credencial de acceso."""
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
