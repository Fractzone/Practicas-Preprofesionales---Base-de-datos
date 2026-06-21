from PyQt6 import QtWidgets, QtGui
from vista.vista_estudiante.CrudEstudiante import Ui_CrudEstudiante
from vista.ventanas_generales.rutas_recursos import ruta_recurso
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI


class VistaCrudEstudiante(QtWidgets.QWidget, Ui_CrudEstudiante):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Principal.png")))
        self.txtCedula.setMaxLength(10)
        self.txtEliminarCedula.setMaxLength(10)
        UtilidadesGUI.aplicar_validador_numerico(self.txtCedula)
        UtilidadesGUI.aplicar_validador_numerico(self.txtTelefono)
        UtilidadesGUI.aplicar_validador_numerico(self.txtEliminarCedula)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPersonal)
