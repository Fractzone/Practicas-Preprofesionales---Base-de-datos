import sys
from PyQt6.QtWidgets import QApplication
from persistencia.gestor_persistencia import GestorPersistencia
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI
from controlador.controlador_login import ControladorLogin

if __name__ == "__main__":
    app = QApplication(sys.argv)
    UtilidadesGUI.configurar_app(app)
    GestorPersistencia.inicializar_datos_si_vacio()
    controlador_login = ControladorLogin(GestorPersistencia())
    controlador_login.iniciar()
    sys.exit(app.exec())
