from datetime import datetime
from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.coordinadores import RepositorioTutorEmpresarial, RepositorioTutorAcademico
from modelo.proceso import RepositorioOferta, RepositorioPostulacion, RepositorioPractica, Practica
from modelo.estudiante import RepositorioEstudiante
from modelo.formulario import RepositorioFormulario2
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_informacion import VistaInformacion
from controlador.utilidades_controlador import parsear_id
from vista.vista_modulo_tutor_empresarial.interfaz_vista_modulo_tutor_empresarial import (
    VistaTutorEmpresarialPrincipal, VistaCrearOferta, VistaRecibirTernas, VistaFormulario2,
    VistaListarPracticasActivas
)

class ControladorTutorEmpresarial:

    def __init__(self, persistencia, cedula_tutor):
        self.persistencia = persistencia
        self.cedula_tutor = cedula_tutor
        self.repo_empresas = RepositorioTutorEmpresarial(persistencia)
        self.repo_academicos = RepositorioTutorAcademico(persistencia)
        self.repo_ofertas = RepositorioOferta(persistencia)
        self.repo_postulaciones = RepositorioPostulacion(persistencia)
        self.repo_estudiantes = RepositorioEstudiante(persistencia)
        self.repo_practicas = RepositorioPractica(persistencia)
        self.repo_formularios2 = RepositorioFormulario2(persistencia)
        self.vista_menu = VistaTutorEmpresarialPrincipal()
        self.v_ofertas = VistaCrearOferta()
        self.v_ternas = VistaRecibirTernas()
        self.v_form2 = VistaFormulario2()
        self.v_practicas = VistaListarPracticasActivas()
        self.conectar_signals()

    def iniciar(self):
        self.vista_menu.show()

    def cargar_datos(self):
        self.repo_empresas.recargar()
        self.repo_academicos.recargar()
        self.repo_ofertas.recargar()
        self.repo_postulaciones.recargar()
        self.repo_estudiantes.recargar()
        self.repo_practicas.recargar()
        self.repo_formularios2.recargar()

    def mi_perfil(self):
        return self.repo_empresas.buscar(self.cedula_tutor)

    def conectar_signals(self):
        self.vista_menu.actCrearOferta.triggered.connect(
            lambda: (self.preparar_ofertas(), self.v_ofertas.show()))
        self.vista_menu.actRecibirTernas.triggered.connect(
            lambda: (self.refrescar_tabla_ternas(), self.v_ternas.show()))
        self.vista_menu.actFormulario2.triggered.connect(self.v_form2.show)
        self.vista_menu.actListarPracticas.triggered.connect(
            lambda: (self.refrescar_practicas_activas(), self.v_practicas.show()))
        self.vista_menu.actSalir.triggered.connect(self.vista_menu.close)
        self.vista_menu.actInformacion.triggered.connect(self.slot_mostrar_informacion)

        self.v_ofertas.btnCrearOferta.clicked.connect(self.slot_crear_oferta)
        self.v_ternas.btnAceptarEstudiante.clicked.connect(self.slot_aceptar_estudiante)
        self.v_ternas.btnRefrescarAceptar.clicked.connect(self.refrescar_tabla_ternas)
        self.v_form2.btnCargar.clicked.connect(self.slot_cargar_form2)
        self.v_form2.btnGuardarEvaluacion.clicked.connect(self.slot_guardar_form2)
        self.v_form2.btnLimpiar.clicked.connect(self.slot_limpiar_form2)
        self.v_practicas.btnRefrescar.clicked.connect(self.refrescar_practicas_activas)

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

    def fila_oferta(self, of):
        perfil = self.mi_perfil()
        return [of.id_oferta, perfil.nombre_empresa if perfil else "N/A", of.puesto,
                of.descripcion, of.fecha_publicacion]

    def fila_terna(self, post):
        estudiante = self.repo_estudiantes.buscar(post.cedula_estudiante)
        oferta = self.repo_ofertas.buscar(post.id_oferta)
        return [post.id_postulacion, self.nombre_completo(estudiante),
                str(estudiante.ciclo) if estudiante else "N/A",
                oferta.puesto if oferta else "N/A", post.estado_validacion]

    def estudiante_de_practica(self, practica):
        post = self.repo_postulaciones.buscar(practica.id_postulacion) if practica else None
        return self.repo_estudiantes.buscar(post.cedula_estudiante) if post else None

    def fila_practica_activa(self, d):
        # d proviene de un JOIN (vista_practica_detalle).
        academico = f'{d["acad_nombres"]} {d["acad_apellidos"]}' if d["acad_nombres"] else "N/A"
        return [d["id_practica"], f'{d["est_nombres"]} {d["est_apellidos"]}',
                academico, d["estado"], d["fecha_inicio"]]

    def refrescar_practicas_activas(self):
        activas = self.repo_practicas.detalle_por_tutor_empresarial(self.cedula_tutor, Practica.ESTADOS_ACTIVA)
        self.pintar_tabla(self.v_practicas.tblPracticas, activas, self.fila_practica_activa)

    def preparar_ofertas(self):
        self.cargar_datos()
        perfil = self.mi_perfil()
        self.v_ofertas.lblEmpresaNombre.setText(perfil.nombre_empresa if perfil else "N/A")
        self.refrescar_tabla_ofertas()

    def refrescar_tabla_ofertas(self):
        perfil = self.mi_perfil()
        mis = self.repo_ofertas.de_empresa(perfil.ruc_empresa) if perfil else []
        self.pintar_tabla(self.v_ofertas.tblOfertas, mis, self.fila_oferta)

    def slot_crear_oferta(self):
        perfil = self.mi_perfil()
        puesto = self.v_ofertas.txtPuesto.text().strip()
        descripcion = self.v_ofertas.txaDescripcion.toPlainText().strip()
        try:
            if perfil is None:
                raise ValueError("No se encontró el perfil de empresa del tutor.")
            nueva = self.repo_ofertas.agregar(
                descripcion, puesto, datetime.now().strftime("%d/%m/%Y"), perfil.ruc_empresa)
            self.refrescar_tabla_ofertas()
            QMessageBox.information(self.v_ofertas, "Éxito",
                                    f"Oferta '{puesto}' creada con ID: {nueva.id_oferta}.")
            self.v_ofertas.txtPuesto.clear()
            self.v_ofertas.txaDescripcion.clear()
        except ValueError as e:
            VistaError(str(e), self.v_ofertas).exec()

    def refrescar_tabla_ternas(self):
        self.cargar_datos()
        perfil = self.mi_perfil()
        rucs = perfil.ruc_empresa if perfil else None
        enviadas = list(filter(
            lambda p: self._oferta_es_mia(p, rucs),
            self.repo_postulaciones.por_estado("Enviada")))
        self.pintar_tabla(self.v_ternas.tblTernasEnviadas, enviadas, self.fila_terna)

    def _oferta_es_mia(self, postulacion, ruc):
        oferta = self.repo_ofertas.buscar(postulacion.id_oferta)
        return oferta is not None and oferta.ruc_empresa == ruc

    def slot_aceptar_estudiante(self):
        try:
            id_post = parsear_id(self.v_ternas.txtIdPostulacionAceptar.text(), "ID de la postulación")
            postulacion = self.repo_postulaciones.buscar(id_post)
            if not postulacion:
                raise ValueError(f"No se encontró la postulación '{id_post}'.")
            perfil = self.mi_perfil()
            if not self._oferta_es_mia(postulacion, perfil.ruc_empresa if perfil else None):
                raise ValueError("La postulación no corresponde a una oferta de su empresa.")
            if postulacion.estado_validacion != "Enviada":
                raise ValueError(f"La postulación no está en estado 'Enviada'. Estado: {postulacion.estado_validacion}.")
            estudiante = self.repo_estudiantes.buscar(postulacion.cedula_estudiante)
            academico = self.asignar_academico(estudiante)
            postulacion.estado_validacion = "Aceptada"
            with self.persistencia.transaccion():
                self.repo_postulaciones.actualizar(postulacion)
                nueva = self.repo_practicas.agregar(
                    datetime.now().strftime("%d/%m/%Y"), "", Practica.EN_PROGRESO,
                    postulacion.id_postulacion,
                    academico.cedula if academico else None, self.cedula_tutor)
            self.refrescar_tabla_ternas()
            aviso = f"Estudiante aceptado. Práctica creada con ID: {nueva.id_practica}."
            if academico is None:
                aviso += "\nAdvertencia: no hay ningún tutor académico registrado."
            QMessageBox.information(self.v_ternas, "Éxito", aviso)
            self.v_ternas.txtIdPostulacionAceptar.clear()
        except ValueError as e:
            VistaError(str(e), self.v_ternas).exec()

    def asignar_academico(self, estudiante):
        if not estudiante:
            return None
        academico = self.repo_academicos.por_carrera(estudiante.carrera)
        if academico is not None:
            return academico
        disponibles = self.repo_academicos.listar()
        return disponibles[0] if disponibles else None

    def slot_cargar_form2(self):
        self.cargar_datos()
        try:
            id_practica = parsear_id(self.v_form2.txtIdPractica.text(), "ID de la práctica")
            practica = self.repo_practicas.buscar(id_practica)
            if not practica:
                raise ValueError(f"No se encontró la práctica con ID '{id_practica}'.")
            if practica.id_tutor_empresarial != self.cedula_tutor:
                raise ValueError("Esta práctica no está asignada a su empresa.")
            if practica.estado != Practica.EVALUACION_SOLICITADA:
                raise ValueError(
                    "El Formulario 2 solo se puede llenar cuando el estudiante ha solicitado "
                    f"la evaluación final. Estado actual: {practica.estado}.")
            post = self.repo_postulaciones.buscar(practica.id_postulacion)
            estudiante = self.repo_estudiantes.buscar(post.cedula_estudiante) if post else None
            perfil = self.mi_perfil()
            self.v_form2.lblEstudianteVal.setText(self.nombre_completo(estudiante))
            self.v_form2.lblEmpresaVal.setText(perfil.nombre_empresa if perfil else "N/A")
            self.v_form2.lblTutorVal.setText(f"{perfil.nombres} {perfil.apellidos}" if perfil else "N/A")
            self.v_form2.lblCargoTelVal.setText(f"{perfil.cargo} / {perfil.telefono}" if perfil else "N/A")
        except ValueError as e:
            VistaError(str(e), self.v_form2).exec()

    def slot_limpiar_form2(self):
        self.v_form2.txtIdPractica.clear()
        self.v_form2.dtFechaRealInicio.setDate(QDate.currentDate())
        self.v_form2.dtFechaRealFin.setDate(QDate.currentDate())
        self.v_form2.spnHorasCumplidas.setValue(0)
        list(map(lambda combo: combo.setCurrentIndex(0), self.v_form2.combos_rubrica))
        self.v_form2.txaProductosRelevantes.clear()
        self.v_form2.txaAspectosRelevantes.clear()
        list(map(lambda lbl: lbl.clear(),
                 [self.v_form2.lblEstudianteVal, self.v_form2.lblEmpresaVal,
                  self.v_form2.lblTutorVal, self.v_form2.lblCargoTelVal]))

    def slot_guardar_form2(self):
        try:
            id_practica = parsear_id(self.v_form2.txtIdPractica.text(), "ID de la práctica")
            practica = self.repo_practicas.buscar(id_practica)
            if not practica:
                raise ValueError(f"No se encontró la práctica con ID '{id_practica}'.")
            if practica.id_tutor_empresarial != self.cedula_tutor:
                raise ValueError("Esta práctica no está asignada a su empresa.")
            if practica.estado != Practica.EVALUACION_SOLICITADA:
                raise ValueError(f"No es posible evaluar. Estado actual de la práctica: {practica.estado}.")
            practica.estado = Practica.PENDIENTE_NOTA
            with self.persistencia.transaccion():
                self.repo_formularios2.agregar(
                    id_practica,
                    self.v_form2.dtFechaRealInicio.date().toString("dd/MM/yyyy"),
                    self.v_form2.dtFechaRealFin.date().toString("dd/MM/yyyy"),
                    self.v_form2.spnHorasCumplidas.value(),
                    self.v_form2.calificaciones(),
                    self.v_form2.txaProductosRelevantes.toPlainText().strip(),
                    self.v_form2.txaAspectosRelevantes.toPlainText().strip())
                self.repo_practicas.actualizar(practica)
            QMessageBox.information(self.v_form2, "Éxito",
                                    "Formulario 2 guardado. La práctica pasa a 'Pendiente Nota'.")
            self.v_form2.txtIdPractica.clear()
            self.v_form2.txaProductosRelevantes.clear()
            self.v_form2.txaAspectosRelevantes.clear()
        except ValueError as e:
            VistaError(str(e), self.v_form2).exec()
