from PyQt6 import QtWidgets, QtGui
from vista.vista_login.LoginPrincipal import Ui_MainWindow
from vista.ventanas_generales.rutas_recursos import ruta_recurso


class VistaLogin(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("General", "Logo.png")))
        self.actSalir.setIcon(QtGui.QIcon(ruta_recurso("General", "Salir.png")))
        self.actInfo.setIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        list(map(self._aplicar_sombra, [self.txtUsuario, self.txtContrasena, self.btnIngresar]))

    @staticmethod
    def _aplicar_sombra(widget):
        sombra = QtWidgets.QGraphicsDropShadowEffect(widget)
        sombra.setBlurRadius(10)
        sombra.setOffset(0, 2)
        sombra.setColor(QtGui.QColor(0, 0, 0, 55))
        widget.setGraphicsEffect(sombra)
