from datetime import datetime
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.coordinadores import RepositorioTutorAcademico, RepositorioTutorEmpresarial
from modelo.estudiante import RepositorioEstudiante
from modelo.proceso import RepositorioPostulacion, RepositorioOferta, RepositorioPractica, Practica
from modelo.formulario import RepositorioFormulario1, RepositorioFormulario2, RepositorioFormulario3
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_informacion import VistaInformacion
from vista.ventanas_generales.vista_confirmacion import VistaConfirmacion
from vista.vista_modulo_tutor_academico.interfaz_vista_modulo_tutor_academico import (
    VistaTutorAcademicoPrincipal, VistaAprobarFormulario1, VistaFormulario3,
    VistaListarPracticasActivas
)

class ControladorTutorAcademico:

    def __init__(self, persistencia, cedula_academico):
        self.persistencia = persistencia
        self.cedula_academico = cedula_academico
        self.repo_academicos = RepositorioTutorAcademico(persistencia)
        self.repo_empresas = RepositorioTutorEmpresarial(persistencia)
        self.repo_estudiantes = RepositorioEstudiante(persistencia)
        self.repo_postulaciones = RepositorioPostulacion(persistencia)
        self.repo_ofertas = RepositorioOferta(persistencia)
        self.repo_practicas = RepositorioPractica(persistencia)
        self.repo_formularios1 = RepositorioFormulario1(persistencia)
        self.repo_formularios2 = RepositorioFormulario2(persistencia)
        self.repo_formularios3 = RepositorioFormulario3(persistencia)
        self.vista_menu = VistaTutorAcademicoPrincipal()
        self.v_aprobar = VistaAprobarFormulario1()
        self.v_form3 = VistaFormulario3()
        self.v_practicas = VistaListarPracticasActivas()
        self.conectar_signals()

    def iniciar(self):
        self.vista_menu.show()

    def cargar_datos(self):
        self.repo_academicos.recargar()
        self.repo_empresas.recargar()
        self.repo_estudiantes.recargar()
        self.repo_postulaciones.recargar()
        self.repo_ofertas.recargar()
        self.repo_practicas.recargar()
        self.repo_formularios1.recargar()
        self.repo_formularios2.recargar()
        self.repo_formularios3.recargar()

    def conectar_signals(self):
        self.vista_menu.actAprobarF1.triggered.connect(
            lambda: (self.refrescar_tabla_pendientes(), self.v_aprobar.show()))
        self.vista_menu.actFormulario3.triggered.connect(self.v_form3.show)
        self.vista_menu.actListarPracticas.triggered.connect(
            lambda: (self.refrescar_practicas_activas(), self.v_practicas.show()))
        self.vista_menu.actSalir.triggered.connect(self.vista_menu.close)
        self.vista_menu.actInformacion.triggered.connect(self.slot_mostrar_informacion)

        self.v_aprobar.btnVerDetalle.clicked.connect(self.slot_ver_detalle)
        self.v_aprobar.btnAprobar.clicked.connect(self.slot_aprobar_f1)
        self.v_aprobar.btnRefrescar.clicked.connect(self.refrescar_tabla_pendientes)

        self.v_form3.btnCargar.clicked.connect(self.slot_cargar_form3)
        self.v_practicas.btnRefrescar.clicked.connect(self.refrescar_practicas_activas)

        self.v_form3.btnGuardarFormulario3.clicked.connect(self.slot_guardar_form3)
        self.v_form3.btnAsentarNota.clicked.connect(self.slot_asentar_nota)
        self.v_form3.btnLimpiar.clicked.connect(self.slot_limpiar_form3)

    def slot_mostrar_informacion(self):
        VistaInformacion(self.vista_menu).exec()

    @staticmethod
    def pintar_tabla(tabla, lista, fila_func):
        tabla.setRowCount(len(lista))
        list(map(lambda par: list(map(
            lambda col: tabla.setItem(par[0], col[0], QTableWidgetItem(str(col[1]))),
            enumerate(fila_func(par[1])))), enumerate(lista)))

    def nombre_persona(self, persona):
        return f"{persona.nombres} {persona.apellidos}" if persona else "N/A"

    def estudiante_de_practica(self, practica):
        post = self.repo_postulaciones.buscar(practica.id_postulacion) if practica else None
        return self.repo_estudiantes.buscar(post.cedula_estudiante) if post else None

    def empresa_de_practica(self, practica):
        return self.repo_empresas.buscar(practica.id_tutor_empresarial) if practica else None

    def practicas_en_estado(self, estados):
        return self.repo_practicas.en_estados(estados)

    def fila_pendiente(self, par):
        practica, formulario = par
        estudiante = self.estudiante_de_practica(practica)
        empresa = self.empresa_de_practica(practica)
        return [practica.id_practica, self.nombre_persona(estudiante),
                empresa.nombre_empresa if empresa else "N/A",
                formulario.tipo_practica, str(formulario.horas_aprox), formulario.estado_aprobacion]

    def pendientes_f1(self):
        practicas = self.practicas_en_estado([Practica.EN_PROGRESO])
        pares = map(lambda pr: (pr, self.repo_formularios1.buscar_por_practica(pr.id_practica)), practicas)
        return list(filter(lambda par: par[1] is not None and par[1].estado_aprobacion == "Pendiente", pares))

    def refrescar_tabla_pendientes(self):
        self.cargar_datos()
        self.pintar_tabla(self.v_aprobar.tblPendientes, self.pendientes_f1(), self.fila_pendiente)

    def fila_practica(self, practica):
        estudiante = self.estudiante_de_practica(practica)
        empresa = self.empresa_de_practica(practica)
        return [practica.id_practica, self.nombre_persona(estudiante),
                empresa.nombre_empresa if empresa else "N/A",
                practica.estado, practica.fecha_inicio]

    def refrescar_practicas_activas(self):
        self.cargar_datos()
        activas = self.practicas_en_estado(Practica.ESTADOS_ACTIVA)
        self.pintar_tabla(self.v_practicas.tblPracticas, activas, self.fila_practica)

    def buscar_practica(self, id_practica):
        practica = self.repo_practicas.buscar(id_practica)
        if not practica:
            raise ValueError(f"No se encontró la práctica con ID '{id_practica}'.")
        return practica

    def slot_ver_detalle(self):
        self.cargar_datos()
        id_practica = self.v_aprobar.txtIdPractica.text().strip()
        try:
            practica = self.buscar_practica(id_practica)
            f1 = self.repo_formularios1.buscar_por_practica(id_practica)
            if not f1:
                raise ValueError("La práctica no tiene un Formulario 1 registrado.")
            actividades = "\n".join(map(
                lambda a: f"  - {a['descripcion']} | {a['horas']}h | {a['fecha_inicio']} a {a['fecha_final']}",
                f1.actividades))
            detalle = (f"Documento: {f1.tipo_documento} N° {f1.numero_documento}\n"
                       f"Tipo de práctica: {f1.tipo_practica}\n"
                       f"Remuneración: {f1.remuneracion}\n"
                       f"Periodo: {f1.fecha_inicial} a {f1.fecha_final_aprox}  |  Horas: {f1.horas_aprox}\n"
                       f"Estado: {f1.estado_aprobacion}\n\nActividades:\n{actividades}")
            self.v_aprobar.txaDetalle.setPlainText(detalle)
        except ValueError as e:
            VistaError(str(e), self.v_aprobar).exec()

    def slot_aprobar_f1(self):
        id_practica = self.v_aprobar.txtIdPractica.text().strip()
        try:
            practica = self.buscar_practica(id_practica)
            f1 = self.repo_formularios1.buscar_por_practica(id_practica)
            if not f1:
                raise ValueError("La práctica no tiene un Formulario 1 registrado.")
            if f1.estado_aprobacion != "Pendiente":
                raise ValueError(f"El Formulario 1 ya fue procesado. Estado: {f1.estado_aprobacion}.")
            f1.estado_aprobacion = "Aprobado"
            self.repo_formularios1.guardar()
            practica.estado = Practica.EN_EJECUCION
            self.repo_practicas.guardar()
            self.refrescar_tabla_pendientes()
            QMessageBox.information(self.v_aprobar, "Éxito",
                                    f"Formulario 1 aprobado. La práctica {id_practica} pasa a 'En Ejecución'.")
            self.v_aprobar.txtIdPractica.clear()
            self.v_aprobar.txaDetalle.clear()
        except ValueError as e:
            VistaError(str(e), self.v_aprobar).exec()

    def slot_cargar_form3(self):
        self.cargar_datos()
        id_practica = self.v_form3.txtIdPractica.text().strip()
        try:
            practica = self.buscar_practica(id_practica)
            if practica.estado != Practica.PENDIENTE_NOTA:
                raise ValueError(
                    "El Formulario 3 solo se llena cuando la evaluación empresarial está completa "
                    f"(estado 'Pendiente Nota'). Estado actual: {practica.estado}.")
            estudiante = self.estudiante_de_practica(practica)
            empresa = self.empresa_de_practica(practica)
            academico = self.repo_academicos.buscar(self.cedula_academico)
            f2 = self.repo_formularios2.buscar_por_practica(id_practica)
            self.v_form3.lblEstudianteVal.setText(self.nombre_persona(estudiante))
            self.v_form3.lblEmpresaVal.setText(empresa.nombre_empresa if empresa else "N/A")
            self.v_form3.lblTutorAcadVal.setText(self.nombre_persona(academico))
            self.v_form3.lblCarreraVal.setText(estudiante.carrera if estudiante else "N/A")
            if f2:
                self.v_form3.lblFechasHorasVal.setText(
                    f"{f2.fecha_real_inicio} a {f2.fecha_real_fin}  |  {f2.horas_cumplidas} horas")
            else:
                self.v_form3.lblFechasHorasVal.setText("N/A")
        except ValueError as e:
            VistaError(str(e), self.v_form3).exec()

    def slot_guardar_form3(self):
        id_practica = self.v_form3.txtIdPractica.text().strip()
        try:
            practica = self.buscar_practica(id_practica)
            if practica.estado != Practica.PENDIENTE_NOTA:
                raise ValueError(f"No es posible evaluar. Estado actual de la práctica: {practica.estado}.")
            self.repo_formularios3.agregar(
                id_practica,
                self.v_form3.txtCampoOcupacional.text().strip(),
                self.v_form3.spnCalificacion.value(),
                self.v_form3.evaluacion())
            QMessageBox.information(self.v_form3, "Éxito",
                                    "Formulario 3 guardado. Ya puede asentar la nota para cerrar la práctica.")
        except ValueError as e:
            VistaError(str(e), self.v_form3).exec()

    def slot_asentar_nota(self):
        id_practica = self.v_form3.txtIdPractica.text().strip()
        try:
            practica = self.buscar_practica(id_practica)
            if practica.estado != Practica.PENDIENTE_NOTA:
                raise ValueError(f"La práctica no está lista para cierre. Estado: {practica.estado}.")
            f3 = self.repo_formularios3.buscar_por_practica(id_practica)
            if not f3:
                raise ValueError("Debe guardar primero el Formulario 3.")
            if not VistaConfirmacion.confirmar(
                    f"¿Confirma asentar la nota {f3.calificacion_sobre_100}/100 y cerrar la práctica?",
                    self.v_form3):
                return
            practica.estado = Practica.FINALIZADA
            practica.fecha_fin = datetime.now().strftime("%d/%m/%Y")
            self.repo_practicas.guardar()
            self.acreditar_practica(practica)
            QMessageBox.information(self.v_form3, "Éxito",
                                    f"Nota asentada. Práctica {id_practica} finalizada y aprobada.")
            self.v_form3.txtIdPractica.clear()
        except ValueError as e:
            VistaError(str(e), self.v_form3).exec()

    def slot_limpiar_form3(self):
        self.v_form3.txtIdPractica.clear()
        self.v_form3.txtCampoOcupacional.clear()
        self.v_form3.spnCalificacion.setValue(0)
        list(map(lambda check: check.setChecked(False), self.v_form3.checks_rubrica))
        list(map(lambda combo: combo.setCurrentIndex(0), self.v_form3.combos_rubrica))
        list(map(lambda lbl: lbl.clear(),
                 [self.v_form3.lblEstudianteVal, self.v_form3.lblEmpresaVal,
                  self.v_form3.lblTutorAcadVal, self.v_form3.lblCarreraVal,
                  self.v_form3.lblFechasHorasVal]))

    def acreditar_practica(self, practica):
        estudiante = self.estudiante_de_practica(practica)
        if estudiante:
            estudiante.num_practicas_realizadas = estudiante.num_practicas_realizadas + 1
            formulario2 = self.repo_formularios2.buscar_por_practica(practica.id_practica)
            if formulario2:
                estudiante.total_horas_realizadas = estudiante.total_horas_realizadas + formulario2.horas_cumplidas
            self.repo_estudiantes.guardar()
