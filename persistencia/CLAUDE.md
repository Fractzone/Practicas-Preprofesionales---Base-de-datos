# Guía de la base de datos — Sistema de Prácticas Preprofesionales

> **Para Claude (app de escritorio):** este documento es tu contexto. El usuario te irá
> pasando funciones o fragmentos del código de la base de datos y te preguntará
> "¿qué hace esto?" o "¿por qué se hace así?". Tu tarea es **explicárselo en
> español, claro y sin tecnicismos innecesarios**, apoyándote en lo que aquí se
> describe. Si te pasa una función, ubícala primero (¿es del gestor?, ¿de un
> repositorio?, ¿de la config?) y luego explícala línea por línea o por bloques,
> según lo que pida. Cuando algo dependa de otra pieza (por ejemplo, un tipo
> personalizado o una transacción), menciónalo y explica la conexión.

---

## 1. En una frase

El programa es un sistema de gestión de prácticas preprofesionales (estudiantes,
tutores, ofertas, postulaciones, prácticas y formularios). Los datos se guardan en
una base de datos **PostgreSQL**. Toda la comunicación con la base pasa por **un
solo punto**: la clase `GestorPersistencia` (archivo `gestor_persistencia.py`).

## 2. Arquitectura por capas

El proyecto está separado en capas; conviene saber dónde encaja la base de datos:

| Capa | Carpeta | Qué hace |
|------|---------|----------|
| **Vista** | `vista/` | Interfaz gráfica (PyQt/Swing según versión). No toca la base directamente. |
| **Controlador** | `controlador/` | Orquesta la lógica de cada caso de uso. Usa repositorios. |
| **Modelo** | `modelo/` | Clases de datos (Estudiante, Oferta, ...) y **repositorios**. |
| **Persistencia** | `persistencia/` | Habla con PostgreSQL. Aquí vive el gestor. |

Flujo típico: **Vista → Controlador → Repositorio (modelo) → GestorPersistencia (persistencia) → PostgreSQL**.

Un detalle importante de diseño: las clases del modelo (`Estudiante`, `Oferta`,
etc.) **no saben nada de SQLAlchemy ni de la base de datos**. Son clases de Python
normales. Es el gestor quien las conecta con las tablas mediante un "mapeo
imperativo" (ver sección 6). Así las capas quedan bien separadas.

## 3. Los tres archivos de `persistencia/`

- **`config_bd.py`** — los datos de conexión (host, puerto, usuario, contraseña,
  base, esquema). Se leen de **variables de entorno** y, si no existen, usan
  valores por defecto de desarrollo local (`localhost`, `postgres`/`admin`, base
  `practicas_db`, esquema `practicas`).
- **`gestor_persistencia.py`** — el corazón: define las tablas, los tipos
  personalizados, conecta las clases con las tablas y ofrece la API de acceso a
  datos (obtener, listar, insertar, actualizar, borrar lógico, consultar, ...).
- **`esquema_postgresql.sql`** — script SQL **documental**. Describe el mismo
  esquema que el gestor crea solo al arrancar. Sirve como referencia; la
  aplicación **no** lo ejecuta (las tablas las crea SQLAlchemy).

## 4. Tecnología usada

- **PostgreSQL** como motor de base de datos.
- **SQLAlchemy 2.0** como librería de acceso (a través del driver `psycopg2`).
- Se usa **SQLAlchemy Core** (objetos `Table`, `Column`) para describir el esquema,
  y **mapeo imperativo** (`registry.map_imperatively`) para asociar cada tabla con
  su clase del modelo sin modificar la clase.
- Las contraseñas se cifran con **PBKDF2-HMAC-SHA256** (módulo `modelo/seguridad.py`).

## 5. El esquema: tablas y relaciones

Todas las tablas viven en el esquema `practicas`. Hay tres grupos:

**Usuarios / roles**
- `administrador` (PK: `usuario`)
- `login` — credenciales de acceso de **todos** los roles (PK: `identificador`).
  No tiene clave foránea porque el identificador puede ser el usuario del admin o
  la cédula de cualquier otro rol.
- `estudiante`, `tutor_academico`, `tutor_empresarial`, `coordinador_vinculacion`
  (PK: `cedula` en cada una).

**Proceso de prácticas**
- `oferta` (PK autogenerada `id_oferta`) → apunta a `tutor_empresarial.ruc_empresa`.
- `postulacion` (PK `id_postulacion`) → apunta a `estudiante`, `oferta` y opcionalmente
  a `coordinador_vinculacion`.
- `practica` (PK `id_practica`) → apunta a `postulacion` y a los dos tutores.
- `solicitud` (PK `id`) → apunta a `estudiante`. Es la única entidad que se maneja
  como **diccionario** en vez de clase (no tiene clase en el modelo).

**Formularios** (los tres apuntan a `practica`)
- `formulario1`, `formulario2`, `formulario3`.

### Reglas de negocio codificadas en el esquema

- **Claves naturales** donde tiene sentido (usuario, cédula) → `VARCHAR`.
- **Claves subrogadas** generadas por la base con `IDENTITY` (`GENERATED ALWAYS
  AS IDENTITY`) para oferta, postulación, práctica, solicitud y formularios →
  `INTEGER`. La app las recupera con `INSERT ... RETURNING`.
- **`CHECK`** para validar estados y rangos (p. ej. `ciclo BETWEEN 1 AND 10`,
  estados de postulación/práctica, remuneración ≥ 0).
- **`UNIQUE`** en emails y en `ruc_empresa` (una empresa = un tutor empresarial).
- **Fechas** como `DATE` en la base, pero como texto `"dd/MM/yyyy"` en la app.
- **Dinero y notas** como `NUMERIC` (no coma flotante).
- **Estructuras anidadas** (actividades, rúbricas, datos de empresa) como `JSONB`.
- **Borrado lógico**: cada tabla tiene una columna `eliminado BOOLEAN`. No se borra
  físicamente; se marca `eliminado = TRUE` (ver sección 8).

### Vistas

Hay tres vistas (`vista_postulacion_detalle`, `vista_practica_detalle`,
`vista_oferta_detalle`) que concentran los `JOIN` de los listados de la interfaz
en la propia base. Los repositorios las consultan con `consultar(...)` en vez de
armar los JOIN en Python.

## 6. Cómo se conectan las clases con las tablas (mapeo imperativo)

En `gestor_persistencia.py`:

1. Se definen las tablas con `Table(...)` y `Column(...)` (SQLAlchemy Core).
2. `mapper_registry.map_imperatively(Clase, tabla)` asocia cada clase del modelo
   con su tabla **sin tocar la clase**. Después de esto, al leer una fila
   SQLAlchemy devuelve un objeto `Estudiante`, `Oferta`, etc. ya poblado.
3. `mapper_registry.configure()` deja todo listo desde el primer uso.
4. El diccionario **`ENTIDADES`** es un catálogo central: para cada nombre de
   entidad (`"estudiante"`, `"oferta"`, ...) guarda una tupla
   `(tabla, clase, nombre_de_la_clave_primaria)`. Casi todos los métodos del gestor
   empiezan buscando aquí con `self._entidad(entidad)`. `solicitud` tiene `None`
   como clase porque se maneja como diccionario.

## 7. Tipos personalizados (TypeDecorator)

Son "traductores" automáticos entre lo que usa la app y lo que guarda la base:

- **`FechaTexto`** — en la app las fechas son texto `"dd/MM/yyyy"`; en la base son
  `DATE`. Al escribir convierte texto → fecha; al leer convierte fecha → texto.
- **`ContrasenaHash`** — al escribir, si la contraseña aún no está cifrada, la
  cifra (hash con sal) usando `hash_password`. Al leer devuelve el hash tal cual.
  Así **nunca** se guarda una contraseña en texto plano. La verificación al
  iniciar sesión la hace `verificar_password` en `modelo/seguridad.py`.

## 8. La API del gestor (lo que usan los repositorios)

Métodos públicos de `GestorPersistencia`, con lo que hace cada uno:

- **`obtener(entidad, clave)`** — devuelve un objeto/dict por su clave primaria, o
  `None`. Incluye los marcados como eliminados (el filtro lo decide quien llama).
- **`existe(entidad, clave)`** — `True`/`False` si la clave existe físicamente.
- **`listar(entidad, where, params, incluir_eliminados, orden)`** — lista objetos.
  Por defecto **excluye los eliminados**. `where` es una cláusula SQL con
  marcadores `%s` y `params` sus valores.
- **`insertar(entidad, objeto)`** — alta de una fila. Si el id lo genera la base
  (`IDENTITY`), lo recupera con `RETURNING` y lo asigna de vuelta al objeto.
- **`actualizar(entidad, objeto)`** — modifica una fila por su clave primaria.
- **`marcar_eliminado(entidad, clave)`** — borrado lógico de una fila.
- **`marcar_eliminados(entidad, claves)`** — borrado lógico en lote por PK.
- **`marcar_eliminados_por(entidad, columna, valores)`** — borrado lógico en lote
  filtrando por cualquier columna (p. ej. todos los formularios de varias prácticas).
- **`consultar(sql, params)`** — ejecuta SQL libre (p. ej. `SELECT` sobre las
  vistas) y devuelve lista de diccionarios `{columna: valor}`. Las fechas salen
  formateadas a `"dd/MM/yyyy"`.
- **`transaccion()`** — context manager (`with gestor.transaccion():`) para agrupar
  varias escrituras en una sola transacción atómica (ver sección 9).
- **`close()`** — cierra la sesión y devuelve la conexión al pool.

Métodos internos útiles para explicar:
- **`_bindize(sql, params)`** — traduce los marcadores `%s` (estilo psycopg2) a
  parámetros nombrados `:_p0`, `:_p1`, ... que entiende `text()` de SQLAlchemy. Es
  clave para entender por qué los repositorios pueden escribir `where="x = %s"`.
- **`_condicion(...)`** — arma el `WHERE` combinando el filtro de `eliminado = FALSE`
  con el `where` opcional del repositorio.
- **`_asegurar_esquema()`** — crea esquema, tablas, índices, restricciones y vistas
  si no existen (idempotente). Se llama al construir el gestor.
- **`_guardar_lote(...)`** — inserción/actualización masiva idempotente
  (`ON CONFLICT DO UPDATE`); solo la usa el sembrado inicial.

## 9. Transacciones

Regla general: **cada escritura confirma (commit) por sí sola**. Pero si se ejecuta
dentro de `with gestor.transaccion():`, todas las escrituras del bloque se confirman
**juntas al final**, o se revierten (rollback) por completo si algo falla. Soporta
anidamiento: solo el bloque más externo confirma. La bandera interna
`_en_transaccion` es la que controla esto, y `_commit_si_corresponde()` solo hace
commit cuando **no** estamos dentro de un bloque.

## 10. Borrado lógico y cascada

No se borra nada físicamente: se pone `eliminado = TRUE`. La "cascada" (borrar un
estudiante y arrastrar sus postulaciones, prácticas, formularios y solicitudes) se
hace **en código**, en `controlador/eliminacion_cascada.py`, no con
`ON DELETE CASCADE`. Ese archivo:
1. Lee los registros relacionados con los repositorios.
2. Los marca en lote con `marcar_eliminados_por`, todo dentro de **una sola
   transacción**, para que sea atómico.

## 11. Datos de ejemplo (sembrado)

`inicializar_datos_si_vacio()` corre al primer arranque: si la tabla `login` está
vacía, crea el usuario `admin` (contraseña `admin`) y siembra estudiantes, tutores,
un coordinador, ofertas y postulaciones de prueba, cada uno con su credencial. Usa
`_crear(...)`, que instancia objetos del modelo **sin pasar por las validaciones**
del constructor (porque son datos ya conocidos y válidos).

## 12. Cómo usan esto los repositorios (para que reconozcas el patrón)

Los repositorios viven en el `modelo/` (p. ej. `RepositorioOferta` en
`modelo/proceso.py`). Reciben el gestor y delegan en él. Ejemplo real:

```python
class RepositorioOferta:
    ENTIDAD = 'oferta'
    def __init__(self, persistencia):
        self.persistencia = persistencia
    def de_empresa(self, ruc_empresa):
        return self.persistencia.listar(self.ENTIDAD, where="ruc_empresa = %s", params=(ruc_empresa,))
    def agregar(self, descripcion, puesto, fecha_publicacion, ruc_empresa):
        nueva = Oferta(None, descripcion, puesto, fecha_publicacion, ruc_empresa)
        self.persistencia.insertar(self.ENTIDAD, nueva)  # la base asigna id_oferta
        return nueva
```

Cuando el usuario te pase una función de un repositorio, casi siempre será una
línea que llama a `self.persistencia.<método>(...)`. Explica **qué método del
gestor usa, con qué filtro `where`/`params`, y qué devuelve**.

## 13. Glosario rápido (para responder al vuelo)

- **Entidad**: un nombre de tabla en texto (`"estudiante"`, `"oferta"`, ...) que el
  gestor traduce a `(tabla, clase, clave_primaria)` con el diccionario `ENTIDADES`.
- **PK / clave primaria**: identificador único de la fila.
- **IDENTITY**: id que genera automáticamente PostgreSQL al insertar.
- **JSONB**: tipo de PostgreSQL para guardar listas/diccionarios (JSON).
- **`%s`**: marcador de parámetro; el valor real viaja aparte en `params` (evita
  inyección SQL).
- **Borrado lógico**: marcar `eliminado = TRUE` en vez de eliminar la fila.
- **Idempotente**: se puede ejecutar varias veces sin causar daño ni duplicar.
- **TypeDecorator**: traductor automático de tipo entre app y base (fechas, hash).

---

### Cómo quiero que respondas

Cuando te pase una función y te pregunte por ella:
1. Di **de qué archivo/capa es** y **para qué sirve** en una frase.
2. Explícala **por bloques o líneas**, en español sencillo.
3. Señala **con qué otras piezas se conecta** (gestor, tipos, transacciones, vistas).
4. Si aplica, menciona **qué pasa en la base de datos** por debajo.
5. Evita inventar: si algo no está en el código que te paso ni en esta guía, dilo.
