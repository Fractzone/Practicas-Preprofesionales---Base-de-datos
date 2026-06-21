from PyQt6.QtGui import QRegularExpressionValidator, QFont
from PyQt6.QtCore import QRegularExpression

class UtilidadesGUI:

    @staticmethod
    def configurar_app(app):
        app.setStyle("Fusion")
        app.setPalette(app.style().standardPalette())
        app.setFont(QFont("Segoe UI", 11))

    @staticmethod
    def aplicar_validador_numerico(*campos, max_longitud=10):
        regex = QRegularExpression(f"^\\d{{1,{max_longitud}}}$")
        validador = QRegularExpressionValidator(regex)
        list(map(lambda campo: campo.setValidator(validador), campos))

    @staticmethod
    def aplicar_fuente_tabla(*tablas, tam=10):
        fuente = QFont("Segoe UI", tam)
        list(map(lambda tabla: (tabla.setFont(fuente),
                                tabla.horizontalHeader().setFont(fuente)), tablas))

    @staticmethod
    def centrar(ventana):
        pantalla = ventana.screen()
        if pantalla is not None:
            geo = ventana.frameGeometry()
            geo.moveCenter(pantalla.availableGeometry().center())
            ventana.move(geo.topLeft())
