# Documentación técnica — Sistema de Gestión de Prácticas Preprofesionales

Resumen técnico del proyecto para entenderlo y poder exponerlo. Describe la tecnología,
la arquitectura, el modelo de datos, el flujo del proceso y las decisiones de diseño.

---

## 1. ¿Qué es?

Aplicación de **escritorio** desarrollada en **Python + PyQt6** que gestiona el ciclo completo
de las prácticas preprofesionales de una carrera universitaria. Maneja **5 tipos de usuario**,
ofertas de práctica, postulaciones, selección por ternas, tres formularios digitales de
seguimiento/evaluación y el cierre con la nota final.

- **Lenguaje:** Python 3.
- **Interfaz gráfica:** PyQt6 (estilo de Qt Designer).
- **Persistencia:** base de datos **PostgreSQL** (acceso con `psycopg2`). El esquema declara
  integridad referencial (claves foráneas), restricciones (`NOT NULL`, `UNIQUE`, `CHECK`),
  longitudes (`VARCHAR(n)`) y tipos apropiados (`DATE`, `JSONB`). El acceso a datos se hace con
  consultas SQL puntuales (`SELECT/INSERT/UPDATE` con `WHERE`), no cargando tablas enteras en memoria.
- **Arranque:** `python main.py`. En el primer arranque la aplicación **crea el esquema, las tablas,
  los índices y las vistas** (de forma idempotente) y siembra el usuario administrador
  (`admin` / `admin`) más datos de ejemplo; desde ahí se registran los demás usuarios.

---

## 2. Arquitectura (patrón MVC en 3 capas)

El proyecto separa responsabilidades en tres capas más una de persistencia:

```
modelo/        → Datos y reglas de negocio (entidades + repositorios + validaciones)
vista/         → Interfaz gráfica (pantallas y sus configuraciones)
controlador/   → Orquesta: conecta lo que el usuario hace en la vista con el modelo
persistencia/  → Acceso a PostgreSQL (gestor genérico con SQL puntual) + DDL del esquema
main.py        → Punto de entrada: arranca la aplicación y muestra el login
```

**Idea central:** la vista no sabe de datos, el modelo no sabe de la interfaz, y el
controlador es el intermediario. Esto hace el código ordenado y fácil de mantener.

### 2.1 Capa de modelo: entidades + repositorios
Cada archivo del modelo contiene **dos cosas**:
1. La **clase de la entidad** (p. ej. `Estudiante`), que en su constructor **valida** sus datos
   (cédula, correo, etc.) y lanza un error si algo está mal.
2. Su **repositorio** (p. ej. `RepositorioEstudiante`), que es el responsable de **listar,
   buscar, agregar, actualizar y eliminar** registros de esa entidad. El repositorio es el
   **único lugar donde vive el SQL** (patrón Repository/DAO): traduce cada operación a una
   consulta puntual (`obtener`, `listar(where=...)`, `insertar`, `actualizar`, `marcar_eliminado`)
   que ejecuta el gestor de persistencia. La vista y el controlador no escriben SQL.

Las **validaciones de ingreso viven en el repositorio/entidad**, no en el controlador. Si un dato
es inválido, el modelo lanza un `ValueError` con un mensaje claro, y el controlador lo muestra.

### 2.2 Capa de persistencia
`GestorPersistencia` (en `persistencia/gestor_persistencia.py`) es genérico y es el **único punto
de acceso a PostgreSQL**. A partir de un diccionario `MAPEO` (que describe cada tabla: columnas,
tipos, restricciones, claves foráneas, `CHECK` e índices) ofrece **primitivas SQL puntuales** a los
repositorios:

- `obtener(entidad, clave)` → `SELECT ... WHERE pk = %s`.
- `listar(entidad, where=None, params=(), orden=None)` → `SELECT ... [WHERE ...] [ORDER BY ...]`
  (por defecto excluye los marcados como eliminados).
- `insertar(entidad, objeto)` → `INSERT`. Para las tablas con id generado por la base
  (`GENERATED ALWAYS AS IDENTITY`) usa `INSERT ... RETURNING` y asigna el id al objeto.
- `actualizar(entidad, objeto)` → `UPDATE ... SET ... WHERE pk = %s` (UPDATE real, no upsert).
- `marcar_eliminado(s)` / `marcar_eliminados_por(columna, valores)` → borrado lógico en lote.
- `consultar(sql, params)` → SQL libre para los `JOIN` (vistas).
- `transaccion()` → *context manager* que agrupa varias escrituras en una sola transacción atómica.

Las fechas se manejan en la app como texto `dd/MM/yyyy` pero se almacenan como `DATE`; la conversión
está centralizada en `_hacia_bd`/`_desde_bd`, así el resto del proyecto no cambia. El dinero y la
nota se guardan como `NUMERIC`; las estructuras anidadas (actividades, rúbricas, datos de empresa)
como `JSONB`; las contraseñas, **cifradas** (hash con sal; ver `modelo/seguridad.py`). Los
identificadores subrogados (oferta, postulación, práctica, solicitud, formularios) los **genera la
base** (IDENTITY), no la aplicación. La conexión se configura por variables de entorno en
`persistencia/config_bd.py`. El esquema completo está en `persistencia/esquema_postgresql.sql`,
espejo fiel del DDL que crea la aplicación.

### 2.3 Capa de vista
Cada pantalla tiene dos partes:
- Una clase `Ui_*` que **construye los widgets** (etiquetas, campos, botones, tablas), al estilo
  de lo que genera Qt Designer.
- Una clase **"interfaz" (wrapper)** —archivos `interfaz_vista_*.py`— que hereda de la `Ui_*` y le
  añade la configuración: íconos, validadores numéricos, fuente de las tablas, tooltips, etc.
  Así la pantalla queda limpia y la configuración separada.

### 2.4 Capa de controlador
Un controlador por módulo/rol. En su arranque crea los repositorios que necesita y la(s)
ventana(s), **conecta los botones** con sus acciones (slots) y **delega** la validación al modelo.
Nunca manipula los diccionarios de datos directamente.

---

## 3. Roles del sistema (5 usuarios)

| Rol | Qué hace |
|---|---|
| **Administrador** | Da de alta/baja a los usuarios del sistema (estudiantes, tutores académicos, coordinadores de vinculación y otros administradores). |
| **Estudiante** | Busca ofertas, postula, llena el Formulario 1, solicita la evaluación final y envía solicitudes especiales. |
| **Coordinador de Vinculación** | Valida postulaciones, arma ternas, registra empresas y atiende solicitudes especiales. |
| **Tutor/Coordinador Empresarial** | Representa una empresa: crea ofertas, acepta estudiantes de las ternas y llena el Formulario 2. |
| **Tutor/Coordinador Académico** | Aprueba el Formulario 1, llena el Formulario 3 y asienta la nota final. |

Cada rol tiene su **panel principal** con barra de menú y barra de herramientas (cada botón con su
tooltip de ayuda). El login identifica el rol y abre el panel correspondiente.

---

## 4. Modelo de datos (entidades y relaciones)

| Entidad | Clave | Descripción |
|---|---|---|
| `Administrador` | usuario | Usuario administrador. |
| `Estudiante` | cédula | Incluye carrera, ciclo, número de prácticas realizadas y total de horas realizadas (acumuladas al finalizar cada práctica). |
| `TutorAcademico` | cédula | Supervisor académico; tiene carrera. |
| `TutorEmpresarial` | cédula | **Es también la empresa**: incluye RUC, nombre y dirección de la empresa. |
| `CoordinadorVinculacion` | cédula | Coordinador del proceso. |
| `Oferta` | id numérico | Oferta de práctica; referencia a la empresa por su RUC. |
| `Postulacion` | id numérico | Vincula un estudiante con una oferta y guarda su estado. |
| `Practica` | id numérico | Se crea al aceptar a un estudiante; referencia a la postulación y a los dos tutores. |
| `Formulario1/2/3` | id numérico | Un formulario de cada tipo por práctica. |
| `Solicitud` | id numérico | Solicitudes especiales del estudiante (con `datos_empresa` en `JSONB`). |
| `Credencial` | identificador | Usuario + contraseña + rol; vive en la tabla `login`. |

**Relaciones clave:**
- Una **empresa** y su **tutor empresarial** son la misma entidad (no existe una clase `Empresa`
  aparte; los datos de la empresa están dentro de `TutorEmpresarial` y se referencian por el RUC).
- Una **oferta** pertenece a una empresa (por RUC).
- Una **postulación** une estudiante ↔ oferta.
- Una **práctica** nace de una postulación aceptada y guarda los dos tutores (cédulas reales).
- Cada **formulario** pertenece a una práctica.

### 4.1 Integridad en la base de datos
Las personas conservan su **clave natural** (cédula, usuario), pero los identificadores de los
registros del proceso (oferta, postulación, práctica, solicitud, formularios) son **subrogados y los
genera la base** con `GENERATED ALWAYS AS IDENTITY` (no se calculan en la aplicación). La base de
datos **hace cumplir** las reglas que antes solo vivían en Python:

- **Identidad:** PK naturales (`usuario`, `cedula`) y PK subrogadas `INTEGER IDENTITY` para el
  proceso; la app las recupera con `INSERT ... RETURNING`.
- **Claves foráneas (sin `ON DELETE CASCADE`, porque el borrado es lógico):**
  `oferta.ruc_empresa → tutor_empresarial.ruc_empresa`,
  `postulacion.cedula_estudiante → estudiante`, `postulacion.id_oferta → oferta`,
  `postulacion.id_coordinador → coordinador_vinculacion` (nullable),
  `practica.id_postulacion → postulacion`, `practica.id_tutor_academico/empresarial` (nullables),
  `solicitud.cedula_estudiante → estudiante`, `formulario1/2/3.id_practica → practica`.
  `login.identificador` **no** lleva FK (puede apuntar a cualquier tabla de usuario).
- **`UNIQUE`:** `tutor_empresarial.ruc_empresa` (una empresa = un tutor empresarial, necesario para
  la FK de `oferta`) y `email` en estudiante/tutores/coordinador.
- **`CHECK`:** estados de postulación, práctica, solicitud y formularios; tipo de solicitud;
  `ciclo BETWEEN 1 AND 10`; contadores y montos no negativos; nota entre 0 y 100.
- **Tipos:** fechas `DATE`, dinero/nota `NUMERIC` (no coma flotante), anidados `JSONB`,
  contraseñas **cifradas** (`VARCHAR(255)` con hash + sal).
- **Índices** sobre las columnas que más se filtran (FK y estados).
- **Vistas** (`vista_postulacion_detalle`, `vista_practica_detalle`, `vista_oferta_detalle`) que
  concentran los `JOIN` de los listados de la interfaz en la base de datos.
- **Transacciones por caso de uso:** las operaciones que tocan varias tablas (aceptar estudiante +
  crear práctica, asentar nota + acreditar horas, alta de usuario + credencial, borrado en cascada)
  se ejecutan dentro de `gestor.transaccion()` para que sean atómicas.

### Familia "Coordinador" (única herencia del proyecto)
Los tres tipos de coordinador/tutor (académico, empresarial y de vinculación) comparten campos
comunes (cédula, contraseña, nombres, apellidos, teléfono, email). Por eso hay una **clase base
`Coordinador`** y los tres heredan de ella, añadiendo sus campos propios. El resto del proyecto
mantiene un estilo plano (sin herencia) para que sea sencillo.

---

## 5. Login y credenciales

Las credenciales se guardan **separadas** del resto, en la tabla `login`, como objetos `Credencial`
(`identificador`, `contraseña`, `rol`). El **identificador** es la **cédula** para estudiante,
tutores y coordinador; y el **usuario** para el administrador. Al dar de alta o de baja a un
usuario, el sistema mantiene la tabla `login` sincronizada automáticamente
(`controlador/sincronizador_credenciales.py`), dentro de la misma transacción que el alta/baja.

Las contraseñas **se almacenan cifradas** (hash PBKDF2 con sal, `modelo/seguridad.py`): nunca en
texto plano. El login verifica con `verificar_password(...)` y las tablas de gestión de usuarios
no muestran la contraseña (la enmascaran). En el primer arranque solo existe el administrador
**`admin` / `admin`**; desde su panel se crean los demás usuarios.

---

## 6. Flujo del proceso (5 fases)

1. **Ofertas y postulación:** la empresa publica una oferta; el estudiante postula.
2. **Validación, ternas y selección:** vinculación valida la postulación (el estudiante debe estar
   en **ciclo ≥ 6**; puede haber hecho prácticas antes, ya que el objetivo es acumular horas), arma
   una terna (1 a 3 candidatos) y la envía; la empresa acepta a uno. El sistema crea
   la práctica y asigna automáticamente los dos tutores: el **empresarial** = quien aceptó; el
   **académico** = un tutor de la **misma carrera** del estudiante; si no hay de esa carrera, se
   asigna cualquier tutor académico existente; si no hay ninguno, queda sin asignar. Este tutor
   académico asignado es **solo informativo**: cualquier tutor académico puede aprobar el
   Formulario 1 y asentar la nota (no hay restricción por usuario).
3. **Planificación (Formulario 1):** el estudiante registra el inicio de la práctica; el tutor
   académico lo aprueba.
4. **Ejecución y evaluación (Formularios 2 y 3):** el estudiante solicita la evaluación final; la
   empresa llena el Formulario 2; el académico llena el Formulario 3 con la nota sobre 100.
5. **Cierre:** el académico asienta la nota; la práctica queda finalizada, se incrementa el contador
   de prácticas del estudiante y se **suman las horas reales cumplidas** (del Formulario 2) a su
   total de horas. Un estudiante puede realizar **varias prácticas** hasta acumular las horas requeridas.

*(El detalle paso a paso y la guía de cada panel están en `README.md`.)*

---

## 7. Máquinas de estado

**Postulación:** `Pendiente → Validada → Enviada → Aceptada` (o `Rechazada`).

**Práctica:** `En progreso → En Ejecución → Evaluación Solicitada → Pendiente Nota → Finalizada / Aprobada`.

Cada acción del sistema solo está disponible en el estado correcto (por ejemplo, "Solicitar
Evaluación Final" solo cuando la práctica está "En Ejecución").

---

## 8. Los tres formularios digitales

En vez de subir archivos, los formularios son **digitales y estructurados** (cada uno es una clase
con su repositorio y su tabla; las rúbricas/actividades se guardan como `JSONB`), uno de cada tipo
por práctica:

- **Formulario 1 – Registro de PPP** (lo llena el estudiante): tipo de documento, tipo de práctica,
  fechas, horas y plan de actividades.
- **Formulario 2 – Evaluación Empresarial** (lo llena el tutor empresarial): fechas y horas reales,
  rúbrica de 10 habilidades (A = Excelente … E = Insatisfactorio) y observaciones.
- **Formulario 3 – Evaluación Académica** (lo llena el tutor académico): campo ocupacional, rúbrica
  de 18 criterios (nivel 1–4 o "No aplica") y nota final sobre 100.

---

## 9. Validaciones

**De datos** (al guardar cualquier registro):
- Cédula ecuatoriana válida (10 dígitos con su dígito verificador).
- Teléfono: 10 dígitos que empiezan con `09`.
- RUC: 13 dígitos que terminan en `001`.
- Correo electrónico con formato válido.
- Contraseña de 4 a 10 caracteres.
- Campos obligatorios no vacíos y valores numéricos dentro de rango.

**De fechas (según el contexto):**
- Formulario 1: la fecha de inicio no puede ser anterior a hoy, y la fecha final no puede ser
  anterior a la de inicio.
- Formulario 2: las fechas reales no pueden ser futuras, y el fin no puede ser anterior al inicio.

Si una validación falla, el modelo lanza un error y la interfaz muestra un mensaje claro.

---

## 10. Eliminación lógica en cascada (soft delete)

El sistema **nunca borra datos físicamente**. Cada registro tiene una marca `eliminado`; al
"eliminar", se marca como inactivo y deja de aparecer en listados, búsquedas y login.

La eliminación es **en cascada**:
- Al eliminar un **estudiante** se dan de baja también sus postulaciones, prácticas, formularios y
  solicitudes.
- Al eliminar una **empresa/tutor empresarial** se dan de baja sus ofertas, las postulaciones a
  esas ofertas, sus prácticas y los formularios.
- Al eliminar un administrador, tutor académico o coordinador de vinculación, solo se da de baja a
  ese usuario (no se anulan las prácticas de los estudiantes por dar de baja a un supervisor).

La cascada (`controlador/eliminacion_cascada.py`) lee los registros relacionados con los
repositorios (SQL con `WHERE`) y los marca en lote con `UPDATE ... SET eliminado = TRUE WHERE
columna = ANY(...)`. Cada cascada se ejecuta en una **única transacción** (un solo `commit` al
final, o `rollback` si algo falla), de modo que nunca queda una eliminación a medias.

Ventaja: se conserva el histórico y se evita dejar datos "huérfanos".

---

## 11. Estándares de la interfaz

- **Tipografía:** Segoe UI en toda la aplicación. Títulos en 14, textos generales en 11, datos de
  tablas en 10. Sin negritas.
- **Apariencia neutra:** estilo "Fusion" con la paleta estándar de Qt (independiente del color de
  acento de Windows).
- **Tamaño:** los paneles miden 800×600 (salvo los tres formularios, más altos, y los cuadros de
  diálogo). Los formularios grandes se abren centrados.
- **Recursos portables:** todos los íconos e imágenes se cargan con `ruta_recurso(...)`, que calcula
  la ruta a partir de la ubicación del proyecto. Por eso **funciona en cualquier computador** mientras
  se copie la carpeta completa (incluida `vista/recursos/`).
- **Carrera por lista fija:** el campo carrera (en estudiante, tutor académico y coordinador) se
  elige de un **combo** con las 4 carreras de la facultad (Computación, Electricidad, Ingeniería
  Civil, Telecomunicaciones), para evitar errores de tipeo y que la asignación por carrera coincida.
- **Nomenclatura de widgets:** prefijos consistentes (`lbl` etiquetas, `txt` cajas de texto, `cmb` combos,
  `btn` botones, `cmb` combos, `tbl` tablas, `dt` fechas, `spn`/`dspn` numéricos, `mnu` menús,
  `act` acciones, `tlb` barra de herramientas, etc.).

---

## 12. Estructura de carpetas

```
main.py                  # arranque de la aplicación
persistencia/            # gestor de acceso a PostgreSQL + config_bd.py + esquema_postgresql.sql
modelo/                  # entidades + repositorios + validaciones
controlador/             # un controlador por rol/módulo + utilidades (sincronizador, cascada)
vista/
  recursos/              # íconos e imágenes
  ventanas_generales/    # utilidades de GUI, rutas de recursos, diálogos (error/confirmación/info)
  vista_login/           # pantalla de inicio de sesión
  vista_administrador/   # panel del administrador y su CRUD
  vista_estudiante/      # CRUD de estudiantes (operado por el administrador)
  vista_crud_personal/   # CRUD de tutores académicos y coordinadores de vinculación
  vista_modulo_*/        # paneles de cada rol (estudiante, vinculación, empresarial, académico)
```

---

## 13. Cómo ejecutar

1. Tener un servidor **PostgreSQL** en ejecución y crear la base de datos (ver `README.md`);
   ajustar la conexión en `persistencia/config_bd.py` si hace falta.
2. Tener Python 3 con PyQt6 y `psycopg2` instalados (ver `requirements.txt`).
3. Ejecutar `python main.py` desde la carpeta raíz: en el primer arranque se crean el esquema,
   las tablas, los índices, las vistas y los datos de ejemplo automáticamente.
4. Iniciar sesión con `admin` / `admin` y registrar los usuarios necesarios.
