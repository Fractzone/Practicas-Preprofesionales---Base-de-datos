CREATE SCHEMA IF NOT EXISTS practicas;
SET search_path TO practicas;

CREATE TABLE IF NOT EXISTS practicas.administrador (
    usuario VARCHAR(20) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    email VARCHAR(120) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS practicas.login (
    identificador VARCHAR(20) PRIMARY KEY,
    contrasena VARCHAR(255) NOT NULL,
    rol VARCHAR(30) NOT NULL,
    eliminado BOOLEAN NOT NULL DEFAULT FALSE,
    CHECK (rol IN ('administrador','estudiante','tutor_academico',
                   'tutor_empresarial','coordinador_vinculacion'))
);

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
CREATE INDEX IF NOT EXISTS idx_oferta_ruc_empresa ON practicas.oferta (ruc_empresa);

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
CREATE INDEX IF NOT EXISTS idx_postulacion_cedula_estudiante ON practicas.postulacion (cedula_estudiante);
CREATE INDEX IF NOT EXISTS idx_postulacion_id_oferta ON practicas.postulacion (id_oferta);
CREATE INDEX IF NOT EXISTS idx_postulacion_estado_validacion ON practicas.postulacion (estado_validacion);

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
CREATE INDEX IF NOT EXISTS idx_practica_id_postulacion ON practicas.practica (id_postulacion);

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
CREATE INDEX IF NOT EXISTS idx_solicitud_cedula_estudiante ON practicas.solicitud (cedula_estudiante);

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
CREATE INDEX IF NOT EXISTS idx_formulario1_id_practica ON practicas.formulario1 (id_practica);

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
CREATE INDEX IF NOT EXISTS idx_formulario2_id_practica ON practicas.formulario2 (id_practica);

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
CREATE INDEX IF NOT EXISTS idx_formulario3_id_practica ON practicas.formulario3 (id_practica);

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

INSERT INTO practicas.administrador (usuario, contrasena, email) VALUES
    ('admin', '<hash de "admin">', 'admin@uce.edu.ec')
ON CONFLICT (usuario) DO NOTHING;

INSERT INTO practicas.estudiante
    (cedula, contrasena, apellidos, nombres, telefono, email, carrera, ciclo,
     num_practicas_realizadas, total_horas_realizadas) VALUES
    ('1032222224', '<hash>', 'Mendez', 'Carlos', '0991111111', 'carlos.mendez@ucuenca.edu.ec', 'Ingeniería de Software', 7, 0, 0),
    ('2451212126', '<hash>', 'Paz', 'Lucia', '0992222222', 'lucia.paz@ucuenca.edu.ec', 'Ingeniería de Software', 8, 1, 240),
    ('1846543211', '<hash>', 'Vargas', 'Diego', '0993333333', 'diego.vargas@ucuenca.edu.ec', 'Ingeniería Civil', 9, 0, 0)
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO practicas.tutor_academico
    (cedula, contrasena, nombres, apellidos, telefono, email, carrera) VALUES
    ('0123456782', '<hash>', 'Hugo', 'Añazco', '0919265583', 'hugo.anazco@ucuenca.edu.ec', 'Ingeniería de Software'),
    ('0912345675', '<hash>', 'Eric', 'Martinez', '0992371889', 'eric.martinez@ucuenca.edu.ec', 'Ingeniería Civil')
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO practicas.tutor_empresarial
    (cedula, contrasena, nombres, apellidos, telefono, email, cargo, ruc_empresa,
     nombre_empresa, direccion_empresa) VALUES
    ('0107778889', '<hash>', 'Roberto', 'Arias', '0995377124', 'roberto@autofact.com', 'Gerente de TI', '0101010106001', 'AutoFact', 'Av. de las Américas & Simón Bolívar'),
    ('0108889990', '<hash>', 'Camila', 'Ortiz', '0908699931', 'camila@optisolver.com', 'Líder de Desarrollo', '0920202025001', 'OptiSolver', 'Calle Larga & Hermano Miguel')
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO practicas.coordinador_vinculacion
    (cedula, contrasena, nombres, apellidos, telefono, email, fecha_nacimiento, direccion, carrera) VALUES
    ('0755555554', '<hash>', 'Manuel', 'Perez', '0994444444', 'manuel.perez@ucuenca.edu.ec', '1980-05-15', 'Cuenca, Azuay', 'Ingeniería de Software')
ON CONFLICT (cedula) DO NOTHING;

INSERT INTO practicas.oferta (descripcion, puesto, fecha_publicacion, ruc_empresa) VALUES
    ('Desarrollo de API REST', 'Pasante Backend', '2026-03-01', '0101010106001'),
    ('Creación de interfaces web', 'Pasante Frontend', '2026-10-02', '0920202025001');

INSERT INTO practicas.postulacion (fecha, estado_validacion, cedula_estudiante, id_oferta) VALUES
    ('2026-03-04', 'Pendiente', '1032222224',
        (SELECT id_oferta FROM practicas.oferta WHERE puesto = 'Pasante Backend')),
    ('2026-10-11', 'Pendiente', '2451212126',
        (SELECT id_oferta FROM practicas.oferta WHERE puesto = 'Pasante Frontend'));

INSERT INTO practicas.login (identificador, contrasena, rol) VALUES
    ('admin', '<hash>', 'administrador'),
    ('1032222224', '<hash>', 'estudiante'),
    ('2451212126', '<hash>', 'estudiante'),
    ('1846543211', '<hash>', 'estudiante'),
    ('0123456782', '<hash>', 'tutor_academico'),
    ('0912345675', '<hash>', 'tutor_academico'),
    ('0107778889', '<hash>', 'tutor_empresarial'),
    ('0108889990', '<hash>', 'tutor_empresarial'),
    ('0755555554', '<hash>', 'coordinador_vinculacion')
ON CONFLICT (identificador) DO NOTHING;
