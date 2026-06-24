# Plan de mejora del uso de PostgreSQL

> Documento de trabajo. Aquí se anotan **todos** los cambios que se buscan hacer.
> Se revisa primero y **luego se ejecuta**. Nada de esto está aplicado aún.

## 0. Decisiones ya tomadas (definen el alcance)

| Tema | Decisión |
|---|---|
| **Estructura del esquema** | **Pragmático**: conservar las claves naturales actuales (cédula, RUC, usuario, IDs de texto) y la empresa embebida en `tutor_empresarial`. **No** se reescribe a `SERIAL` ni se separan `empresa`/`convenio`. Se le **añaden** restricciones (FK, NOT NULL, UNIQUE, CHECK), longitudes (`VARCHAR(n)`) e índices. |
| **Consultas** | Migrar **todos** los repositorios a SQL puntual (`SELECT/INSERT/UPDATE` con `WHERE`), eliminando el patrón "cargar toda la tabla en memoria y filtrar con Python". |
| **Borrado** | Se **mantiene** la eliminación lógica (`eliminado BOOLEAN`). Las FK son normales (sin `ON DELETE CASCADE`); la cascada lógica sigue en código. |
| **Fechas** | Migrar de `TEXT` (`dd/MM/yyyy`) a tipo **`DATE`** en la BD, convirtiendo en la capa de persistencia para que el resto de la app siga viendo `dd/MM/yyyy`. |

### Principio rector sobre los repositorios
**No se eliminan las clases `Repositorio`.** El repositorio es el lugar **correcto** donde debe vivir el SQL (patrón Repository/DAO). Lo que cambia es su *implementación interna*: en vez de cargar todo a un diccionario y filtrar en Python, ejecutarán SQL puntual. La vista y el controlador **no cambian** su forma de llamarlos. Así "todo pasa por PostgreSQL" **dentro** de los repositorios, sin romper MVC ni meter SQL en la GUI.

---

## 1. Diagnóstico del estado actual

- La BD se usa **solo como reemplazo de los archivos pickle**: `cargar(entidad)` hace `SELECT` sin `WHERE` (trae la tabla entera) y `guardar(entidad, dict)` hace `INSERT ... ON CONFLICT DO UPDATE` de **todo** el diccionario.
- **Cero** `WHERE`, `JOIN`, `ORDER BY`, `GROUP BY` en SQL. Todo listado/búsqueda/filtro se hace en memoria con `filter`/`lambda`.
- **Sin integridad referencial**: ninguna FK. Cédulas, RUC e IDs son `TEXT` sueltos.
- **Sin restricciones**: ningún `NOT NULL`, `UNIQUE`, `CHECK`. Toda la validación vive en Python (`modelo/validaciones.py`).
- Fechas como `TEXT` `dd/MM/yyyy`; IDs de texto generados con `max()+1` en memoria.
- 12 repositorios afectados; el único punto de acceso a la BD es `persistencia/gestor_persistencia.py`.

---

## 2. Cambios en el esquema (DDL)

Se redefine `MAPEO` y `esquema_postgresql.sql` para incluir longitudes y restricciones. Resumen por tabla (PK = clave natural actual, salvo indicación):

### 2.1 Longitudes / tipos
- Cédula → `VARCHAR(10)`, RUC → `VARCHAR(13)`, teléfono → `VARCHAR(10)`.
- Email → `VARCHAR(120)`, nombres/apellidos/carrera/puesto → `VARCHAR(100/150)`.
- Fechas → **`DATE`** (ver sección 4).
- Estructuras anidadas (actividades, rúbricas, datos_empresa) → se mantienen en **`JSONB`**.
- `eliminado` → `BOOLEAN NOT NULL DEFAULT FALSE`.

### 2.2 `NOT NULL`
Columnas obligatorias según los constructores del modelo: en cada tabla, la PK, `contrasena`, `nombres`/`apellidos` (o `usuario`/`email` en admin), `carrera` (estudiante/tutor académico/coordinador), `ruc_empresa`/`nombre_empresa` (tutor empresarial), `id_oferta`/`cedula_estudiante` (postulación), `id_postulacion` (práctica), `id_practica` (formularios). Las columnas que pueden quedar vacías (p. ej. `postulacion.id_coordinador` hasta que se valida, `practica.fecha_fin`, tutores asignados) quedan **NULL-ables**.

### 2.3 `UNIQUE`
- `tutor_empresarial.ruc_empresa` → **`UNIQUE`** (necesario para poder referenciarlo desde `oferta.ruc_empresa`).
  ⚠️ *Implica la regla de negocio "una empresa = un solo tutor empresarial". Hoy el modelo lo asume así, pero hay que confirmarlo (ver sección 8).*
- `email` en estudiante / tutores / coordinador → `UNIQUE` (opcional; confirmar en sección 8).

### 2.4 Claves foráneas (FK)
Todas con tipos coincidentes a las PK referenciadas. Sin `ON DELETE CASCADE` (borrado lógico):

| Tabla.columna | Referencia |
|---|---|
| `oferta.ruc_empresa` | `tutor_empresarial.ruc_empresa` |
| `postulacion.cedula_estudiante` | `estudiante.cedula` |
| `postulacion.id_oferta` | `oferta.id_oferta` |
| `postulacion.id_coordinador` (NULL-able) | `coordinador_vinculacion.cedula` |
| `practica.id_postulacion` | `postulacion.id_postulacion` |
| `practica.id_tutor_academico` (NULL-able) | `tutor_academico.cedula` |
| `practica.id_tutor_empresarial` (NULL-able) | `tutor_empresarial.cedula` |
| `solicitud.cedula_estudiante` | `estudiante.cedula` |
| `formulario1/2/3.id_practica` | `practica.id_practica` |

> `login.identificador` **no** lleva FK: puede apuntar a admin, estudiante, tutores o coordinador (no hay una sola tabla destino). Se documenta el motivo.

> **Orden de creación de tablas**: ya es correcto en `MAPEO` (las referenciadas se crean antes). Se conserva ese orden.

### 2.5 `CHECK` (reflejan validaciones que hoy hace Python)
- `estudiante.ciclo` → `CHECK (ciclo BETWEEN 1 AND 10)`.
- `estudiante.num_practicas_realizadas >= 0`, `total_horas_realizadas >= 0`.
- `postulacion.estado_validacion` → `CHECK (estado_validacion IN ('Pendiente','Validada','Enviada','Aceptada','Rechazada'))`.
- `practica.estado` → `CHECK (estado IN ('En progreso','En Ejecución','Evaluación Solicitada','Pendiente Nota','Finalizada / Aprobada'))`.
- `formulario3.calificacion_sobre_100` → `CHECK (BETWEEN 0 AND 100)`.
- `formulario1.estado_aprobacion`, `formulario2.estado`, `solicitud.estado`, `solicitud.tipo` → CHECK por conjunto **una vez verificados todos los valores reales en el código** (sub-tarea previa para no romper la app).

### 2.6 Índices
- Índice en cada columna FK que se filtra a menudo: `postulacion(cedula_estudiante)`, `postulacion(id_oferta)`, `postulacion(estado_validacion)`, `practica(id_postulacion)`, `oferta(ruc_empresa)`, `formularioN(id_practica)`, `solicitud(cedula_estudiante)`.

---

## 3. Refactor de la capa de persistencia (`gestor_persistencia.py`)

Ampliar `GestorPersistencia` con **primitivas SQL puntuales** (genéricas, basadas en `MAPEO`) que usarán los repositorios:

- `obtener(entidad, clave)` → `SELECT ... WHERE pk = %s` → objeto/dict o `None`.
- `listar(entidad, where=None, params=(), incluir_eliminados=False, orden=None)` → `SELECT ... [WHERE ...] [ORDER BY ...]`.
- `upsert(entidad, objeto)` → `INSERT ... ON CONFLICT (pk) DO UPDATE` de **una** fila.
- `actualizar(entidad, clave, **campos)` → `UPDATE ... SET ... WHERE pk = %s` (para cambios puntuales de estado, contadores, etc.).
- `marcar_eliminado(entidad, clave)` → `UPDATE ... SET eliminado = TRUE WHERE pk = %s`.
- `siguiente_id(entidad)` → `SELECT COALESCE(MAX(CAST(pk AS INTEGER)),0)+1` (reemplaza el `max()+1` en memoria).
- `consultar(sql, params=())` → ejecuta SQL libre (para los `JOIN`/agregaciones de la sección 5) y devuelve filas como dicts.

Notas:
- Mantener temporalmente `cargar`/`guardar` antiguos para una **migración incremental** repositorio por repositorio; eliminarlos al final cuando ya nadie los use.
- Reutilizar el reconstructor `_reconstruir` (sigue usando `Cls.__new__`).
- Conversión de tipos centralizada en `_hacia_bd`/`_desde_bd` (incluye el nuevo caso `DATE`).

---

## 4. Migración de fechas a `DATE`

- En `MAPEO`, las columnas de fecha pasan de `TEXT` a `DATE`:
  `oferta.fecha_publicacion`, `postulacion.fecha`, `practica.fecha_inicio/fecha_fin`,
  `solicitud.fecha`, `formulario1.fecha_inicial/fecha_final_aprox`,
  `formulario2.fecha_real_inicio/fecha_real_fin`, `coordinador_vinculacion.fecha_nacimiento`.
- Conversión **centralizada** en la capa de persistencia (la app sigue usando strings `dd/MM/yyyy`):
  - Escritura: `_hacia_bd` con tipo `DATE` → `datetime.strptime(valor, "%d/%m/%Y").date()` (o `None`).
  - Lectura: `_desde_bd` con tipo `DATE` → `valor.strftime("%d/%m/%Y")` (o `None`).
- Resultado: **vistas, validaciones y controladores no cambian**; ganamos comparaciones/orden por fecha en SQL.
- Riesgo controlado: el único punto que toca el formato es el gestor. Probar con datos sembrados.

---

## 5. Migración de los repositorios a SQL puntual

Reescribir el interior de los 12 repositorios para usar las primitivas de la sección 3. La **interfaz pública de cada repositorio se conserva** (mismos nombres de método). Cambios típicos:

- `__init__`: deja de hacer `cargar()` masivo y de guardar el diccionario completo en memoria.
- `listar()` → `persistencia.listar(ENTIDAD)` (con `WHERE NOT eliminado`).
- `buscar(clave)` → `persistencia.obtener(ENTIDAD, clave)`.
- `agregar(...)` → valida con el modelo + `persistencia.upsert(...)`.
- `eliminar(clave)` → `persistencia.marcar_eliminado(...)`.
- Filtros como `de_empresa(ruc)`, `por_estado(estado)`, `de_estudiante(cedula)`, `de_ofertas([...])` → `SELECT ... WHERE ...` (con `IN (...)` donde aplique).
- `siguiente_id()` → `persistencia.siguiente_id(ENTIDAD)`.

Repositorios a migrar: `RepositorioAdministrador`, `RepositorioEstudiante`, `RepositorioTutorAcademico`, `RepositorioTutorEmpresarial`, `RepositorioCoordinadorVinculacion`, `RepositorioOferta`, `RepositorioPostulacion`, `RepositorioPractica`, `RepositorioSolicitud`, `RepositorioFormulario1/2/3`.

También adaptar:
- `controlador/eliminacion_cascada.py` (hoy marca objetos en memoria y llama `repo.guardar()`): pasará a usar `actualizar`/`marcar_eliminado` puntuales (idealmente un solo `UPDATE ... WHERE ... IN (...)` por tabla).
- `controlador/sincronizador_credenciales.py` (carga/guarda todo `login`): pasará a `obtener`/`upsert`/`marcar_eliminado`.

> ⚠️ Riesgo a vigilar: algunos controladores podrían depender de atributos internos tipo `repo.estudiantes` (diccionario). Hay que verificar y migrarlos a los métodos públicos. Sub-tarea de auditoría antes de borrar `cargar/guardar`.

---

## 6. Consultas con `JOIN` para los listados (lo que se ve en la GUI)

Identificar los listados que hoy **cruzan datos en Python** y reescribirlos como `SELECT ... JOIN`. Candidatos:
- **Listar Estudiantes** (panel coordinador): estudiante + nº prácticas + horas.
- **Validar Postulaciones / Bandeja**: postulación + estudiante + oferta + estado.
- **Listar Prácticas Activas** (académico/empresarial): práctica + estudiante + tutores + estado.
- **Buscar Ofertas** (estudiante): oferta + empresa (nombre_empresa por RUC).

Estos `JOIN` pueden encapsularse como métodos de consulta en el repositorio correspondiente (devolviendo dicts/filas listas para la tabla) usando `persistencia.consultar(sql, params)`. Opcionalmente, crear 1–2 **`CREATE VIEW`** para los cruces más usados (luce bien en la defensa de BD I).

---

## 7. Datos de ejemplo y arranque

- `_sembrar_datos_ejemplo` se mantiene, pero respetando el **orden por dependencias** (ya lo respeta) y las nuevas restricciones (las fechas sembradas deben ser válidas para `DATE`, los RUC únicos, etc.).
- `inicializar_datos_si_vacio` sigue igual (siembra solo si `login` está vacío).
- Mantener `esquema_postgresql.sql` como **espejo fiel** del DDL nuevo (FK, NOT NULL, CHECK, índices) para entrega/documentación.

---

## 8. Decisiones pendientes de confirmar (antes de ejecutar)

1. **Diseño de la capa de acceso**: ¿primitivas genéricas en `GestorPersistencia` (sección 3, **recomendado**, menos código repetido) **o** SQL escrito a mano y explícito dentro de cada repositorio (más "visible" para la materia, más código)? *Recomiendo el genérico para CRUD + SQL explícito solo para los `JOIN` de la sección 6.*
2. **`UNIQUE(ruc_empresa)`**: ¿se acepta la regla "una empresa = un solo tutor empresarial"? Es necesaria para la FK `oferta → tutor_empresarial`. Si no, habría que separar la tabla `empresa` (eso sería el enfoque "híbrido", descartado por ahora).
3. **`UNIQUE(email)`**: ¿lo aplicamos en estudiante/tutores/coordinador o lo dejamos libre?
4. **`CHECK` de estados de formularios/solicitudes**: confirmar el conjunto exacto de valores tras auditar el código, para no rechazar valores válidos.

---

## 9. Orden de ejecución propuesto (fases)

1. **Fase 0 — Respaldo**: copia del proyecto y/o `pg_dump` de `practicas_db`.
2. **Fase 1 — Esquema nuevo** (secciones 2 y 4): actualizar `MAPEO` + `esquema_postgresql.sql` con tipos, `NOT NULL`, `UNIQUE`, FK, `CHECK`, índices y fechas `DATE`. Probar arranque limpio (BD vacía → se crea y siembra).
3. **Fase 2 — Primitivas SQL** (sección 3): ampliar `GestorPersistencia` (incl. conversión `DATE`), conservando `cargar/guardar` temporalmente.
4. **Fase 3 — Migrar repositorios** (sección 5), entidad por entidad, probando la app entre cada uno.
5. **Fase 4 — Adaptar cascada y sincronizador** (sección 5).
6. **Fase 5 — Consultas `JOIN`/vistas** (sección 6).
7. **Fase 6 — Limpieza**: eliminar `cargar/guardar` masivos y código muerto; actualizar `README.md` y `DOCUMENTACION_TECNICA.md`.

---

## 10. Pruebas / verificación

- Arranque limpio sobre BD vacía: se crea esquema, tablas y datos de ejemplo sin error.
- Flujo completo de las 5 fases (postular → validar → terna → aceptar → Form1 → Form2 → Form3 → asentar nota) funcionando igual que antes.
- Intentar violar una FK / `CHECK` manualmente y comprobar que la BD lo rechaza.
- Eliminación lógica en cascada (estudiante y empresa) sigue marcando los hijos.
- Listados de la GUI muestran lo mismo que antes (ahora vía `JOIN`/`WHERE`).
