from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.coordinadores import CoordinadorVinculacion, RepositorioCoordinadorVinculacion
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_confirmacion import VistaConfirmacion
from vista.vista_crud_personal.interfaz_vista_crud_personal import VistaCrudVinculacion
from controlador.sincronizador_credenciales import SincronizadorCredenciales

class ControladorCRUDVinculacion:

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.repo = RepositorioCoordinadorVinculacion(persistencia)
        self.vista = VistaCrudVinculacion()
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
    def fila(c):
        return [c.cedula, c.nombres, c.apellidos, c.telefono, c.email, c.direccion, c.carrera]

    def refrescar_tabla(self):
        self.repo.recargar()
        self.pintar_tabla(self.vista.tblPersonal, self.repo.listar(), self.fila)

    def limpiar(self):
        list(map(lambda w: w.clear(), [
            self.vista.txtCedula, self.vista.txtContrasena, self.vista.txtNombres,
            self.vista.txtApellidos, self.vista.txtTelefono, self.vista.txtEmail,
            self.vista.txtDireccion]))
        self.vista.cmbCarrera.setCurrentIndex(0)

    def slot_agregar(self):
        try:
            if SincronizadorCredenciales.existe_activo(self.persistencia, self.vista.txtCedula.text().strip()):
                raise ValueError("Ya existe un usuario activo con esa cédula.")
            with self.persistencia.transaccion():
                nuevo = self.repo.agregar(
                    self.vista.txtCedula.text().strip(), self.vista.txtContrasena.text().strip(),
                    self.vista.txtNombres.text().strip(), self.vista.txtApellidos.text().strip(),
                    self.vista.txtTelefono.text().strip(), self.vista.txtEmail.text().strip(),
                    self.vista.dtFechaNacimiento.date().toString("dd/MM/yyyy"),
                    self.vista.txtDireccion.text().strip(), self.vista.cmbCarrera.currentText())
                SincronizadorCredenciales.agregar(self.persistencia, nuevo.cedula, nuevo.contrasena, CoordinadorVinculacion.ROL)
            self.refrescar_tabla()
            QMessageBox.information(self.vista, "Éxito", "Coordinador de vinculación agregado correctamente.")
            self.limpiar()
        except ValueError as e:
            VistaError(str(e), self.vista).exec()

    def slot_eliminar(self):
        cedula = self.vista.txtEliminarCedula.text().strip()
        try:
            coord = self.repo.buscar(cedula)
            if coord is None:
                raise ValueError("No existe un coordinador de vinculación con la cédula ingresada.")
            if not VistaConfirmacion.confirmar(
                    f"¿Eliminar al coordinador {coord.nombres} {coord.apellidos} (cédula {cedula})?", self.vista):
                return
            with self.persistencia.transaccion():
                self.repo.eliminar(cedula)
                SincronizadorCredenciales.eliminar(self.persistencia, cedula)
            self.refrescar_tabla()
            QMessageBox.information(self.vista, "Éxito", "Coordinador de vinculación eliminado correctamente.")
            self.vista.txtEliminarCedula.clear()
        except ValueError as e:
            VistaError(str(e), self.vista).exec()
