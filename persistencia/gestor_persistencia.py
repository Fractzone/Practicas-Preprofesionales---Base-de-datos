"""
Gestor de persistencia respaldado por PostgreSQL.

Esta versión reemplaza el almacenamiento con pickle por una base de datos
PostgreSQL, pero mantiene EXACTAMENTE la misma interfaz pública que usaba el
resto del proyecto:

    - cargar(entidad)            -> dict {clave_natural: objeto_del_modelo}
    - guardar(entidad, dict)     -> persiste todo el diccionario
    - inicializar_datos_si_vacio()

Gracias a esto, modelo/, controlador/ y vista/ no requieren ningún cambio:
siguen cargando el diccionario completo, mutándolo en memoria y guardándolo.

El mapeo objeto <-> tabla se define en MAPEO. Cada entidad declara su tabla,
la clase del modelo a reconstruir (o None si es un dict plano, como 'solicitud'),
el atributo usado como clave del diccionario y sus columnas con el tipo SQL.

Para reconstruir los objetos al leer de la BD se usa `Cls.__new__(Cls)` y se
asignan los atributos directamente, igual que hacía pickle: NO se vuelve a
ejecutar `__init__`, evitando que las validaciones del constructor fallen con
datos ya almacenados.
"""

import json

import psycopg2
from psycopg2.extras import Json

from persistencia.config_bd import CONFIG_BD

from modelo.administrador import Administrador
from modelo.credencial import Credencial
from modelo.estudiante import Estudiante
from modelo.coordinadores import TutorAcademico, TutorEmpresarial, CoordinadorVinculacion
from modelo.proceso import Oferta, Postulacion, Practica
from modelo.formulario import Formulario1, Formulario2, Formulario3


# Definición de columnas por entidad: (nombre_columna, tipo_sql).
# La primera columna de cada lista es siempre la clave primaria (= 'clave').
MAPEO = {
    "administrador": {
        "tabla": "administrador",
        "clase": Administrador,
        "clave": "usuario",
        "columnas": [
            ("usuario", "TEXT"),
            ("contrasena", "TEXT"),
            ("email", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "login": {
        "tabla": "login",
        "clase": Credencial,
        "clave": "identificador",
        "columnas": [
            ("identificador", "TEXT"),
            ("contrasena", "TEXT"),
            ("rol", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "estudiante": {
        "tabla": "estudiante",
        "clase": Estudiante,
        "clave": "cedula",
        "columnas": [
            ("cedula", "TEXT"),
            ("contrasena", "TEXT"),
            ("apellidos", "TEXT"),
            ("nombres", "TEXT"),
            ("telefono", "TEXT"),
            ("email", "TEXT"),
            ("carrera", "TEXT"),
            ("ciclo", "INTEGER"),
            ("num_practicas_realizadas", "INTEGER"),
            ("total_horas_realizadas", "INTEGER"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "tutor_academico": {
        "tabla": "tutor_academico",
        "clase": TutorAcademico,
        "clave": "cedula",
        "columnas": [
            ("cedula", "TEXT"),
            ("contrasena", "TEXT"),
            ("nombres", "TEXT"),
            ("apellidos", "TEXT"),
            ("telefono", "TEXT"),
            ("email", "TEXT"),
            ("carrera", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "tutor_empresarial": {
        "tabla": "tutor_empresarial",
        "clase": TutorEmpresarial,
        "clave": "cedula",
        "columnas": [
            ("cedula", "TEXT"),
            ("contrasena", "TEXT"),
            ("nombres", "TEXT"),
            ("apellidos", "TEXT"),
            ("telefono", "TEXT"),
            ("email", "TEXT"),
            ("cargo", "TEXT"),
            ("ruc_empresa", "TEXT"),
            ("nombre_empresa", "TEXT"),
            ("direccion_empresa", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "coordinador_vinculacion": {
        "tabla": "coordinador_vinculacion",
        "clase": CoordinadorVinculacion,
        "clave": "cedula",
        "columnas": [
            ("cedula", "TEXT"),
            ("contrasena", "TEXT"),
            ("nombres", "TEXT"),
            ("apellidos", "TEXT"),
            ("telefono", "TEXT"),
            ("email", "TEXT"),
            ("fecha_nacimiento", "TEXT"),
            ("direccion", "TEXT"),
            ("carrera", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "oferta": {
        "tabla": "oferta",
        "clase": Oferta,
        "clave": "id_oferta",
        "columnas": [
            ("id_oferta", "TEXT"),
            ("descripcion", "TEXT"),
            ("puesto", "TEXT"),
            ("fecha_publicacion", "TEXT"),
            ("ruc_empresa", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "postulacion": {
        "tabla": "postulacion",
        "clase": Postulacion,
        "clave": "id_postulacion",
        "columnas": [
            ("id_postulacion", "TEXT"),
            ("fecha", "TEXT"),
            ("estado_validacion", "TEXT"),
            ("cedula_estudiante", "TEXT"),
            ("id_oferta", "TEXT"),
            ("id_coordinador", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "practica": {
        "tabla": "practica",
        "clase": Practica,
        "clave": "id_practica",
        "columnas": [
            ("id_practica", "TEXT"),
            ("fecha_inicio", "TEXT"),
            ("fecha_fin", "TEXT"),
            ("estado", "TEXT"),
            ("id_postulacion", "TEXT"),
            ("id_tutor_academico", "TEXT"),
            ("id_tutor_empresarial", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "solicitud": {
        "tabla": "solicitud",
        "clase": None,  # dict plano
        "clave": "id",
        "columnas": [
            ("id", "TEXT"),
            ("tipo", "TEXT"),
            ("motivo", "TEXT"),
            ("estado", "TEXT"),
            ("cedula_estudiante", "TEXT"),
            ("fecha", "TEXT"),
            ("datos_empresa", "JSONB"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "formulario1": {
        "tabla": "formulario1",
        "clase": Formulario1,
        "clave": "id_formulario1",
        "columnas": [
            ("id_formulario1", "TEXT"),
            ("id_practica", "TEXT"),
            ("tipo_documento", "TEXT"),
            ("numero_documento", "TEXT"),
            ("tipo_practica", "TEXT"),
            ("remuneracion", "DOUBLE PRECISION"),
            ("fecha_inicial", "TEXT"),
            ("fecha_final_aprox", "TEXT"),
            ("horas_aprox", "INTEGER"),
            ("actividades", "JSONB"),
            ("estado_aprobacion", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "formulario2": {
        "tabla": "formulario2",
        "clase": Formulario2,
        "clave": "id_formulario2",
        "columnas": [
            ("id_formulario2", "TEXT"),
            ("id_practica", "TEXT"),
            ("fecha_real_inicio", "TEXT"),
            ("fecha_real_fin", "TEXT"),
            ("horas_cumplidas", "INTEGER"),
            ("calificaciones_rubrica", "JSONB"),
            ("productos_relevantes", "TEXT"),
            ("aspectos_relevantes", "TEXT"),
            ("estado", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
    "formulario3": {
        "tabla": "formulario3",
        "clase": Formulario3,
        "clave": "id_formulario3",
        "columnas": [
            ("id_formulario3", "TEXT"),
            ("id_practica", "TEXT"),
            ("campo_ocupacional", "TEXT"),
            ("calificacion_sobre_100", "DOUBLE PRECISION"),
            ("evaluacion_escenario", "JSONB"),
            ("estado", "TEXT"),
            ("eliminado", "BOOLEAN"),
        ],
    },
}


class GestorPersistencia:

    def __init__(self):
        self.schema = CONFIG_BD.get("schema", "public")
        self.conexion = psycopg2.connect(
            host=CONFIG_BD["host"],
            port=CONFIG_BD["port"],
            dbname=CONFIG_BD["dbname"],
            user=CONFIG_BD["user"],
            password=CONFIG_BD["password"],
        )
        self._asegurar_esquema()

    # ------------------------------------------------------------------ #
    # Utilidades internas
    # ------------------------------------------------------------------ #
    def _tabla(self, nombre):
        return f'"{self.schema}".{nombre}'

    def _asegurar_esquema(self):
        """Crea el esquema y todas las tablas si aún no existen (idempotente)."""
        with self.conexion.cursor() as cur:
            cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"')
            cur.execute(f'SET search_path TO "{self.schema}"')
            for mapa in MAPEO.values():
                definiciones = []
                for indice, (col, tipo) in enumerate(mapa["columnas"]):
                    if indice == 0:
                        definiciones.append(f"{col} {tipo} PRIMARY KEY")
                    else:
                        definiciones.append(f"{col} {tipo}")
                cur.execute(
                    f'CREATE TABLE IF NOT EXISTS {self._tabla(mapa["tabla"])} '
                    f'({", ".join(definiciones)})'
                )
        self.conexion.commit()

    @staticmethod
    def _leer_atributo(objeto, columna):
        if isinstance(objeto, dict):
            return objeto.get(columna)
        return getattr(objeto, columna, None)

    @staticmethod
    def _hacia_bd(valor, tipo):
        if tipo == "JSONB":
            return Json(valor) if valor is not None else None
        return valor

    @staticmethod
    def _desde_bd(valor, tipo):
        if tipo == "JSONB" and isinstance(valor, str):
            return json.loads(valor)
        return valor

    @staticmethod
    def _reconstruir(mapa, fila):
        """Reconstruye el objeto (o dict) a partir de una fila {columna: valor}."""
        clase = mapa["clase"]
        if clase is None:
            return {col: GestorPersistencia._desde_bd(fila[col], tipo)
                    for (col, tipo) in mapa["columnas"]}
        objeto = clase.__new__(clase)  # sin invocar __init__, igual que pickle
        for (col, tipo) in mapa["columnas"]:
            setattr(objeto, col, GestorPersistencia._desde_bd(fila[col], tipo))
        return objeto

    # ------------------------------------------------------------------ #
    # Interfaz pública (idéntica a la versión con pickle)
    # ------------------------------------------------------------------ #
    def cargar(self, entidad):
        mapa = MAPEO[entidad]
        columnas = [col for (col, _) in mapa["columnas"]]
        resultado = {}
        with self.conexion.cursor() as cur:
            cur.execute(f'SELECT {", ".join(columnas)} FROM {self._tabla(mapa["tabla"])}')
            for tupla in cur.fetchall():
                fila = dict(zip(columnas, tupla))
                objeto = self._reconstruir(mapa, fila)
                resultado[fila[mapa["clave"]]] = objeto
        return resultado

    def guardar(self, entidad, diccionario_datos):
        mapa = MAPEO[entidad]
        columnas = [col for (col, _) in mapa["columnas"]]
        marcadores = ", ".join(["%s"] * len(columnas))
        asignaciones = ", ".join(
            f"{col} = EXCLUDED.{col}" for col in columnas if col != mapa["clave"])
        sql = (
            f'INSERT INTO {self._tabla(mapa["tabla"])} ({", ".join(columnas)}) '
            f'VALUES ({marcadores}) '
            f'ON CONFLICT ({mapa["clave"]}) DO UPDATE SET {asignaciones}'
        )
        filas = [
            tuple(self._hacia_bd(self._leer_atributo(objeto, col), tipo)
                  for (col, tipo) in mapa["columnas"])
            for objeto in diccionario_datos.values()
        ]
        with self.conexion.cursor() as cur:
            if filas:
                cur.executemany(sql, filas)
        self.conexion.commit()

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

        administrador = Administrador("admin", "admin", "admin@uce.edu.ec")
        gestor.guardar("administrador", {administrador.usuario: administrador})
        gestor.guardar("login", {
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
        self.guardar("estudiante", estudiantes)

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
        self.guardar("tutor_academico", tutores_academicos)

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
        self.guardar("tutor_empresarial", tutores_empresariales)

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
        self.guardar("coordinador_vinculacion", coordinadores)

        # --- Ofertas ---
        ofertas = {
            "1": self._crear(Oferta, {
                "id_oferta": "1", "descripcion": "Desarrollo de API REST",
                "puesto": "Pasante Backend", "fecha_publicacion": "01/03/2026",
                "ruc_empresa": "0101010106001", "eliminado": False}),
            "2": self._crear(Oferta, {
                "id_oferta": "2", "descripcion": "Creación de interfaces web",
                "puesto": "Pasante Frontend", "fecha_publicacion": "02/10/2026",
                "ruc_empresa": "0920202025001", "eliminado": False}),
        }
        self.guardar("oferta", ofertas)

        # --- Postulaciones (pendientes de validación) ---
        postulaciones = {
            "1": self._crear(Postulacion, {
                "id_postulacion": "1", "fecha": "04/03/2026",
                "estado_validacion": "Pendiente", "cedula_estudiante": "1032222224",
                "id_oferta": "1", "id_coordinador": None, "eliminado": False}),
            "2": self._crear(Postulacion, {
                "id_postulacion": "2", "fecha": "11/10/2026",
                "estado_validacion": "Pendiente", "cedula_estudiante": "2451212126",
                "id_oferta": "2", "id_coordinador": None, "eliminado": False}),
        }
        self.guardar("postulacion", postulaciones)

        # --- Credenciales de acceso de todos los usuarios sembrados ---
        self.guardar("login", credenciales)
