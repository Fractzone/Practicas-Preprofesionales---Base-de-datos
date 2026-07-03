from datetime import datetime
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.proceso import RepositorioOferta, RepositorioPostulacion, RepositorioPractica, Practica, RepositorioSolicitud
from modelo.coordinadores import RepositorioTutorEmpresarial, RepositorioTutorAcademico
from modelo.estudiante import RepositorioEstudiante
from modelo.formulario import RepositorioFormulario1
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_informacion import VistaInformacion
from vista.ventanas_generales.vista_confirmacion import VistaConfirmacion
from controlador.utilidades_controlador import parsear_id
from vista.vista_modulo_estudiante.interfaz_vista_modulo_estudiante import (
    VistaEstudiantePrincipal, VistaBuscarOfertas,
    VistaMisPostulaciones, VistaSolicitudes, VistaFormulario1
)

class ControladorEstudiante:
    TIPO_EMPRESA_PROPIA = "Autorización de Empresa Propia"

    def __init__(self, persistencia, cedula_estudiante):
        self.persistencia = persistencia
        self.cedula_estudiante = cedula_estudiante
        self.repo_ofertas = RepositorioOferta(persistencia)
        self.repo_empresas = RepositorioTutorEmpresarial(persistencia)
        self.repo_academicos = RepositorioTutorAcademico(persistencia)
        self.repo_estudiantes = RepositorioEstudiante(persistencia)
        self.repo_postulaciones = RepositorioPostulacion(persistencia)
        self.repo_formularios1 = RepositorioFormulario1(persistencia)
        self.repo_practicas = RepositorioPractica(persistencia)
        self.repo_solicitudes = RepositorioSolicitud(persistencia)
        self.vista_menu = VistaEstudiantePrincipal()
        self.v_ofertas = VistaBuscarOfertas()
        self.v_postulaciones = VistaMisPostulaciones()
        self.v_solicitudes = VistaSolicitudes()
        self.v_form1 = VistaFormulario1()
        self.conectar_signals()

    def iniciar(self):
        self.vista_menu.show()

    def conectar_signals(self):
        self.vista_menu.actBuscarOferta.triggered.connect(
            lambda: (self.refrescar_tabla_ofertas(), self.v_ofertas.show()))
        self.vista_menu.actPostulaciones.triggered.connect(
            lambda: (self.refrescar_tabla_postulaciones(), self.v_postulaciones.show()))
        self.vista_menu.actFormulario1.triggered.connect(
            lambda: (self.preparar_formulario1(), self.v_form1.show()))
        self.vista_menu.actSolicitarEvaluacion.triggered.connect(self.slot_solicitar_evaluacion)
        self.vista_menu.actSolicitudesEspeciales.triggered.connect(
            lambda: (self.refrescar_tabla_solicitudes(), self.v_solicitudes.show()))
        self.vista_menu.actSalir.triggered.connect(self.vista_menu.close)
        self.vista_menu.actInformacion.triggered.connect(self.slot_mostrar_informacion)

        self.v_ofertas.btnPostular.clicked.connect(self.slot_postular)
        self.v_ofertas.btnRefrescar.clicked.connect(self.refrescar_tabla_ofertas)
        self.v_postulaciones.btnRefrescar.clicked.connect(self.refrescar_tabla_postulaciones)
        self.v_solicitudes.btnEnviarSolicitud.clicked.connect(self.slot_enviar_solicitud)

        self.v_form1.btnCargar.clicked.connect(self.slot_cargar_form1)
        self.v_form1.btnAgregarActividad.clicked.connect(self.slot_agregar_actividad)
        self.v_form1.btnEliminarActividad.clicked.connect(self.slot_eliminar_actividad)
        self.v_form1.btnGuardarFormulario.clicked.connect(self.slot_guardar_form1)
        self.v_form1.btnLimpiar.clicked.connect(self.slot_limpiar_form1)

    def slot_mostrar_informacion(self):
        VistaInformacion(self.vista_menu).exec()

    @staticmethod
    def pintar_tabla(tabla, lista, fila_func):
        tabla.setRowCount(len(lista))
        list(map(lambda par: list(map(
            lambda col: tabla.setItem(par[0], col[0], QTableWidgetItem(str(col[1]))),
            enumerate(fila_func(par[1])))), enumerate(lista)))

    def nombre_empresa(self, oferta):
        empresa = self.repo_empresas.buscar_por_ruc(oferta.ruc_empresa) if oferta else None
        return empresa.nombre_empresa if empresa else "N/A"

    def nombre_persona(self, persona):
        return f"{persona.nombres} {persona.apellidos}" if persona else "N/A"

    def mis_postulaciones_ids(self):
        return list(map(lambda p: p.id_postulacion,
                        self.repo_postulaciones.de_estudiante(self.cedula_estudiante)))

    def practica_activa(self):
        return self.repo_practicas.activa_de_postulaciones(
            self.mis_postulaciones_ids(), Practica.ESTADOS_ACTIVA)

    def fila_oferta(self, d):
        # d proviene de un JOIN (vista_oferta_detalle).
        return [d["id_oferta"], d["nombre_empresa"], d["puesto"],
                d["descripcion"], d["fecha_publicacion"]]

    def fila_postulacion(self, post):
        oferta = self.repo_ofertas.buscar(post.id_oferta)
        return [post.id_postulacion,
                oferta.puesto if oferta else "N/A",
                self.nombre_empresa(oferta),
                post.estado_validacion]

    @staticmethod
    def fila_solicitud(sol):
        return [sol["id"], sol["tipo"], sol["estado"], sol["fecha"]]

    def refrescar_tabla_ofertas(self):
        self.pintar_tabla(self.v_ofertas.tblOfertas, self.repo_ofertas.detalle_disponibles(), self.fila_oferta)

    def refrescar_tabla_postulaciones(self):
        mis = self.repo_postulaciones.de_estudiante(self.cedula_estudiante)
        self.pintar_tabla(self.v_postulaciones.tblMisPostulaciones, mis, self.fila_postulacion)

    def refrescar_tabla_solicitudes(self):
        mis = self.repo_solicitudes.de_estudiante(self.cedula_estudiante)
        self.pintar_tabla(self.v_solicitudes.tblSolicitudes, mis, self.fila_solicitud)

    def slot_postular(self):
        try:
            id_oferta = parsear_id(self.v_ofertas.txtIdOferta.text(), "ID de la oferta")
            oferta = self.repo_ofertas.buscar(id_oferta)
            if not oferta:
                raise ValueError(f"No se encontró la oferta con ID '{id_oferta}'.")
            if self.practica_activa():
                raise ValueError("Ya tiene una práctica activa en curso. No puede postular a nuevas ofertas.")
            if self.repo_postulaciones.tiene_activa_para_oferta(self.cedula_estudiante, id_oferta):
                raise ValueError("Ya tiene una postulación activa para esta oferta.")
            nueva = self.repo_postulaciones.agregar(
                datetime.now().strftime("%d/%m/%Y"), "Pendiente", self.cedula_estudiante, id_oferta, None)
            self.refrescar_tabla_ofertas()
            QMessageBox.information(self.v_ofertas, "Éxito",
                                    f"Postulación registrada exitosamente.\n"
                                    f"ID Postulación: {nueva.id_postulacion}\nOferta: {oferta.puesto}")
            self.v_ofertas.txtIdOferta.clear()
        except ValueError as e:
            VistaError(str(e), self.v_ofertas).exec()

    def slot_enviar_solicitud(self):
        tipo = self.v_solicitudes.cmbTipoSolicitud.currentText()
        motivo = self.v_solicitudes.txaMotivoDetalle.toPlainText().strip()
        datos_empresa = None
        if tipo == self.TIPO_EMPRESA_PROPIA:
            datos_empresa = {
                "nombre_empresa": self.v_solicitudes.txtEmpNombre.text().strip(),
                "ruc_empresa": self.v_solicitudes.txtEmpRuc.text().strip(),
                "direccion_empresa": self.v_solicitudes.txtEmpDireccion.text().strip(),
                "telefono": self.v_solicitudes.txtEmpTelefono.text().strip(),
                "email": self.v_solicitudes.txtEmpEmail.text().strip(),
            }
        try:
            nueva = self.repo_solicitudes.agregar(
                tipo, motivo, self.cedula_estudiante, datetime.now().strftime("%d/%m/%Y"), datos_empresa)
            self.refrescar_tabla_solicitudes()
            QMessageBox.information(self.v_solicitudes, "Éxito",
                                    f"Solicitud enviada correctamente.\nID: {nueva['id']}\n"
                                    f"Tipo: {tipo}\nEstado: Pendiente")
            self.v_solicitudes.txaMotivoDetalle.clear()
        except ValueError as e:
            VistaError(str(e), self.v_solicitudes).exec()

    def cabecera_practica(self, practica):
        post = self.repo_postulaciones.buscar(practica.id_postulacion) if practica else None
        oferta = self.repo_ofertas.buscar(post.id_oferta) if post else None
        estudiante = self.repo_estudiantes.buscar(self.cedula_estudiante)
        empresa = self.repo_empresas.buscar(practica.id_tutor_empresarial) if practica else None
        academico = self.repo_academicos.buscar(practica.id_tutor_academico) if practica else None
        return {
            "empresa": self.nombre_empresa(oferta),
            "estudiante": f"{self.nombre_persona(estudiante)} - {self.cedula_estudiante}",
            "tutor_emp": f"{self.nombre_persona(empresa)} - {empresa.cedula}" if empresa else "N/A",
            "tutor_acad": f"{self.nombre_persona(academico)} - {academico.cedula}" if academico else "N/A",
        }

    def pintar_cabecera_form1(self, practica):
        datos = self.cabecera_practica(practica)
        self.v_form1.lblEmpresaVal.setText(datos["empresa"])
        self.v_form1.lblEstudianteVal.setText(datos["estudiante"])
        self.v_form1.lblTutorEmpVal.setText(datos["tutor_emp"])
        self.v_form1.lblTutorAcadVal.setText(datos["tutor_acad"])

    def preparar_formulario1(self):
        practica = self.practica_activa()
        if practica:
            self.v_form1.txtIdPractica.setText(str(practica.id_practica))
            self.pintar_cabecera_form1(practica)

    def slot_cargar_form1(self):
        try:
            id_practica = parsear_id(self.v_form1.txtIdPractica.text(), "ID de la práctica")
            practica = self.practica_de_estudiante(id_practica)
            self.pintar_cabecera_form1(practica)
        except ValueError as e:
            VistaError(str(e), self.v_form1).exec()

    def practica_de_estudiante(self, id_practica):
        practica = self.repo_practicas.buscar(id_practica)
        if not practica or practica.id_postulacion not in self.mis_postulaciones_ids():
            raise ValueError(f"No se encontró una práctica suya con ID '{id_practica}'.")
        return practica

    def slot_agregar_actividad(self):
        fila = self.v_form1.tblActividades.rowCount()
        self.v_form1.tblActividades.insertRow(fila)

    def slot_eliminar_actividad(self):
        fila = self.v_form1.tblActividades.currentRow()
        if fila >= 0:
            self.v_form1.tblActividades.removeRow(fila)

    def leer_actividades(self):
        tabla = self.v_form1.tblActividades
        def celda(fila, col):
            item = tabla.item(fila, col)
            return item.text().strip() if item else ""
        def actividad(fila):
            horas = celda(fila, 1)
            if not horas.isdigit():
                raise ValueError(f"Las horas de la actividad {fila + 1} deben ser un entero positivo.")
            return {"descripcion": celda(fila, 0), "horas": int(horas),
                    "fecha_inicio": celda(fila, 2), "fecha_final": celda(fila, 3)}
        filas = list(filter(lambda f: any(celda(f, c) for c in range(4)), range(tabla.rowCount())))
        return list(map(actividad, filas))

    def slot_guardar_form1(self):
        try:
            id_practica = parsear_id(self.v_form1.txtIdPractica.text(), "ID de la práctica")
            practica = self.practica_de_estudiante(id_practica)
            if practica.estado != Practica.EN_PROGRESO:
                raise ValueError(
                    "El Formulario 1 solo puede registrarse al inicio de la práctica. "
                    f"Estado actual: {practica.estado}.")
            actividades = self.leer_actividades()
            tipo_documento = "Convenio" if self.v_form1.rbtConvenio.isChecked() else "Carta de Compromiso"
            tipo_practica = "Preprofesional" if self.v_form1.rbtPreprofesional.isChecked() else "Pasantía"
            self.repo_formularios1.agregar(
                id_practica, tipo_documento, self.v_form1.txtNumDocumento.text().strip(), tipo_practica,
                self.v_form1.dspnRemuneracion.value(),
                self.v_form1.dtFechaInicial.date().toString("dd/MM/yyyy"),
                self.v_form1.dtFechaFinal.date().toString("dd/MM/yyyy"),
                self.v_form1.spnHorasAprox.value(), actividades)
            QMessageBox.information(self.v_form1, "Éxito",
                                    "Formulario 1 registrado. Queda pendiente de aprobación del tutor académico.")
            self.v_form1.close()
        except ValueError as e:
            VistaError(str(e), self.v_form1).exec()

    def slot_limpiar_form1(self):
        self.v_form1.txtIdPractica.clear()
        self.v_form1.txtNumDocumento.clear()
        self.v_form1.rbtConvenio.setChecked(True)
        self.v_form1.rbtPreprofesional.setChecked(True)
        self.v_form1.dspnRemuneracion.setValue(0)
        self.v_form1.spnHorasAprox.setValue(0)
        self.v_form1.dtFechaInicial.setDate(QDate.currentDate())
        self.v_form1.dtFechaFinal.setDate(QDate.currentDate())
        self.v_form1.tblActividades.setRowCount(0)
        list(map(lambda lbl: lbl.clear(),
                 [self.v_form1.lblEmpresaVal, self.v_form1.lblEstudianteVal,
                  self.v_form1.lblTutorEmpVal, self.v_form1.lblTutorAcadVal]))

    def slot_solicitar_evaluacion(self):
        try:
            practica = self.practica_activa()
            if not practica:
                raise ValueError("No tiene una práctica activa.")
            if practica.estado != Practica.EN_EJECUCION:
                raise ValueError(
                    "Solo puede solicitar la evaluación final cuando su práctica está en ejecución "
                    f"(Formulario 1 aprobado). Estado actual: {practica.estado}.")
            if not VistaConfirmacion.confirmar(
                    "¿Confirma que ha finalizado sus horas y desea solicitar la evaluación final?",
                    self.vista_menu):
                return
            practica.estado = Practica.EVALUACION_SOLICITADA
            self.repo_practicas.actualizar(practica)
            QMessageBox.information(self.vista_menu, "Éxito",
                                    "Evaluación final solicitada. El tutor empresarial será notificado.")
        except ValueError as e:
            VistaError(str(e), self.vista_menu).exec()
