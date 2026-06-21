from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.estudiante import Estudiante, RepositorioEstudiante
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_confirmacion import VistaConfirmacion
from vista.vista_estudiante.interfaz_vista_estudiante import VistaCrudEstudiante
from controlador.sincronizador_credenciales import SincronizadorCredenciales
from controlador import eliminacion_cascada

class ControladorCRUDEstudiante:

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.repo = RepositorioEstudiante(persistencia)
        self.vista = VistaCrudEstudiante()
        self.conectar_signals()

    def iniciar(self):
        self.refrescar_tabla()
        self.vista.show()

    def conectar_signals(self):
        self.vista.btnGuardar.clicked.connect(self.slot_agregar)
        self.vista.btnLimpiar.clicked.connect(self.limpiar)
        self.vista.btnEliminar.clicked.connect(self.slot_eliminar)
        self.vista.btnRefrescar.clicked.connect(self.refrescar_tabla)

    @staticmethod
    def pintar_tabla(tabla, lista, fila_func):
        tabla.setRowCount(len(lista))
        list(map(lambda par: list(map(
            lambda col: tabla.setItem(par[0], col[0], QTableWidgetItem(str(col[1]))),
            enumerate(fila_func(par[1])))), enumerate(lista)))

    @staticmethod
    def fila(e):
        return [e.cedula, e.contrasena, e.apellidos, e.nombres, e.telefono, e.email,
                e.carrera, e.ciclo, e.total_horas_realizadas]

    def refrescar_tabla(self):
        self.repo.recargar()
        self.pintar_tabla(self.vista.tblPersonal, self.repo.listar(), self.fila)

    def limpiar(self):
        list(map(lambda w: w.clear(), [
            self.vista.txtCedula, self.vista.txtContrasena, self.vista.txtApellidos,
            self.vista.txtNombres, self.vista.txtTelefono, self.vista.txtEmail]))
        self.vista.cmbCarrera.setCurrentIndex(0)
        self.vista.spnCiclo.setValue(1)

    def slot_agregar(self):
        try:
            if SincronizadorCredenciales.existe_activo(self.persistencia, self.vista.txtCedula.text().strip()):
                raise ValueError("Ya existe un usuario activo con esa cédula.")
            nuevo = self.repo.agregar(
                self.vista.txtCedula.text().strip(), self.vista.txtContrasena.text().strip(),
                self.vista.txtApellidos.text().strip(), self.vista.txtNombres.text().strip(),
                self.vista.txtTelefono.text().strip(), self.vista.txtEmail.text().strip(),
                self.vista.cmbCarrera.currentText(), self.vista.spnCiclo.value())
            SincronizadorCredenciales.agregar(self.persistencia, nuevo.cedula, nuevo.contrasena, Estudiante.ROL)
            self.refrescar_tabla()
            QMessageBox.information(self.vista, "Éxito", "Estudiante agregado correctamente.")
            self.limpiar()
        except ValueError as e:
            VistaError(str(e), self.vista).exec()

    def slot_eliminar(self):
        cedula = self.vista.txtEliminarCedula.text().strip()
        try:
            estudiante = self.repo.buscar(cedula)
            if estudiante is None:
                raise ValueError("No existe un estudiante registrado con la cédula ingresada.")
            if not VistaConfirmacion.confirmar(
                    f"¿Eliminar al estudiante {estudiante.nombres} {estudiante.apellidos} (cédula {cedula})?", self.vista):
                return
            self.repo.eliminar(cedula)
            SincronizadorCredenciales.eliminar(self.persistencia, cedula)
            eliminacion_cascada.por_estudiante(self.persistencia, cedula)
            self.refrescar_tabla()
            QMessageBox.information(self.vista, "Éxito",
                                    "Estudiante eliminado. Sus postulaciones, prácticas y solicitudes también se dieron de baja.")
            self.vista.txtEliminarCedula.clear()
        except ValueError as e:
            VistaError(str(e), self.vista).exec()
