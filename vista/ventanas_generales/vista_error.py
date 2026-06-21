from PyQt6 import QtCore, QtGui, QtWidgets

class VistaError(QtWidgets.QDialog):
    def __init__(self, mensaje_error, parent=None):
        super().__init__(parent)
        self.setObjectName("frmError")
        self.setWindowTitle("Error del Sistema")
        self.resize(450, 180)
        self.setModal(True)

        self.lblTitulo = QtWidgets.QLabel("¡Atención!", parent=self)
        self.lblTitulo.setGeometry(QtCore.QRect(20, 20, 410, 30))
        font_titulo = QtGui.QFont("Segoe UI", 14)
        self.lblTitulo.setFont(font_titulo)
        self.lblTitulo.setStyleSheet("color: #D32F2F;")
        self.lblTitulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.lblMensaje = QtWidgets.QLabel(mensaje_error, parent=self)
        self.lblMensaje.setGeometry(QtCore.QRect(20, 60, 410, 60))
        font_mensaje = QtGui.QFont("Segoe UI", 11)
        self.lblMensaje.setFont(font_mensaje)
        self.lblMensaje.setWordWrap(True)
        self.lblMensaje.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.btnAceptar = QtWidgets.QPushButton("Aceptar", parent=self)
        self.btnAceptar.setGeometry(QtCore.QRect(175, 130, 100, 30))
        font_boton = QtGui.QFont("Segoe UI", 11)
        self.btnAceptar.setFont(font_boton)

        self.btnAceptar.clicked.connect(self.accept)