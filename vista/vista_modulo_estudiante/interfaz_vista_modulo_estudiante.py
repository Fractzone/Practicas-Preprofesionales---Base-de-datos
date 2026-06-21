from PyQt6 import QtCore, QtWidgets, QtGui
from vista.vista_modulo_estudiante.VistaEstudiantePrincipal import Ui_frmEstudiante
from vista.vista_modulo_estudiante.BuscarOfertas import Ui_BuscarOfertas
from vista.vista_modulo_estudiante.MisPostulaciones import Ui_MisPostulaciones
from vista.vista_modulo_estudiante.Solicitudes import Ui_Solicitudes
from vista.vista_modulo_estudiante.Formulario1 import Ui_Formulario1
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI
from vista.ventanas_generales.rutas_recursos import ruta_recurso


class VistaEstudiantePrincipal(QtWidgets.QMainWindow, Ui_frmEstudiante):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Principal.png")))
        self.lblImagen.setPixmap(QtGui.QPixmap(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Principal.png")))
        self.actPostulaciones.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Postulacion", "Postulacion_Principal.png")))
        self.actBuscarOferta.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Oferta", "Oferta_Principal.png")))
        self.actFormulario1.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Enviar_Formulario.png")))
        self.actSolicitarEvaluacion.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Listar.png")))
        self.actSolicitudesEspeciales.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Oferta", "Oferta_Principal.png")))
        self.actSalir.setIcon(QtGui.QIcon(ruta_recurso("General", "Salir.png")))
        self.actInformacion.setIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        self.actPostulaciones.setToolTip("Ver el estado de mis postulaciones")
        self.actBuscarOferta.setToolTip("Buscar ofertas disponibles y postular")
        self.actFormulario1.setToolTip("Llenar el Formulario 1 (Registro de PPP)")
        self.actSolicitarEvaluacion.setToolTip("Solicitar la evaluación final de mi práctica")
        self.actSolicitudesEspeciales.setToolTip("Enviar una solicitud especial")
        self.actInformacion.setToolTip("Acerca del sistema")
        self.actSalir.setToolTip("Cerrar esta ventana")


class VistaBuscarOfertas(QtWidgets.QWidget, Ui_BuscarOfertas):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Oferta", "Oferta_Principal.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdOferta)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblOfertas)


class VistaMisPostulaciones(QtWidgets.QWidget, Ui_MisPostulaciones):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Postulacion", "Postulacion_Principal.png")))
        UtilidadesGUI.aplicar_fuente_tabla(self.tblMisPostulaciones)


class VistaSolicitudes(QtWidgets.QWidget, Ui_Solicitudes):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Enviar_Formulario.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtEmpTelefono)
        UtilidadesGUI.aplicar_validador_numerico(self.txtEmpRuc, max_longitud=13)
        self.txtEmpRuc.setMaxLength(13)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblSolicitudes)


class VistaFormulario1(QtWidgets.QWidget, Ui_Formulario1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Enviar_Formulario.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdPractica)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblActividades)
        self.dtFechaInicial.setDate(QtCore.QDate.currentDate())
        self.dtFechaFinal.setDate(QtCore.QDate.currentDate())

    def showEvent(self, event):
        super().showEvent(event)
        UtilidadesGUI.centrar(self)
