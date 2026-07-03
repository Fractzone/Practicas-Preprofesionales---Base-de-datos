from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modelo.administrador import Administrador, RepositorioAdministrador
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_confirmacion import VistaConfirmacion
from vista.vista_administrador.interfaz_vista_administrador import VistaCrudAdministrador
from controlador.sincronizador_credenciales import SincronizadorCredenciales

class ControladorCRUDAdministrador:

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.repo = RepositorioAdministrador(persistencia)
        self.vista = VistaCrudAdministrador()
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
    def fila(a):
        # La contraseña se almacena cifrada y no se muestra (buena práctica).
        return [a.usuario, "••••••••", a.email]

    def refrescar_tabla(self):
        self.pintar_tabla(self.vista.tblPersonal, self.repo.listar(), self.fila)

    def limpiar(self):
        list(map(lambda w: w.clear(), [
            self.vista.txtUsuario, self.vista.txtContrasena, self.vista.txtEmail]))

    def slot_agregar(self):
        try:
            if SincronizadorCredenciales.existe_activo(self.persistencia, self.vista.txtUsuario.text().strip()):
                raise ValueError("Ya existe un usuario activo con ese nombre de usuario.")
            with self.persistencia.transaccion():
                nuevo = self.repo.agregar(
                    self.vista.txtUsuario.text().strip(), self.vista.txtContrasena.text().strip(),
                    self.vista.txtEmail.text().strip())
                SincronizadorCredenciales.agregar(self.persistencia, nuevo.usuario, nuevo.contrasena, Administrador.ROL)
            self.refrescar_tabla()
            QMessageBox.information(self.vista, "Éxito", "Administrador agregado correctamente.")
            self.limpiar()
        except ValueError as e:
            VistaError(str(e), self.vista).exec()

    def slot_eliminar(self):
        usuario = self.vista.txtEliminarUsuario.text().strip()
        try:
            administrador = self.repo.buscar(usuario)
            if administrador is None:
                raise ValueError("No existe un administrador registrado con el usuario ingresado.")
            if not VistaConfirmacion.confirmar(
                    f"¿Eliminar al administrador '{usuario}'?", self.vista):
                return
            with self.persistencia.transaccion():
                self.repo.eliminar(usuario)
                SincronizadorCredenciales.eliminar(self.persistencia, usuario)
            self.refrescar_tabla()
            QMessageBox.information(self.vista, "Éxito", "Administrador eliminado correctamente.")
            self.vista.txtEliminarUsuario.clear()
        except ValueError as e:
            VistaError(str(e), self.vista).exec()
