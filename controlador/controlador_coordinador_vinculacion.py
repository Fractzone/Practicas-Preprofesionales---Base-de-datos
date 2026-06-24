from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.proceso import RepositorioPostulacion, RepositorioOferta, RepositorioSolicitud
from modelo.estudiante import RepositorioEstudiante
from modelo.coordinadores import RepositorioTutorEmpresarial, TutorEmpresarial
from controlador.sincronizador_credenciales import SincronizadorCredenciales
from controlador.utilidades_controlador import parsear_id
from controlador import eliminacion_cascada
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_informacion import VistaInformacion
from vista.ventanas_generales.vista_confirmacion import VistaConfirmacion
from vista.vista_modulo_coordinador_vinculacion.interfaz_vista_modulo_coordinador_vinculacion import (
    VistaCoordinadorVinculacionPrincipal, VistaValidarPostulaciones, VistaArmarTernas,
    VistaGestionarEmpresas, VistaBandejaSolicitudes, VistaListarEstudiantes
)

class ControladorCoordinadorVinculacion:
    CICLO_MINIMO = 6
    TIPO_EMPRESA_PROPIA = "Autorización de Empresa Propia"

    def __init__(self, persistencia, cedula_coordinador):
        self.persistencia = persistencia
        self.cedula_coordinador = cedula_coordinador
        self.repo_postulaciones = RepositorioPostulacion(persistencia)
        self.repo_estudiantes = RepositorioEstudiante(persistencia)
        self.repo_ofertas = RepositorioOferta(persistencia)
        self.repo_empresas = RepositorioTutorEmpresarial(persistencia)
        self.repo_solicitudes = RepositorioSolicitud(persistencia)
        self.vista_menu = VistaCoordinadorVinculacionPrincipal()
        self.v_validar = VistaValidarPostulaciones()
        self.v_ternas = VistaArmarTernas()
        self.v_empresas = VistaGestionarEmpresas()
        self.v_bandeja = VistaBandejaSolicitudes()
        self.v_estudiantes = VistaListarEstudiantes()
        self.conectar_signals()

    def iniciar(self):
        self.vista_menu.show()

    def cargar_datos(self):
        self.repo_postulaciones.recargar()
        self.repo_estudiantes.recargar()
        self.repo_ofertas.recargar()
        self.repo_empresas.recargar()
        self.repo_solicitudes.recargar()

    def conectar_signals(self):
        self.vista_menu.actValidarPostulacion.triggered.connect(
            lambda: (self.refrescar_tabla_validacion(), self.v_validar.show()))
        self.vista_menu.actArmarTerna.triggered.connect(
            lambda: (self.cargar_combo_ofertas(), self.v_ternas.show()))
        self.vista_menu.actGestionarEmpresa.triggered.connect(
            lambda: (self.refrescar_tabla_empresas(), self.v_empresas.show()))
        self.vista_menu.actBandejaSolicitudes.triggered.connect(
            lambda: (self.refrescar_tabla_solicitudes(), self.v_bandeja.show()))
        self.vista_menu.actListarEstudiantes.triggered.connect(
            lambda: (self.refrescar_tabla_estudiantes(), self.v_estudiantes.show()))
        self.vista_menu.actSalir.triggered.connect(self.vista_menu.close)
        self.vista_menu.actInformacion.triggered.connect(self.slot_mostrar_informacion)

        self.v_validar.btnAprobar.clicked.connect(self.slot_aprobar)
        self.v_validar.btnRechazar.clicked.connect(self.slot_rechazar)
        self.v_validar.btnRefrescar.clicked.connect(self.refrescar_tabla_validacion)

        self.v_ternas.cmbOfertas.currentIndexChanged.connect(self.slot_filtrar_por_oferta)
        self.v_ternas.btnEnviarTerna.clicked.connect(self.slot_enviar_terna)
        self.v_ternas.btnRefrescarTernas.clicked.connect(self.slot_filtrar_por_oferta)

        self.v_empresas.btnGuardar.clicked.connect(self.slot_registrar_empresa)
        self.v_empresas.btnLimpiar.clicked.connect(self.limpiar_form_empresa)
        self.v_empresas.btnEliminar.clicked.connect(self.slot_eliminar_empresa)
        self.v_empresas.btnRefrescar.clicked.connect(self.refrescar_tabla_empresas)

        self.v_bandeja.btnAprobar.clicked.connect(self.slot_aprobar_solicitud)
        self.v_bandeja.btnRechazar.clicked.connect(self.slot_rechazar_solicitud)
        self.v_bandeja.btnRefrescar.clicked.connect(self.refrescar_tabla_solicitudes)

        self.v_estudiantes.btnRefrescar.clicked.connect(self.refrescar_tabla_estudiantes)

    def slot_mostrar_informacion(self):
        VistaInformacion(self.vista_menu).exec()

    @staticmethod
    def pintar_tabla(tabla, lista, fila_func):
        tabla.setRowCount(len(lista))
        list(map(lambda par: list(map(
            lambda col: tabla.setItem(par[0], col[0], QTableWidgetItem(str(col[1]))),
            enumerate(fila_func(par[1])))), enumerate(lista)))

    def nombre_completo(self, estudiante):
        return f"{estudiante.nombres} {estudiante.apellidos}" if estudiante else "N/A"

    def nombre_empresa(self, oferta):
        empresa = self.repo_empresas.buscar_por_ruc(oferta.ruc_empresa) if oferta else None
        return empresa.nombre_empresa if empresa else "N/A"

    def fila_validacion(self, d):
        # d proviene de un JOIN (vista_postulacion_detalle).
        return [
            d["id_postulacion"],
            d["cedula_estudiante"],
            f'{d["est_nombres"]} {d["est_apellidos"]}',
            str(d["est_ciclo"]),
            str(d["est_num_practicas"]),
            f'{d["oferta_puesto"]} - {d["nombre_empresa"]}',
            d["estado_validacion"]
        ]

    def fila_terna(self, post):
        estudiante = self.repo_estudiantes.buscar(post.cedula_estudiante)
        return [
            post.id_postulacion,
            estudiante.cedula if estudiante else "N/A",
            self.nombre_completo(estudiante),
            str(estudiante.ciclo) if estudiante else "N/A",
            post.estado_validacion
        ]

    def fila_empresa(self, te):
        return [te.cedula, f"{te.nombres} {te.apellidos}", te.cargo, te.ruc_empresa,
                te.nombre_empresa, te.email]

    @staticmethod
    def fila_estudiante(estudiante):
        return [estudiante.cedula, estudiante.nombres, estudiante.apellidos, estudiante.carrera,
                estudiante.ciclo, estudiante.num_practicas_realizadas, estudiante.total_horas_realizadas]

    def refrescar_tabla_estudiantes(self):
        self.cargar_datos()
        self.pintar_tabla(self.v_estudiantes.tblEstudiantes, self.repo_estudiantes.listar(), self.fila_estudiante)

    def fila_solicitud(self, sol):
        estudiante = self.repo_estudiantes.buscar(sol.get("cedula_estudiante"))
        return [sol["id"], sol["tipo"], self.nombre_completo(estudiante),
                sol["motivo"], sol["estado"], sol["fecha"]]

    def refrescar_tabla_validacion(self):
        pendientes = self.repo_postulaciones.detalle_pendientes()
        self.pintar_tabla(self.v_validar.tblPostulaciones, pendientes, self.fila_validacion)

    def slot_aprobar(self):
        try:
            id_postulacion = parsear_id(self.v_validar.txtIdPostulacion.text(), "ID de la postulación")
            postulacion = self.repo_postulaciones.buscar(id_postulacion)
            if not postulacion:
                raise ValueError(f"No se encontró la postulación con ID '{id_postulacion}'.")
            if postulacion.estado_validacion != "Pendiente":
                raise ValueError(f"La postulación ya fue procesada. Estado actual: {postulacion.estado_validacion}.")
            estudiante = self.repo_estudiantes.buscar(postulacion.cedula_estudiante)
            if not estudiante:
                raise ValueError("No se encontró el estudiante asociado.")
            if int(estudiante.ciclo) < self.CICLO_MINIMO:
                raise ValueError(f"El estudiante cursa el ciclo {estudiante.ciclo}. Se requiere mínimo {self.CICLO_MINIMO}to ciclo.")
            postulacion.estado_validacion = "Validada"
            postulacion.id_coordinador = self.cedula_coordinador
            self.repo_postulaciones.actualizar(postulacion)
            self.refrescar_tabla_validacion()
            QMessageBox.information(self.v_validar, "Éxito", f"Postulación {id_postulacion} aprobada.")
            self.v_validar.txtIdPostulacion.clear()
        except ValueError as e:
            VistaError(str(e), self.v_validar).exec()

    def slot_rechazar(self):
        try:
            id_postulacion = parsear_id(self.v_validar.txtIdPostulacion.text(), "ID de la postulación")
            postulacion = self.repo_postulaciones.buscar(id_postulacion)
            if not postulacion:
                raise ValueError(f"No se encontró la postulación con ID '{id_postulacion}'.")
            if postulacion.estado_validacion != "Pendiente":
                raise ValueError(f"La postulación ya fue procesada. Estado actual: {postulacion.estado_validacion}.")
            postulacion.estado_validacion = "Rechazada"
            self.repo_postulaciones.actualizar(postulacion)
            self.refrescar_tabla_validacion()
            QMessageBox.information(self.v_validar, "Éxito", f"Postulación {id_postulacion} rechazada.")
            self.v_validar.txtIdPostulacion.clear()
        except ValueError as e:
            VistaError(str(e), self.v_validar).exec()

    def cargar_combo_ofertas(self):
        self.cargar_datos()
        self.v_ternas.cmbOfertas.clear()
        self.v_ternas.cmbOfertas.addItem("-- Seleccione una oferta --", None)
        list(map(
            lambda o: self.v_ternas.cmbOfertas.addItem(
                f"{o.id_oferta} - {o.puesto} ({self.nombre_empresa(o)})", o.id_oferta),
            self.repo_ofertas.listar()))

    def slot_filtrar_por_oferta(self):
        id_oferta = self.v_ternas.cmbOfertas.currentData()
        if not id_oferta:
            self.v_ternas.tblPostulaciones.setRowCount(0)
            return
        validadas = self.repo_postulaciones.validadas_de_oferta(id_oferta)
        self.pintar_tabla(self.v_ternas.tblPostulaciones, validadas, self.fila_terna)

    def slot_enviar_terna(self):
        try:
            ids = [parsear_id(w.text(), "ID de postulación")
                   for w in (self.v_ternas.txtIdPostulante1, self.v_ternas.txtIdPostulante2,
                             self.v_ternas.txtIdPostulante3) if w.text().strip()]
            id_oferta = self.v_ternas.cmbOfertas.currentData()
            if not id_oferta:
                raise ValueError("Debe seleccionar una oferta.")
            if len(ids) < 1:
                raise ValueError("Debe ingresar al menos un ID de postulación (terna de 1 a 3).")
            if len(set(ids)) != len(ids):
                raise ValueError("Los IDs de la terna deben ser diferentes.")
            terna = list(map(self.repo_postulaciones.buscar, ids))
            no_encontradas = list(filter(lambda x: x[1] is None, zip(ids, terna)))
            if no_encontradas:
                raise ValueError(f"No se encontraron: {', '.join(map(lambda x: str(x[0]), no_encontradas))}.")
            fuera_de_oferta = list(filter(lambda p: p.id_oferta != id_oferta, terna))
            if fuera_de_oferta:
                raise ValueError("Todas las postulaciones de la terna deben pertenecer a la oferta seleccionada.")
            no_validadas = list(filter(lambda p: p.estado_validacion != "Validada", terna))
            if no_validadas:
                raise ValueError(f"No están 'Validada': {', '.join(map(lambda p: str(p.id_postulacion), no_validadas))}.")
            list(map(lambda p: setattr(p, 'estado_validacion', 'Enviada'), terna))
            with self.persistencia.transaccion():
                list(map(self.repo_postulaciones.actualizar, terna))
            self.slot_filtrar_por_oferta()
            QMessageBox.information(self.v_ternas, "Éxito",
                                    f"Terna de {len(terna)} postulante(s) enviada para la oferta {id_oferta}.")
            list(map(lambda w: w.clear(),
                     [self.v_ternas.txtIdPostulante1, self.v_ternas.txtIdPostulante2, self.v_ternas.txtIdPostulante3]))
        except ValueError as e:
            VistaError(str(e), self.v_ternas).exec()

    def refrescar_tabla_empresas(self):
        self.repo_empresas.recargar()
        self.pintar_tabla(self.v_empresas.tblEmpresas, self.repo_empresas.listar(), self.fila_empresa)

    def limpiar_form_empresa(self):
        list(map(lambda w: w.clear(), [
            self.v_empresas.txtCedula, self.v_empresas.txtContrasena, self.v_empresas.txtNombres,
            self.v_empresas.txtApellidos, self.v_empresas.txtTelefono, self.v_empresas.txtEmail,
            self.v_empresas.txtCargo, self.v_empresas.txtRUC, self.v_empresas.txtNombreEmpresa,
            self.v_empresas.txtDireccionEmpresa]))

    def slot_registrar_empresa(self):
        try:
            if SincronizadorCredenciales.existe_activo(self.persistencia, self.v_empresas.txtCedula.text().strip()):
                raise ValueError("Ya existe un usuario activo con esa cédula.")
            with self.persistencia.transaccion():
                nuevo = self.repo_empresas.agregar(
                    self.v_empresas.txtCedula.text().strip(),
                    self.v_empresas.txtContrasena.text().strip(),
                    self.v_empresas.txtNombres.text().strip(),
                    self.v_empresas.txtApellidos.text().strip(),
                    self.v_empresas.txtTelefono.text().strip(),
                    self.v_empresas.txtEmail.text().strip(),
                    self.v_empresas.txtCargo.text().strip(),
                    self.v_empresas.txtRUC.text().strip(),
                    self.v_empresas.txtNombreEmpresa.text().strip(),
                    self.v_empresas.txtDireccionEmpresa.text().strip())
                SincronizadorCredenciales.agregar(self.persistencia, nuevo.cedula, nuevo.contrasena, TutorEmpresarial.ROL)
            self.refrescar_tabla_empresas()
            QMessageBox.information(self.v_empresas, "Éxito",
                                    f"Empresa '{nuevo.nombre_empresa}' y su tutor empresarial registrados.")
            self.limpiar_form_empresa()
        except ValueError as e:
            VistaError(str(e), self.v_empresas).exec()

    def slot_eliminar_empresa(self):
        cedula = self.v_empresas.txtEliminarCedula.text().strip()
        try:
            if not cedula:
                raise ValueError("Ingrese la cédula del tutor empresarial a eliminar.")
            empresa = self.repo_empresas.buscar(cedula)
            if empresa is None:
                raise ValueError("No existe un tutor empresarial con la cédula ingresada.")
            if not VistaConfirmacion.confirmar(
                    f"¿Está seguro que desea eliminar a {empresa.nombre_empresa} (cédula {cedula})?", self.v_empresas):
                return
            with self.persistencia.transaccion():
                self.repo_empresas.eliminar(cedula)
                SincronizadorCredenciales.eliminar(self.persistencia, cedula)
                eliminacion_cascada.por_empresa(self.persistencia, cedula, empresa.ruc_empresa)
            self.refrescar_tabla_empresas()
            QMessageBox.information(self.v_empresas, "Éxito",
                                    "Tutor empresarial eliminado. Sus ofertas, postulaciones y prácticas también se dieron de baja.")
            self.v_empresas.txtEliminarCedula.clear()
        except ValueError as e:
            VistaError(str(e), self.v_empresas).exec()

    def prellenar_empresa(self, datos):
        self.limpiar_form_empresa()
        self.v_empresas.txtNombreEmpresa.setText(datos.get("nombre_empresa", ""))
        self.v_empresas.txtRUC.setText(datos.get("ruc_empresa", ""))
        self.v_empresas.txtDireccionEmpresa.setText(datos.get("direccion_empresa", ""))
        self.v_empresas.txtTelefono.setText(datos.get("telefono", ""))
        self.v_empresas.txtEmail.setText(datos.get("email", ""))

    def refrescar_tabla_solicitudes(self):
        self.cargar_datos()
        self.pintar_tabla(self.v_bandeja.tblSolicitudes, self.repo_solicitudes.listar(), self.fila_solicitud)

    def slot_aprobar_solicitud(self):
        try:
            id_solicitud = parsear_id(self.v_bandeja.txtIdSolicitud.text(), "ID de la solicitud")
            solicitud = self.repo_solicitudes.buscar(id_solicitud)
            if solicitud is None:
                raise ValueError(f"No se encontró la solicitud con ID '{id_solicitud}'.")
            if solicitud["estado"] != "Pendiente":
                raise ValueError(f"La solicitud ya fue procesada. Estado actual: {solicitud['estado']}.")
            solicitud["estado"] = "Aprobada"
            self.repo_solicitudes.actualizar(solicitud)
            self.refrescar_tabla_solicitudes()
            self.v_bandeja.txtIdSolicitud.clear()
            if solicitud["tipo"] == self.TIPO_EMPRESA_PROPIA:
                self.refrescar_tabla_empresas()
                self.prellenar_empresa(solicitud.get("datos_empresa") or {})
                self.v_empresas.show()
                QMessageBox.information(self.v_bandeja, "Registrar empresa",
                                        "Solicitud aprobada. Complete y registre la empresa (tutor empresarial).")
            else:
                QMessageBox.information(self.v_bandeja, "Éxito", f"Solicitud {id_solicitud} aprobada.")
        except ValueError as e:
            VistaError(str(e), self.v_bandeja).exec()

    def slot_rechazar_solicitud(self):
        try:
            id_solicitud = parsear_id(self.v_bandeja.txtIdSolicitud.text(), "ID de la solicitud")
            solicitud = self.repo_solicitudes.buscar(id_solicitud)
            if solicitud is None:
                raise ValueError(f"No se encontró la solicitud con ID '{id_solicitud}'.")
            if solicitud["estado"] != "Pendiente":
                raise ValueError(f"La solicitud ya fue procesada. Estado actual: {solicitud['estado']}.")
            solicitud["estado"] = "Rechazada"
            self.repo_solicitudes.actualizar(solicitud)
            self.refrescar_tabla_solicitudes()
            QMessageBox.information(self.v_bandeja, "Éxito", f"Solicitud {id_solicitud} rechazada.")
            self.v_bandeja.txtIdSolicitud.clear()
        except ValueError as e:
            VistaError(str(e), self.v_bandeja).exec()
