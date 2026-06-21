from PyQt6 import QtWidgets, QtGui
from vista.vista_crud_personal.CrudTutorAcademico import Ui_CrudTutorAcademico
from vista.vista_crud_personal.CrudVinculacion import Ui_CrudVinculacion
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI
from vista.ventanas_generales.rutas_recursos import ruta_recurso


class VistaCrudTutorAcademico(QtWidgets.QWidget, Ui_CrudTutorAcademico):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.txtCedula.setMaxLength(10)
        self.txtEliminarCedula.setMaxLength(10)
        UtilidadesGUI.aplicar_validador_numerico(self.txtCedula)
        UtilidadesGUI.aplicar_validador_numerico(self.txtTelefono)
        UtilidadesGUI.aplicar_validador_numerico(self.txtEliminarCedula)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPersonal)


class VistaCrudVinculacion(QtWidgets.QWidget, Ui_CrudVinculacion):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.txtCedula.setMaxLength(10)
        self.txtEliminarCedula.setMaxLength(10)
        UtilidadesGUI.aplicar_validador_numerico(self.txtCedula)
        UtilidadesGUI.aplicar_validador_numerico(self.txtTelefono)
        UtilidadesGUI.aplicar_validador_numerico(self.txtEliminarCedula)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPersonal)
