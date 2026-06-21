from PyQt6 import QtCore, QtGui, QtWidgets

class VistaConfirmacion(QtWidgets.QDialog):
    def __init__(self, mensaje, parent=None):
        super().__init__(parent)
        self.setObjectName("frmConfirmacion")
        self.setWindowTitle("Confirmar Eliminación")
        self.resize(450, 180)
        self.setModal(True)

        self.lblTitulo = QtWidgets.QLabel("¿Está seguro?", parent=self)
        self.lblTitulo.setGeometry(QtCore.QRect(20, 20, 410, 30))
        self.lblTitulo.setFont(QtGui.QFont("Segoe UI", 14))
        self.lblTitulo.setStyleSheet("color: #D32F2F;")
        self.lblTitulo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.lblMensaje = QtWidgets.QLabel(mensaje, parent=self)
        self.lblMensaje.setGeometry(QtCore.QRect(20, 60, 410, 60))
        self.lblMensaje.setFont(QtGui.QFont("Segoe UI", 11))
        self.lblMensaje.setWordWrap(True)
        self.lblMensaje.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        self.btnAceptar = QtWidgets.QPushButton("Aceptar", parent=self)
        self.btnAceptar.setGeometry(QtCore.QRect(110, 130, 100, 30))
        self.btnAceptar.setFont(QtGui.QFont("Segoe UI", 11))
        self.btnAceptar.setStyleSheet(
            "QPushButton { background-color: #D32F2F; color: white; border: none; border-radius: 5px; }"
            "QPushButton:hover { background-color: #F44336; }"
            "QPushButton:pressed { background-color: #B71C1C; }"
        )
        self.btnAceptar.clicked.connect(self.accept)

        self.btnCancelar = QtWidgets.QPushButton("Cancelar", parent=self)
        self.btnCancelar.setGeometry(QtCore.QRect(240, 130, 100, 30))
        self.btnCancelar.setFont(QtGui.QFont("Segoe UI", 11))
        self.btnCancelar.clicked.connect(self.reject)

    @staticmethod
    def confirmar(mensaje, parent=None):
        return VistaConfirmacion(mensaje, parent).exec() == QtWidgets.QDialog.DialogCode.Accepted.value
