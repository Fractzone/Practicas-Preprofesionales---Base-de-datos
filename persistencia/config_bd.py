"""
Configuración de la conexión a PostgreSQL.

Edite los valores de CONFIG_BD con las credenciales de su servidor PostgreSQL
antes de ejecutar la aplicación. La base de datos indicada en 'dbname' debe
existir previamente (por ejemplo, créela con `CREATE DATABASE practicas_db;`).
El esquema indicado en 'schema' se crea automáticamente si no existe.
"""

CONFIG_BD = {
    "host": "localhost",
    "port": 5432,
    "dbname": "practicas_db",
    "user": "postgres",
    "password": "postgresql",
    "schema": "practicas",
}
