--Creamos el esquema practicas si no existe
CREATE SCHEMA IF NOT EXISTS practicas;
SET search_path TO practicas;

/*
 El flujo del sql es
 Python -> SQLAlchemy -> psycopg2 -> PostgresSQL

 El programa maneja la eliminacion con elimincacion logica en cascada para no romper las relaciones
 Existen las tablas para objetos y la tabla login, la cual solo guarda las credenciales y el rol, para una consulta mas optima
 */

-- Creacion de la tabla adminsitrradores
CREATE TABLE IF NOT EXISTS practicas.administrador (
    usuario VARCHAR(20) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    email VARCHAR(120) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE
);

-- Creacion de la tabla login
CREATE TABLE IF NOT EXISTS practicas.login (
    identificador VARCHAR(20) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (rol IN ('administrador','estudiante','tutor_academico',
                   'tutor_empresarial','coordinador_vinculacion'))
);

-- Creacion de la tabla estudiantes
CREATE TABLE IF NOT EXISTS practicas.estudiante (
    cedula VARCHAR(10) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    telefono VARCHAR(10) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    carrera VARCHAR(100) NOT NULL,
    ciclo INTEGER NOT NULL,
    num_practicas_realizadas INTEGER NOT NULL DEFAULT 0,
    total_horas_realizadas INTEGER NOT NULL DEFAULT 0,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (ciclo BETWEEN 1 AND 10),
    CHECK (num_practicas_realizadas >= 0),
    CHECK (total_horas_realizadas >= 0)
);

-- Creacion tutor academico
CREATE TABLE IF NOT EXISTS practicas.tutor_academico (
    cedula VARCHAR(10) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(10) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    carrera VARCHAR(100) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE
);

-- Creacion tabla tutor empresariaal
CREATE TABLE IF NOT EXISTS practicas.tutor_empresarial (
    cedula VARCHAR(10) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(10) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    cargo VARCHAR(100) NOT NULL,
    ruc_empresa VARCHAR(13) NOT NULL UNIQUE,
    nombre_empresa VARCHAR(150) NOT NULL,
    direccion_empresa VARCHAR(255) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE
);

-- Creacion tabla coordinador de vinculacion
CREATE TABLE IF NOT EXISTS practicas.coordinador_vinculacion (
    cedula VARCHAR(10) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    telefono VARCHAR(10) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    fecha_nacimiento DATE NOT NULL,
    direccion VARCHAR(255) NOT NULL,
    carrera VARCHAR(100) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE
);

-- Creacion tabla de ofertas
CREATE TABLE IF NOT EXISTS practicas.oferta (
    id_oferta INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    descripcion TEXT NOT NULL,
    puesto VARCHAR(100) NOT NULL,
    fecha_publicacion DATE,
    ruc_empresa VARCHAR(13) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_oferta_ruc_empresa FOREIGN KEY (ruc_empresa)
        REFERENCES practicas.tutor_empresarial(ruc_empresa)
);

-- Crear tabla postulacion
CREATE TABLE IF NOT EXISTS practicas.postulacion (
    id_postulacion INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha DATE,
    estado_validacion VARCHAR(20) NOT NULL,
    cedula_estudiante VARCHAR(10) NOT NULL,
    id_oferta INTEGER NOT NULL,
    id_coordinador VARCHAR(10),
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (estado_validacion IN ('Pendiente','Validada','Enviada','Aceptada','Rechazada')),
    CONSTRAINT fk_postulacion_cedula_estudiante FOREIGN KEY (cedula_estudiante)
        REFERENCES practicas.estudiante(cedula),
    CONSTRAINT fk_postulacion_id_oferta FOREIGN KEY (id_oferta)
        REFERENCES practicas.oferta(id_oferta),
    CONSTRAINT fk_postulacion_id_coordinador FOREIGN KEY (id_coordinador)
        REFERENCES practicas.coordinador_vinculacion(cedula)
);

-- Crear tabla practica
CREATE TABLE IF NOT EXISTS practicas.practica (
    id_practica INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_inicio DATE,
    fecha_fin DATE,
    estado VARCHAR(30) NOT NULL,
    id_postulacion INTEGER NOT NULL,
    id_tutor_academico VARCHAR(10),
    id_tutor_empresarial VARCHAR(10),
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (estado IN ('En progreso','En Ejecución','Evaluación Solicitada',
                      'Pendiente Nota','Finalizada / Aprobada')),
    CONSTRAINT fk_practica_id_postulacion FOREIGN KEY (id_postulacion)
        REFERENCES practicas.postulacion(id_postulacion),
    CONSTRAINT fk_practica_id_tutor_academico FOREIGN KEY (id_tutor_academico)
        REFERENCES practicas.tutor_academico(cedula),
    CONSTRAINT fk_practica_id_tutor_empresarial FOREIGN KEY (id_tutor_empresarial)
        REFERENCES practicas.tutor_empresarial(cedula)
);

-- Crear tabla solicitud
CREATE TABLE IF NOT EXISTS practicas.solicitud (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo VARCHAR(60) NOT NULL,
    motivo TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL,
    cedula_estudiante VARCHAR(10) NOT NULL,
    fecha DATE,
    datos_empresa JSONB,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (estado IN ('Pendiente','Aprobada','Rechazada')),
    CHECK (tipo IN ('Autorización de Empresa Propia','Emisión de Certificado/Oficio')),
    CONSTRAINT fk_solicitud_cedula_estudiante FOREIGN KEY (cedula_estudiante)
        REFERENCES practicas.estudiante(cedula)
);

-- Crear tabla formulario
CREATE TABLE IF NOT EXISTS practicas.formulario1 (
    id_formulario1 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_practica INTEGER NOT NULL,
    tipo_documento VARCHAR(40) NOT NULL,
    numero_documento VARCHAR(50) NOT NULL,
    tipo_practica VARCHAR(30) NOT NULL,
    remuneracion NUMERIC(10,2) NOT NULL,
    fecha_inicial DATE,
    fecha_final_aprox DATE,
    horas_aprox INTEGER NOT NULL,
    actividades JSONB NOT NULL,
    estado_aprobacion VARCHAR(20) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (estado_aprobacion IN ('Pendiente','Aprobado')),
    CHECK (remuneracion >= 0),
    CHECK (horas_aprox > 0),
    CONSTRAINT fk_formulario1_id_practica FOREIGN KEY (id_practica)
        REFERENCES practicas.practica(id_practica)
);

-- Crear tabla fomrulario 2
CREATE TABLE IF NOT EXISTS practicas.formulario2 (
    id_formulario2 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_practica INTEGER NOT NULL,
    fecha_real_inicio DATE,
    fecha_real_fin DATE,
    horas_cumplidas INTEGER NOT NULL,
    calificaciones_rubrica JSONB NOT NULL,
    productos_relevantes TEXT NOT NULL,
    aspectos_relevantes TEXT NOT NULL,
    estado VARCHAR(20) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (horas_cumplidas > 0),
    CHECK (estado IN ('Completado')),
    CONSTRAINT fk_formulario2_id_practica FOREIGN KEY (id_practica)
        REFERENCES practicas.practica(id_practica)
);

-- Crear tabbla formulario 3
CREATE TABLE IF NOT EXISTS practicas.formulario3 (
    id_formulario3 INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_practica INTEGER NOT NULL,
    campo_ocupacional VARCHAR(150) NOT NULL,
    calificacion_sobre_100 NUMERIC(5,2) NOT NULL,
    evaluacion_escenario JSONB NOT NULL,
    estado VARCHAR(20) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (calificacion_sobre_100 BETWEEN 0 AND 100),
    CHECK (estado IN ('Completado')),
    CONSTRAINT fk_formulario3_id_practica FOREIGN KEY (id_practica)
        REFERENCES practicas.practica(id_practica)
);

-- Creacion de views
CREATE OR REPLACE VIEW practicas.vista_postulacion_detalle AS
SELECT p.id_postulacion, p.estado_validacion, p.fecha, p.eliminado, p.cedula_estudiante,
       e.nombres AS est_nombres, e.apellidos AS est_apellidos, e.ciclo AS est_ciclo,
       e.num_practicas_realizadas AS est_num_practicas, e.carrera AS est_carrera,
       p.id_oferta, o.puesto AS oferta_puesto, o.descripcion AS oferta_descripcion,
       o.ruc_empresa, te.nombre_empresa
FROM practicas.postulacion p
JOIN practicas.estudiante e ON p.cedula_estudiante = e.cedula
JOIN practicas.oferta o ON p.id_oferta = o.id_oferta
JOIN practicas.tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa;

CREATE OR REPLACE VIEW practicas.vista_practica_detalle AS
SELECT pr.id_practica, pr.estado, pr.fecha_inicio, pr.fecha_fin, pr.eliminado,
       pr.id_postulacion, pr.id_tutor_academico, pr.id_tutor_empresarial,
       e.cedula AS est_cedula, e.nombres AS est_nombres, e.apellidos AS est_apellidos,
       e.carrera AS est_carrera,
       ta.nombres AS acad_nombres, ta.apellidos AS acad_apellidos,
       te.nombres AS emp_nombres, te.apellidos AS emp_apellidos, te.nombre_empresa
FROM practicas.practica pr
JOIN practicas.postulacion p ON pr.id_postulacion = p.id_postulacion
JOIN practicas.estudiante e ON p.cedula_estudiante = e.cedula
LEFT JOIN practicas.tutor_academico ta ON pr.id_tutor_academico = ta.cedula
LEFT JOIN practicas.tutor_empresarial te ON pr.id_tutor_empresarial = te.cedula;

CREATE OR REPLACE VIEW practicas.vista_oferta_detalle AS
SELECT o.id_oferta, o.puesto, o.descripcion, o.fecha_publicacion, o.eliminado,
       o.ruc_empresa, te.nombre_empresa
FROM practicas.oferta o
JOIN practicas.tutor_empresarial te ON o.ruc_empresa = te.ruc_empresa;

CREATE OR REPLACE VIEW practicas.vista_estudiantes_destacados AS
SELECT
    e.cedula,
    e.nombres,
    e.apellidos,
    COUNT(f3.id_formulario3) AS practicas_evaluadas,
    ROUND(AVG(f3.calificacion_sobre_100), 2) AS promedio_calificacion
FROM practicas.estudiante e
LEFT JOIN practicas.postulacion p ON p.cedula_estudiante = e.cedula AND p.eliminado = FALSE
LEFT JOIN practicas.practica pr ON pr.id_postulacion = p.id_postulacion AND pr.eliminado = FALSE
LEFT JOIN practicas.formulario3 f3 ON f3.id_practica = pr.id_practica AND f3.eliminado = FALSE
WHERE e.eliminado = FALSE
GROUP BY e.cedula, e.nombres, e.apellidos
HAVING AVG(f3.calificacion_sobre_100) > (
    SELECT AVG(calificacion_sobre_100)
    FROM practicas.formulario3
    WHERE eliminado = FALSE
)
ORDER BY promedio_calificacion DESC;

-- Insercion de datos
INSERT INTO practicas.administrador (usuario, contrasena, email) VALUES
    ('admin', 'admin', 'admin@uce.edu.ec');

INSERT INTO practicas.estudiante
(cedula, contrasena, apellidos, nombres, telefono, email, carrera, ciclo,
 num_practicas_realizadas, total_horas_realizadas) VALUES
   ('1032222224', 'est123', 'Mendez', 'Carlos', '0991111111', 'carlos.mendez@ucuenca.edu.ec', 'Ingeniería de Software', 7, 0, 0),
   ('2451212126', 'est123', 'Paz', 'Lucia', '0992222222', 'lucia.paz@ucuenca.edu.ec', 'Ingeniería de Software', 8, 1, 240),
   ('1846543211', 'est123', 'Vargas', 'Diego', '0993333333', 'diego.vargas@ucuenca.edu.ec', 'Ingeniería Civil', 9, 0, 0);

INSERT INTO practicas.tutor_academico
(cedula, contrasena, nombres, apellidos, telefono, email, carrera) VALUES
   ('0123456782', 'ta123', 'Hugo', 'Añazco', '0919265583', 'hugo.anazco@ucuenca.edu.ec', 'Ingeniería de Software'),
   ('0912345675', 'ta123', 'Eric', 'Martinez', '0992371889', 'eric.martinez@ucuenca.edu.ec', 'Ingeniería Civil');

INSERT INTO practicas.tutor_empresarial
(cedula, contrasena, nombres, apellidos, telefono, email, cargo, ruc_empresa,
 nombre_empresa, direccion_empresa) VALUES
    ('0107778889', 'te123', 'Roberto', 'Arias', '0995377124', 'roberto@autofact.com', 'Gerente de TI', '0101010106001', 'AutoFact', 'Av. de las Américas & Simón Bolívar'),
    ('0108889990', 'te123', 'Camila', 'Ortiz', '0908699931', 'camila@optisolver.com', 'Líder de Desarrollo', '0920202025001', 'OptiSolver', 'Calle Larga & Hermano Miguel');

INSERT INTO practicas.coordinador_vinculacion
(cedula, contrasena, nombres, apellidos, telefono, email, fecha_nacimiento, direccion, carrera) VALUES
    ('0755555554', 'cv123', 'Manuel', 'Perez', '0994444444', 'manuel.perez@ucuenca.edu.ec', '1980-05-15', 'Cuenca, Azuay', 'Ingeniería de Software');

INSERT INTO practicas.oferta (descripcion, puesto, fecha_publicacion, ruc_empresa) VALUES
   ('Desarrollo de API REST', 'Pasante Backend', '2026-03-01', '0101010106001'),
   ('Creación de interfaces web', 'Pasante Frontend', '2026-10-02', '0920202025001');

INSERT INTO practicas.postulacion (fecha, estado_validacion, cedula_estudiante, id_oferta) VALUES
   ('2026-03-04', 'Pendiente', '1032222224',
    (SELECT id_oferta FROM practicas.oferta WHERE puesto = 'Pasante Backend')),
   ('2026-10-11', 'Pendiente', '2451212126',
    (SELECT id_oferta FROM practicas.oferta WHERE puesto = 'Pasante Frontend'));

INSERT INTO practicas.login (identificador, contrasena, rol) VALUES
     ('admin', 'admin', 'administrador'),
     ('1032222224', 'est123', 'estudiante'),
     ('2451212126', 'est123', 'estudiante'),
     ('1846543211', 'est123', 'estudiante'),
     ('0123456782', 'ta123', 'tutor_academico'),
     ('0912345675', 'ta123', 'tutor_academico'),
     ('0107778889', 'te123', 'tutor_empresarial'),
     ('0108889990', 'te123', 'tutor_empresarial'),
     ('0755555554', 'cv123', 'coordinador_vinculacion');

-- Querys de ejemplo
SELECT * From practicas.vista_postulacion_detalle;
SELECT * From practicas.vista_practica_detalle;
SELECT * From practicas.vista_oferta_detalle;
SELECT * From practicas.vista_estudiantes_destacados;