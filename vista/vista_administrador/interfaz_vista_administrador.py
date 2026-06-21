from PyQt6 import QtWidgets, QtGui
from vista.vista_administrador.VistaAdministrador import Ui_MainWindow as Ui_VistaAdministrador
from vista.vista_administrador.CrudAdministrador import Ui_CrudAdministrador
from vista.ventanas_generales.rutas_recursos import ruta_recurso
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI


class VistaPrincipalAdministrador(QtWidgets.QMainWindow, Ui_VistaAdministrador):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("General", "Admin.png")))
        self.lblIconoAdmin.setPixmap(QtGui.QPixmap(ruta_recurso("General", "Admin.png")))
        self.actMantenimientoEstudiante.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Principal.png")))
        self.actMantenimientoCoordinador.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.actMantenimientoTutorAcademico.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Validar_Postulacion.png")))
        self.actMantenimientoAdministrador.setIcon(QtGui.QIcon(ruta_recurso("General", "Admin.png")))
        self.actSalir.setIcon(QtGui.QIcon(ruta_recurso("General", "Salir.png")))
        self.actInformacion.setIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        self.actMantenimientoEstudiante.setToolTip("Gestionar estudiantes (agregar, listar y eliminar)")
        self.actMantenimientoTutorAcademico.setToolTip("Gestionar tutores académicos")
        self.actMantenimientoCoordinador.setToolTip("Gestionar coordinadores de vinculación")
        self.actMantenimientoAdministrador.setToolTip("Gestionar administradores")
        self.actInformacion.setToolTip("Acerca del sistema")
        self.actSalir.setToolTip("Cerrar esta ventana")


class VistaCrudAdministrador(QtWidgets.QWidget, Ui_CrudAdministrador):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("General", "Admin.png")))
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPersonal)
