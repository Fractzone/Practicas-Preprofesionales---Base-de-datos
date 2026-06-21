from PyQt6 import QtWidgets, QtGui
from vista.vista_modulo_coordinador_vinculacion.VistaCoordinadorVinculacionPrincipal import Ui_frmVinculacion
from vista.vista_modulo_coordinador_vinculacion.ValidarPostulaciones import Ui_ValidarPostulaciones
from vista.vista_modulo_coordinador_vinculacion.ArmarTernas import Ui_ArmarTernas
from vista.vista_modulo_coordinador_vinculacion.GestionarEmpresas import Ui_GestionarEmpresas
from vista.vista_modulo_coordinador_vinculacion.BandejaSolicitudes import Ui_BandejaSolicitudes
from vista.vista_modulo_coordinador_vinculacion.ListarEstudiantes import Ui_ListarEstudiantes
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI
from vista.ventanas_generales.rutas_recursos import ruta_recurso


class VistaCoordinadorVinculacionPrincipal(QtWidgets.QMainWindow, Ui_frmVinculacion):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.lblImagen.setPixmap(QtGui.QPixmap(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.actValidarPostulacion.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Validar_Postulacion.png")))
        self.actArmarTerna.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Listar.png")))
        self.actListarEstudiantes.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Principal.png")))
        self.actGestionarEmpresa.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Empresa", "Empresa_Principal.png")))
        self.actBandejaSolicitudes.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Convenio", "Convenio_Principal.png")))
        self.actInformacion.setIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        self.actSalir.setIcon(QtGui.QIcon(ruta_recurso("General", "Salir.png")))
        self.actValidarPostulacion.setToolTip("Validar las postulaciones de los estudiantes")
        self.actArmarTerna.setToolTip("Armar ternas de postulantes para una oferta")
        self.actListarEstudiantes.setToolTip("Ver el estado de los estudiantes")
        self.actGestionarEmpresa.setToolTip("Gestionar empresas / tutores empresariales")
        self.actBandejaSolicitudes.setToolTip("Revisar la bandeja de solicitudes especiales")
        self.actInformacion.setToolTip("Acerca del sistema")
        self.actSalir.setToolTip("Cerrar esta ventana")


class VistaValidarPostulaciones(QtWidgets.QWidget, Ui_ValidarPostulaciones):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Validar_Postulacion.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdPostulacion)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPostulaciones)


class VistaArmarTernas(QtWidgets.QWidget, Ui_ArmarTernas):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Listar.png")))
        UtilidadesGUI.aplicar_validador_numerico(
            self.txtIdPostulante1, self.txtIdPostulante2, self.txtIdPostulante3)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPostulaciones)


class VistaGestionarEmpresas(QtWidgets.QWidget, Ui_GestionarEmpresas):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Empresa", "Empresa_Principal.png")))
        self.txtCedula.setMaxLength(10)
        self.txtRUC.setMaxLength(13)
        self.txtEliminarCedula.setMaxLength(10)
        UtilidadesGUI.aplicar_validador_numerico(self.txtCedula)
        UtilidadesGUI.aplicar_validador_numerico(self.txtTelefono)
        UtilidadesGUI.aplicar_validador_numerico(self.txtRUC, max_longitud=13)
        UtilidadesGUI.aplicar_validador_numerico(self.txtEliminarCedula)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblEmpresas)


class VistaListarEstudiantes(QtWidgets.QWidget, Ui_ListarEstudiantes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Principal.png")))
        UtilidadesGUI.aplicar_fuente_tabla(self.tblEstudiantes)


class VistaBandejaSolicitudes(QtWidgets.QWidget, Ui_BandejaSolicitudes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Convenio", "Convenio_Principal.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdSolicitud)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblSolicitudes)
