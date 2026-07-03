from contextlib import contextmanager
from datetime import date, datetime
from sqlalchemy import (create_engine, select, insert, update, text, func, literal,)
from sqlalchemy.engine import URL
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import sessionmaker
from persistencia.config_bd import CONFIG_BD
from persistencia.datos_persistencia import (FORMATO_FECHA, _SCHEMA, metadata, ENTIDADES, _ddl_vistas, sembrar_datos_ejemplo,)
from modelo.administrador import Administrador
from modelo.credencial import Credencial

"""
Se usa psycopg2 para conectar PostgresSQL con python
"""

#Crea la plantilla para conexion con el postgresSQL
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
        #Aqui crea la secion usando la plantilla de conexion antes creada
        self._session = _Session()
        self._asegurar_esquema()

    @staticmethod
    def _entidad(entidad):
        return ENTIDADES[entidad]

    #Leer atributo de una clase
    @staticmethod
    def _leer_atributo(objeto, columna):
        if isinstance(objeto, dict):
            return objeto.get(columna)
        # Este validacion se hace para la entidad solicitud que es la que se manjera como diccionario en vez de clase
        return getattr(objeto, columna, None)

    #Guaradr atributo en una clase
    @staticmethod
    def _asignar(objeto, columna, valor):
        if isinstance(objeto, dict):
            objeto[columna] = valor
        else:
            setattr(objeto, columna, valor)

    """
    Reconstruye la consulta en psycopg2 y lo pasa a SQLAlquemist
    persistencia.listar("oferta", where="ruc_empresa = %s AND puesto = %s", params=("0101010106001", "Pasante Backend"))
    ["ruc_empresa = ", ":_p0", " AND puesto = ", ":_p1", ""]
    """
    @staticmethod
    def _bindize(sql, params):
        partes = sql.split("%s")
        if len(partes) == 1:
            return sql, {}
        binds = {} #Formato solcitado de sqlalquemist
        salida = [partes[0]]
        for i, parte in enumerate(partes[1:]):
            nombre = f"_p{i}"
            binds[nombre] = params[i]
            salida.append(f":{nombre}")
            salida.append(parte)
        return "".join(salida), binds

    #Formate las condicones con AND
    def _condicion(self, where, params, incluir_eliminados):
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

    #Inicializacion del programa si no existen cosas
    def _asegurar_esquema(self):
        with _engine.begin() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{self.schema}"'))
        metadata.create_all(_engine, checkfirst=True)
        with _engine.begin() as conn:
            for ddl in _ddl_vistas(self.schema):
                conn.execute(text(ddl))

    def _commit_si_corresponde(self):
        if not self._en_transaccion:
            self._session.commit()

    @contextmanager
    def transaccion(self):
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
        self._session.close()

    #Busca un objeto por su clave primaria y devuevle el objeto
    def obtener(self, entidad, clave):
        tabla, clase, pk = self._entidad(entidad)
        if clase is not None:
            return self._session.get(clase, clave)
        fila = self._session.execute(
            select(tabla).where(tabla.c[pk] == clave)).mappings().first()
        return dict(fila) if fila is not None else None

    def existe(self, entidad, clave):
        tabla, _clase, pk = self._entidad(entidad)
        fila = self._session.execute(
            select(literal(1)).select_from(tabla).where(tabla.c[pk] == clave).limit(1)
        ).first()
        return fila is not None

    #Devuelve una lista de objetos o lista de diccionarios
    def listar(self, entidad, where=None, params=(), incluir_eliminados=False, orden=None):
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
        tabla, clase, _pk = self._entidad(entidad)
        try:
            if clase is not None:
                self._session.add(objeto)
                self._session.flush()
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
        tabla, _clase, pk = self._entidad(entidad)
        try:
            self._session.execute(
                update(tabla).where(tabla.c[pk] == clave).values(eliminado=True))
            self._commit_si_corresponde()
        except Exception:
            self._session.rollback()
            raise

    def marcar_eliminados(self, entidad, claves):
        self.marcar_eliminados_por(entidad, self._entidad(entidad)[2], claves)

    #Eliminacion en cascada
    def marcar_eliminados_por(self, entidad, columna, valores):
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

    #Se usa para ejecutar codigo SQL puro
    def consultar(self, sql, params=()):
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

    def _guardar_lote(self, entidad, diccionario_datos):
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

    @staticmethod
    def inicializar_datos_si_vacio():
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
            sembrar_datos_ejemplo(gestor)
