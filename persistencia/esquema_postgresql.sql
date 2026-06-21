-- =====================================================================
-- Esquema PostgreSQL del Sistema de Prácticas Preprofesionales
-- =====================================================================
-- Este script es la documentación del esquema que la aplicación crea
-- automáticamente al arrancar (de forma idempotente) desde
-- persistencia/gestor_persistencia.py.
--
-- A diferencia del .sql del curso de Base de Datos (que usa IDs SERIAL,
-- tipos DATE y tablas empresa/convenio normalizadas), este esquema es un
-- ESPEJO FIEL de la estructura ya definida en el modelo Python:
--   * Las claves primarias son las claves naturales que genera la app
--     (cedula, usuario, identificador) o los IDs en formato texto que
--     produce siguiente_id() -> por eso son VARCHAR/TEXT.
--   * Las fechas se almacenan como TEXT en formato "dd/MM/yyyy", tal como
--     las maneja la aplicación.
--   * Las estructuras anidadas (listas/diccionarios) se guardan como JSONB.
--   * Los datos de empresa viven embebidos en tutor_empresarial (el modelo
--     Python no define entidades empresa/convenio separadas).
-- =====================================================================

CREATE SCHEMA IF NOT EXISTS practicas;
SET search_path TO practicas;

-- ----------------------------- Usuarios ------------------------------

CREATE TABLE IF NOT EXISTS practicas.administrador (
    usuario     TEXT PRIMARY KEY,
    contrasena  TEXT,
    email       TEXT,
    eliminado   BOOLEAN
);

-- Credenciales de acceso de todos los roles
CREATE TABLE IF NOT EXISTS practicas.login (
    identificador TEXT PRIMARY KEY,
    contrasena    TEXT,
    rol           TEXT,
    eliminado     BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.estudiante (
    cedula                   TEXT PRIMARY KEY,
    contrasena               TEXT,
    apellidos                TEXT,
    nombres                  TEXT,
    telefono                 TEXT,
    email                    TEXT,
    carrera                  TEXT,
    ciclo                    INTEGER,
    num_practicas_realizadas INTEGER,
    total_horas_realizadas   INTEGER,
    eliminado                BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.tutor_academico (
    cedula      TEXT PRIMARY KEY,
    contrasena  TEXT,
    nombres     TEXT,
    apellidos   TEXT,
    telefono    TEXT,
    email       TEXT,
    carrera     TEXT,
    eliminado   BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.tutor_empresarial (
    cedula            TEXT PRIMARY KEY,
    contrasena        TEXT,
    nombres           TEXT,
    apellidos         TEXT,
    telefono          TEXT,
    email             TEXT,
    cargo             TEXT,
    ruc_empresa       TEXT,
    nombre_empresa    TEXT,
    direccion_empresa TEXT,
    eliminado         BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.coordinador_vinculacion (
    cedula           TEXT PRIMARY KEY,
    contrasena       TEXT,
    nombres          TEXT,
    apellidos        TEXT,
    telefono         TEXT,
    email            TEXT,
    fecha_nacimiento TEXT,
    direccion        TEXT,
    carrera          TEXT,
    eliminado        BOOLEAN
);

-- ----------------------- Proceso de prácticas ------------------------

CREATE TABLE IF NOT EXISTS practicas.oferta (
    id_oferta         TEXT PRIMARY KEY,
    descripcion       TEXT,
    puesto            TEXT,
    fecha_publicacion TEXT,
    ruc_empresa       TEXT,
    eliminado         BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.postulacion (
    id_postulacion    TEXT PRIMARY KEY,
    fecha             TEXT,
    estado_validacion TEXT,
    cedula_estudiante TEXT,
    id_oferta         TEXT,
    id_coordinador    TEXT,
    eliminado         BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.practica (
    id_practica          TEXT PRIMARY KEY,
    fecha_inicio         TEXT,
    fecha_fin            TEXT,
    estado               TEXT,
    id_postulacion       TEXT,
    id_tutor_academico   TEXT,
    id_tutor_empresarial TEXT,
    eliminado            BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.solicitud (
    id                TEXT PRIMARY KEY,
    tipo              TEXT,
    motivo            TEXT,
    estado            TEXT,
    cedula_estudiante TEXT,
    fecha             TEXT,
    datos_empresa     JSONB,
    eliminado         BOOLEAN
);

-- ------------------------------ Formularios --------------------------

CREATE TABLE IF NOT EXISTS practicas.formulario1 (
    id_formulario1    TEXT PRIMARY KEY,
    id_practica       TEXT,
    tipo_documento    TEXT,
    numero_documento  TEXT,
    tipo_practica     TEXT,
    remuneracion      DOUBLE PRECISION,
    fecha_inicial     TEXT,
    fecha_final_aprox TEXT,
    horas_aprox       INTEGER,
    actividades       JSONB,
    estado_aprobacion TEXT,
    eliminado         BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.formulario2 (
    id_formulario2         TEXT PRIMARY KEY,
    id_practica            TEXT,
    fecha_real_inicio      TEXT,
    fecha_real_fin         TEXT,
    horas_cumplidas        INTEGER,
    calificaciones_rubrica JSONB,
    productos_relevantes   TEXT,
    aspectos_relevantes    TEXT,
    estado                 TEXT,
    eliminado              BOOLEAN
);

CREATE TABLE IF NOT EXISTS practicas.formulario3 (
    id_formulario3         TEXT PRIMARY KEY,
    id_practica            TEXT,
    campo_ocupacional      TEXT,
    calificacion_sobre_100 DOUBLE PRECISION,
    evaluacion_escenario   JSONB,
    estado                 TEXT,
    eliminado              BOOLEAN
);

-- =====================================================================
-- Datos de ejemplo (los inserta la aplicación en el primer arranque).
-- Se muestran aquí como referencia; las contraseñas de acceso están en
-- la tabla login.
-- =====================================================================

-- Administrador del sistema
INSERT INTO practicas.administrador (usuario, contrasena, email, eliminado) VALUES
    ('admin', 'admin', 'admin@uce.edu.ec', FALSE)
ON CONFLICT (usuario) DO NOTHING;

-- Estudiantes
INSERT INTO practicas.estudiante
    (cedula, contrasena, apellidos, nombres, telefono, email, carrera, ciclo,
     num_practicas_realizadas, total_horas_realizadas, eliminado) VALUES
    ('1032222224', 'est123', 'Mendez', 'Carlos', '0991111111', 'carlos.mendez@ucuenca.edu.ec', 'Ingeniería de Software', 7, 0, 0, FALSE),
    ('2451212126', 'est123', 'Paz', 'Lucia', '0992222222', 'lucia.paz@ucuenca.edu.ec', 'Ingeniería de Software', 8, 1, 240, FALSE),
    ('1846543211', 'est123', 'Vargas', 'Diego', '0993333333', 'diego.vargas@ucuenca.edu.ec', 'Ingeniería Civil', 9, 0, 0, FALSE)
ON CONFLICT (cedula) DO NOTHING;

-- Tutores académicos
INSERT INTO practicas.tutor_academico
    (cedula, contrasena, nombres, apellidos, telefono, email, carrera, eliminado) VALUES
    ('0123456782', 'ta123', 'Hugo', 'Añazco', '0919265583', 'hugo.anazco@ucuenca.edu.ec', 'Ingeniería de Software', FALSE),
    ('0912345675', 'ta123', 'Eric', 'Martinez', '0992371889', 'eric.martinez@ucuenca.edu.ec', 'Ingeniería Civil', FALSE)
ON CONFLICT (cedula) DO NOTHING;

-- Tutores empresariales (empresa embebida)
INSERT INTO practicas.tutor_empresarial
    (cedula, contrasena, nombres, apellidos, telefono, email, cargo, ruc_empresa,
     nombre_empresa, direccion_empresa, eliminado) VALUES
    ('0107778889', 'te123', 'Roberto', 'Arias', '0995377124', 'roberto@autofact.com', 'Gerente de TI', '0101010106001', 'AutoFact', 'Av. de las Américas & Simón Bolívar', FALSE),
    ('0108889990', 'te123', 'Camila', 'Ortiz', '0908699931', 'camila@optisolver.com', 'Líder de Desarrollo', '0920202025001', 'OptiSolver', 'Calle Larga & Hermano Miguel', FALSE)
ON CONFLICT (cedula) DO NOTHING;

-- Coordinador de vinculación
INSERT INTO practicas.coordinador_vinculacion
    (cedula, contrasena, nombres, apellidos, telefono, email, fecha_nacimiento,
     direccion, carrera, eliminado) VALUES
    ('0755555554', 'cv123', 'Manuel', 'Perez', '0994444444', 'manuel.perez@ucuenca.edu.ec', '15/05/1980', 'Cuenca, Azuay', 'Ingeniería de Software', FALSE)
ON CONFLICT (cedula) DO NOTHING;

-- Ofertas
INSERT INTO practicas.oferta
    (id_oferta, descripcion, puesto, fecha_publicacion, ruc_empresa, eliminado) VALUES
    ('1', 'Desarrollo de API REST', 'Pasante Backend', '01/03/2026', '0101010106001', FALSE),
    ('2', 'Creación de interfaces web', 'Pasante Frontend', '02/10/2026', '0920202025001', FALSE)
ON CONFLICT (id_oferta) DO NOTHING;

-- Postulaciones (pendientes de validación)
INSERT INTO practicas.postulacion
    (id_postulacion, fecha, estado_validacion, cedula_estudiante, id_oferta, id_coordinador, eliminado) VALUES
    ('1', '04/03/2026', 'Pendiente', '1032222224', '1', NULL, FALSE),
    ('2', '11/10/2026', 'Pendiente', '2451212126', '2', NULL, FALSE)
ON CONFLICT (id_postulacion) DO NOTHING;

-- Credenciales de acceso
INSERT INTO practicas.login (identificador, contrasena, rol, eliminado) VALUES
    ('admin', 'admin', 'administrador', FALSE),
    ('1032222224', 'est123', 'estudiante', FALSE),
    ('2451212126', 'est123', 'estudiante', FALSE),
    ('1846543211', 'est123', 'estudiante', FALSE),
    ('0123456782', 'ta123', 'tutor_academico', FALSE),
    ('0912345675', 'ta123', 'tutor_academico', FALSE),
    ('0107778889', 'te123', 'tutor_empresarial', FALSE),
    ('0108889990', 'te123', 'tutor_empresarial', FALSE),
    ('0755555554', 'cv123', 'coordinador_vinculacion', FALSE)
ON CONFLICT (identificador) DO NOTHING;
