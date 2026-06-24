# Diagramas de la base de datos

Dos diagramas de la base de datos **actual**:
1. **Diagrama Entidad-Relación (E-R)** en notación de **Peter Chen**.
2. **Diagrama Relacional** (esquema lógico: tablas, claves primarias y foráneas).

> Hay también un archivo `diagrama_er_chen.dot` (Graphviz) que renderiza el E-R como **imagen**.
> Ver la última sección para generarlo.

---

## 1. Diagrama Entidad-Relación (notación de Chen)

### Símbolos (leyenda)

```
 [ ENTIDAD ]      rectángulo  = entidad
 < relación >     rombo       = relación entre entidades
 ( atributo )     elipse      = atributo
 (_atributo_)     subrayado   = atributo clave (clave primaria)
 ──1──  ──N──     número sobre la línea = cardinalidad
```

> **Nota de diseño (importante para la defensa):** en el modelo conceptual de Chen, las **claves
> foráneas no se dibujan como atributos**: se representan mediante las **relaciones (rombos)**. Por
> eso aquí, p. ej., `postulacion` no muestra `cedula_estudiante`/`id_oferta` como atributos: esos
> vínculos están en los rombos *realiza* y *recibe*. Las FK sí aparecen en el **diagrama relacional**
> (sección 2).
>
> **Empresa embebida:** no existe una entidad `EMPRESA` separada; los datos de la empresa
> (`ruc_empresa`, `nombre_empresa`, `direccion_empresa`) son **atributos de** `TUTOR_EMPRESARIAL`.

### 1.1 Estructura (entidades, relaciones y cardinalidades)

```
                         [ COORDINADOR_VINCULACION ]
                                    |
                                  1 |
                              < valida >          (parcial: una postulación puede
                                  N |              no estar validada todavía)
                                    |
[ ESTUDIANTE ] ──1── < realiza > ──N── [ POSTULACION ] ──N── < recibe > ──1── [ OFERTA ]
      |                                       |                                     |
    1 |                                     1 |                                   N |
  < envia >                              < genera >                          < publica >
    N |                                     1 |                                   1 |
      |                                       |                                     |
[ SOLICITUD ]                            [ PRACTICA ] ─────────────────[ TUTOR_EMPRESARIAL ]
                                          |   |   |   \  N                          1
                                        1 |   |   |    \──── < supervisa > ─────────┘
                                          |   |   |                       (1 empresa : N prácticas)
                  ┌──── 1 < documenta_f1 > 1 ──── [ FORMULARIO1 ]
                  ├──── 1 < documenta_f2 > 1 ──── [ FORMULARIO2 ]
                  ├──── 1 < documenta_f3 > 1 ──── [ FORMULARIO3 ]
                  |
              [ PRACTICA ] ──N── < dirige > ──1── [ TUTOR_ACADEMICO ]

   [ ADMINISTRADOR ]      [ LOGIN ]   (credenciales de acceso; tabla independiente,
                                       sin clave foránea: el identificador puede ser
                                       el usuario del admin o la cédula de cualquier rol)
```

### 1.2 Relaciones (forma Chen, una por una)

| # | Relación (rombo) | Cardinalidad | Significado |
|---|---|---|---|
| 1 | `TUTOR_EMPRESARIAL` —< **publica** >— `OFERTA` | 1 : N | un tutor empresarial publica muchas ofertas |
| 2 | `OFERTA` —< **recibe** >— `POSTULACION` | 1 : N | una oferta recibe muchas postulaciones |
| 3 | `ESTUDIANTE` —< **realiza** >— `POSTULACION` | 1 : N | un estudiante hace muchas postulaciones |
| 4 | `COORDINADOR_VINCULACION` —< **valida** >— `POSTULACION` | 1 : N (parcial) | el coordinador valida postulaciones (puede estar sin validar) |
| 5 | `POSTULACION` —< **genera** >— `PRACTICA` | 1 : 1 | una postulación aceptada genera una práctica |
| 6 | `TUTOR_ACADEMICO` —< **dirige** >— `PRACTICA` | 1 : N (parcial) | un tutor académico dirige varias prácticas |
| 7 | `TUTOR_EMPRESARIAL` —< **supervisa** >— `PRACTICA` | 1 : N (parcial) | un tutor empresarial supervisa varias prácticas |
| 8 | `ESTUDIANTE` —< **envia** >— `SOLICITUD` | 1 : N | un estudiante envía varias solicitudes |
| 9 | `PRACTICA` —< **documenta_f1** >— `FORMULARIO1` | 1 : 1 | una práctica tiene un Formulario 1 |
| 10 | `PRACTICA` —< **documenta_f2** >— `FORMULARIO2` | 1 : 1 | una práctica tiene un Formulario 2 |
| 11 | `PRACTICA` —< **documenta_f3** >— `FORMULARIO3` | 1 : 1 | una práctica tiene un Formulario 3 |

### 1.3 Atributos por entidad (elipses; la clave primaria va subrayada)

```
[ADMINISTRADOR]            (_usuario_) (contrasena) (email) (eliminado)
[LOGIN]                    (_identificador_) (contrasena) (rol) (eliminado)
[ESTUDIANTE]               (_cedula_) (nombres) (apellidos) (telefono) (email) (carrera)
                           (ciclo) (num_practicas_realizadas) (total_horas_realizadas)
                           (contrasena) (eliminado)
[TUTOR_ACADEMICO]          (_cedula_) (nombres) (apellidos) (telefono) (email) (carrera)
                           (contrasena) (eliminado)
[TUTOR_EMPRESARIAL]        (_cedula_) (nombres) (apellidos) (telefono) (email) (cargo)
                           (ruc_empresa·UNIQUE) (nombre_empresa) (direccion_empresa)
                           (contrasena) (eliminado)
[COORDINADOR_VINCULACION]  (_cedula_) (nombres) (apellidos) (telefono) (email)
                           (fecha_nacimiento) (direccion) (carrera) (contrasena) (eliminado)
[OFERTA]                   (_id_oferta_) (descripcion) (puesto) (fecha_publicacion) (eliminado)
[POSTULACION]              (_id_postulacion_) (fecha) (estado_validacion) (eliminado)
[PRACTICA]                 (_id_practica_) (fecha_inicio) (fecha_fin) (estado) (eliminado)
[SOLICITUD]                (_id_) (tipo) (motivo) (estado) (fecha) (datos_empresa) (eliminado)
[FORMULARIO1]              (_id_formulario1_) (tipo_documento) (numero_documento) (tipo_practica)
                           (remuneracion) (fecha_inicial) (fecha_final_aprox) (horas_aprox)
                           (actividades) (estado_aprobacion) (eliminado)
[FORMULARIO2]              (_id_formulario2_) (fecha_real_inicio) (fecha_real_fin) (horas_cumplidas)
                           (calificaciones_rubrica) (productos_relevantes) (aspectos_relevantes)
                           (estado) (eliminado)
[FORMULARIO3]              (_id_formulario3_) (campo_ocupacional) (calificacion_sobre_100)
                           (evaluacion_escenario) (estado) (eliminado)
```

> Los identificadores subrayados de OFERTA, POSTULACION, PRACTICA, SOLICITUD y FORMULARIOn son
> **claves subrogadas generadas por la base** (`GENERATED ALWAYS AS IDENTITY`). Las demás claves
> primarias son **naturales** (usuario, identificador, cédula).

---

## 2. Diagrama Relacional (esquema lógico)

Notación: la <u>clave primaria</u> va subrayada; `(FK → tabla.columna)` indica clave foránea.

```
ADMINISTRADOR ( PK usuario, contrasena, email, eliminado )

LOGIN ( PK identificador, contrasena, rol, eliminado )
   -- sin FK: identificador puede ser el usuario del admin o la cédula de cualquier rol

ESTUDIANTE ( PK cedula, contrasena, apellidos, nombres, telefono, email, carrera,
             ciclo, num_practicas_realizadas, total_horas_realizadas, eliminado )

TUTOR_ACADEMICO ( PK cedula, contrasena, nombres, apellidos, telefono, email, carrera, eliminado )

TUTOR_EMPRESARIAL ( PK cedula, contrasena, nombres, apellidos, telefono, email, cargo,
                    ruc_empresa [UNIQUE], nombre_empresa, direccion_empresa, eliminado )

COORDINADOR_VINCULACION ( PK cedula, contrasena, nombres, apellidos, telefono, email,
                          fecha_nacimiento, direccion, carrera, eliminado )

OFERTA ( PK id_oferta,  descripcion, puesto, fecha_publicacion, eliminado,
         ruc_empresa  (FK → tutor_empresarial.ruc_empresa) )

POSTULACION ( PK id_postulacion, fecha, estado_validacion, eliminado,
              cedula_estudiante (FK → estudiante.cedula),
              id_oferta         (FK → oferta.id_oferta),
              id_coordinador    (FK → coordinador_vinculacion.cedula)  -- NULL hasta validarse )

PRACTICA ( PK id_practica, fecha_inicio, fecha_fin, estado, eliminado,
           id_postulacion       (FK → postulacion.id_postulacion),
           id_tutor_academico   (FK → tutor_academico.cedula)    -- NULL si no asignado,
           id_tutor_empresarial (FK → tutor_empresarial.cedula) )

SOLICITUD ( PK id, tipo, motivo, estado, fecha, datos_empresa[JSONB], eliminado,
            cedula_estudiante (FK → estudiante.cedula) )

FORMULARIO1 ( PK id_formulario1, tipo_documento, numero_documento, tipo_practica, remuneracion,
              fecha_inicial, fecha_final_aprox, horas_aprox, actividades[JSONB],
              estado_aprobacion, eliminado,
              id_practica (FK → practica.id_practica) )

FORMULARIO2 ( PK id_formulario2, fecha_real_inicio, fecha_real_fin, horas_cumplidas,
              calificaciones_rubrica[JSONB], productos_relevantes, aspectos_relevantes,
              estado, eliminado,
              id_practica (FK → practica.id_practica) )

FORMULARIO3 ( PK id_formulario3, campo_ocupacional, calificacion_sobre_100,
              evaluacion_escenario[JSONB], estado, eliminado,
              id_practica (FK → practica.id_practica) )
```

### Resumen de cardinalidades (lado relacional)

```
tutor_empresarial 1 ───< N oferta            (oferta.ruc_empresa)
oferta            1 ───< N postulacion        (postulacion.id_oferta)
estudiante        1 ───< N postulacion        (postulacion.cedula_estudiante)
coordinador_vinc. 1 ───< N postulacion        (postulacion.id_coordinador, NULL-able)
postulacion       1 ───< 1 practica           (practica.id_postulacion)
tutor_academico   1 ───< N practica           (practica.id_tutor_academico, NULL-able)
tutor_empresarial 1 ───< N practica           (practica.id_tutor_empresarial, NULL-able)
estudiante        1 ───< N solicitud          (solicitud.cedula_estudiante)
practica          1 ───< 1 formulario1/2/3    (formularioN.id_practica)
```

---

## 3. Cómo obtener el diagrama E-R como imagen

El archivo `diagrama_er_chen.dot` (en la raíz del proyecto) contiene el diagrama de Chen completo
(entidades = rectángulos, atributos = elipses con la PK subrayada, relaciones = rombos con su
cardinalidad). Para convertirlo en imagen:

- **Con Graphviz instalado** (https://graphviz.org/download/):
  ```
  dot -Tpng diagrama_er_chen.dot -o diagrama_er_chen.png
  # (si el grafo queda muy disperso, probar otro motor:)
  neato -Tpng diagrama_er_chen.dot -o diagrama_er_chen.png
  ```
- **Sin instalar nada:** abrir https://dreampuf.github.io/GraphvizOnline y pegar el contenido
  del archivo `diagrama_er_chen.dot`; descargar el PNG/SVG resultante.
