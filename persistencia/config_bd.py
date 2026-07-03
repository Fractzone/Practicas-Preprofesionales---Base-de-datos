import os

#Configuracion para la conexion a la base de datos
CONFIG_BD = {
    #Lee las variables de entorno para encontrar una conexion existente
    "host": os.environ.get("PGHOST", "localhost"),
    #Si no existe usa los datos estandar
    "port": int(os.environ.get("PGPORT", "5432")),
    "dbname": os.environ.get("PGDATABASE", "practicas_db"),
    "user": os.environ.get("PGUSER", "postgres"),
    "password": os.environ.get("PGPASSWORD", "admin"),
    "schema": os.environ.get("PGSCHEMA", "practicas"),
}
