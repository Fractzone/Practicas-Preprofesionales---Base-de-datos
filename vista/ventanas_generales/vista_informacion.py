from PyQt6 import QtCore, QtGui, QtWidgets
from vista.ventanas_generales.rutas_recursos import ruta_recurso

class VistaInformacion(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("frmInformacion")
        self.setWindowTitle("Acerca del Sistema")
        self.resize(500, 300)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        self.lblTitulo = QtWidgets.QLabel("Sistema de Gestión de Prácticas Preprofesionales", parent=self)
        self.lblTitulo.setGeometry(QtCore.QRect(20, 20, 460, 30))
        font_titulo = QtGui.QFont("Segoe UI", 14)
        self.lblTitulo.setFont(font_titulo)
        self.lblTitulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.lblInfo = QtWidgets.QLabel(parent=self)
        self.lblInfo.setGeometry(QtCore.QRect(30, 60, 440, 180))
        font_info = QtGui.QFont("Segoe UI", 11)
        self.lblInfo.setFont(font_info)
        self.lblInfo.setWordWrap(True)
        self.lblInfo.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop | QtCore.Qt.AlignmentFlag.AlignHCenter)
        texto_acerca_de = (
            "<b>Sistema:</b> Gestión de Prácticas Preprofesionales<br><br>"
            "<b>Autor:</b> Diego Añazco Salazar<br><br>"
            "<b>Desarrollado para:</b> Universidad de Cuenca<br>"
            "<b>Carrera:</b> Computación<br><br>"
        )
        self.lblInfo.setText(texto_acerca_de)
        self.btnCerrar = QtWidgets.QPushButton("Cerrar", parent=self)
        self.btnCerrar.setGeometry(QtCore.QRect(200, 250, 100, 30))
        self.btnCerrar.setFont(QtGui.QFont("Segoe UI", 11))
        self.btnCerrar.clicked.connect(self.accept)