# Sistema de Gestión de Prácticas Preprofesionales

> **Versión PostgreSQL.** Esta es una copia del proyecto que persiste los datos en
> **PostgreSQL** en lugar de archivos pickle (`.dat`). El acceso a datos se concentra en
> `persistencia/gestor_persistencia.py`; el resto del proyecto (modelo, controlador y
> vista) es idéntico a la versión original.

## 0. Puesta en marcha (PostgreSQL)

1. Tener un servidor **PostgreSQL** en ejecución y crear la base de datos:
   ```sql
   CREATE DATABASE practicas_db;
   ```
2. Editar `persistencia/config_bd.py` con sus credenciales (host, puerto, base, usuario,
   contraseña y esquema).
3. Instalar las dependencias: `pip install -r requirements.txt`.
4. Ejecutar `python main.py`. En el primer arranque la aplicación crea automáticamente el
   esquema, las tablas y los datos de ejemplo (esto es idempotente). El DDL equivalente,
   por si desea ejecutarlo manualmente, está en `persistencia/esquema_postgresql.sql`.

**Credenciales de acceso sembradas:** `admin`/`admin` (administrador);
estudiantes `1032222224`, `2451212126`, `1846543211` (clave `est123`);
tutores académicos `0123456782`, `0912345675` (`ta123`);
tutores empresariales `0107778889`, `0108889990` (`te123`);
coordinador de vinculación `0755555554` (`cv123`).

---

## 1. Flujo completo del proceso (5 fases)

El proceso sigue un orden definido. A continuación, el detalle paso a paso indicando
quién hace cada acción y qué ocurre en el sistema.

### Fase 1 — Preparación, ofertas y postulación
1. *(Opcional)* Si el estudiante consigue una **empresa propia**, envía una **Solicitud Especial**
   de tipo "Autorización de Empresa Propia" con los datos de la empresa. El **Coordinador de
   Vinculación** la revisa y, si la aprueba, registra al **Tutor Empresarial** (la empresa).
2. El **Tutor Empresarial** crea una **Oferta** de práctica para su empresa.
3. El **Estudiante** busca las ofertas disponibles y **postula** a la que le interese.

### Fase 2 — Validación, ternas y selección
4. El **Coordinador de Vinculación** **valida** la postulación. Para aprobarla, el estudiante
   debe estar en **ciclo ≥ 6** . Resultado: "Validada"
   (o "Rechazada").
5. El **Coordinador de Vinculación** arma una **Terna** (de 1 a 3 postulaciones validadas de la
   misma oferta) y la **envía** a la empresa.
6. El **Tutor Empresarial** recibe las ternas de su oferta, las revisa y **acepta** a un estudiante.
7. El **sistema** crea la **Práctica** (estado "En progreso") y **asigna automáticamente** los dos
   tutores: el empresarial (quien aceptó) y el académico (según la carrera del estudiante).

### Fase 3 — Planificación e inicio (Formulario 1)
8. El **Estudiante** llena el **Formulario 1 (Registro de PPP)**: tipo de documento, tipo de
   práctica, fechas, horas y el plan de actividades.
9. El **Tutor Académico** revisa el Formulario 1 y lo **aprueba**. La práctica pasa a "En Ejecución".

### Fase 4 — Ejecución y evaluación (Formularios 2 y 3)
10. El **Estudiante** cumple sus horas y luego marca **"Solicitar Evaluación Final"**. La práctica
    pasa a "Evaluación Solicitada".
11. El **Tutor Empresarial** llena el **Formulario 2 (Evaluación Empresarial)** con una rúbrica de
    10 habilidades. La práctica pasa a "Pendiente Nota".
12. El **Tutor Académico** revisa el Formulario 2 y llena el **Formulario 3 (Evaluación Académica)**
    con la nota final sobre 100 (rúbrica de 18 criterios).

### Fase 5 — Cierre y asentamiento de nota
13. El **Tutor Académico** pulsa **"Asentar Nota"**.
14. El **sistema** marca la práctica como "Finalizada / Aprobada" e incrementa en 1 el número de
    prácticas realizadas del estudiante.

---

## 2. Guía por rol (cómo funciona cada panel)

### 2.1 Administrador
Panel con accesos a los mantenimientos de cada tipo de usuario (estudiantes, tutores
académicos, coordinadores de vinculación y administradores). Cada mantenimiento es una sola
ventana con el mismo formato:

- **Formulario** con los datos del usuario.
- Botones **Agregar** y **Limpiar**.
- **Tabla** con los registros existentes.
- Debajo de la tabla: un campo **"Cédula/Usuario a eliminar"** con los botones **Eliminar** y **Refrescar**.

Para **agregar**: complete el formulario y pulse **Agregar**. Para **eliminar**: escriba la
cédula/usuario en el campo inferior y pulse **Eliminar** (se pide confirmación). **Refrescar**
recarga la tabla.

### 2.2 Estudiante
- **Buscar Oferta:** lista las ofertas disponibles. Escriba el **ID de la oferta** y pulse
  **Postular**. No se puede postular si ya tiene una práctica activa o una postulación activa a esa oferta.
- **Postulaciones:** muestra el estado de sus postulaciones.
- **Llenar Formulario 1:** disponible cuando ya tiene una práctica activa; registra los datos de
  inicio de la práctica y el plan de actividades (puede agregar/eliminar filas y usar **Limpiar**).
- **Solicitar Evaluación Final:** habilitado solo cuando la práctica está "En Ejecución".
- **Solicitudes especiales:** "Autorización de Empresa Propia" (adjunta datos de la empresa) o
  "Emisión de Certificado/Oficio".

### 2.3 Coordinador de Vinculación
- **Validar Postulaciones:** ingrese el ID de la postulación y pulse **Aprobar** o **Rechazar**.
- **Armar Terna:** seleccione una oferta, ingrese de 1 a 3 IDs de postulaciones validadas y pulse
  **Enviar Terna**.
- **Listar Estudiantes:** muestra el estado de los estudiantes (cédula, nombres, carrera, ciclo,
  número de prácticas y horas realizadas).
- **Gestionar Empresas:** mantenimiento de tutores empresariales, con el mismo
  formato de los demás mantenimientos.
- **Bandeja de Solicitudes:** aprueba o rechaza solicitudes; al aprobar "Empresa Propia" se abre
  el alta del tutor empresarial ya prellenada.

### 2.4 Tutor / Coordinador Empresarial
- **Crear Oferta:** crea una oferta para su empresa (el RUC se toma de su perfil).
- **Listar Prácticas Activas:** muestra sus prácticas en curso con su estado.
- **Recibir Ternas:** ve las ternas enviadas a su empresa; ingrese el ID de la postulación y pulse
  **Aceptar** para crear la práctica.
- **Evaluación Empresarial (Formulario 2):** ingrese el ID de la práctica, cargue los datos y
  califique la rúbrica de 10 habilidades.

### 2.5 Tutor / Coordinador Académico
- **Listar Prácticas Activas:** muestra las prácticas activas con su estado.
- **Aprobar Formulario 1:** revisa el detalle del Formulario 1 y lo aprueba.
- **Evaluación Académica (Formulario 3):** ingrese el ID de la práctica, complete la rúbrica de 18
  criterios y la nota sobre 100, guarde y luego **Asentar Nota** para cerrar la práctica.
