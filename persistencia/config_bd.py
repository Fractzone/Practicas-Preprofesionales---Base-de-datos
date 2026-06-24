"""
Configuración de la conexión a PostgreSQL.

Los valores se leen de variables de entorno (buena práctica: no incrustar
credenciales en el código fuente) y, si no están definidas, se usan los valores
por defecto de un entorno de desarrollo local. Para producción/entrega, definir:

    PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD, PGSCHEMA

La base de datos indicada en PGDATABASE debe existir previamente (por ejemplo,
créela con `CREATE DATABASE practicas_db;`). El esquema (PGSCHEMA) se crea
automáticamente si no existe.
"""
import os

CONFIG_BD = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "practicas_db"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "postgresql"),
    "schema": os.environ.get("PGSCHEMA", "practicas"),
}
