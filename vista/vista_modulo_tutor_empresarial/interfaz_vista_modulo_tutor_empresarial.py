from PyQt6 import QtCore, QtWidgets, QtGui
from vista.vista_modulo_tutor_empresarial.VistaTutorEmpresarialPrincipal import Ui_frmTutorEmpresarial
from vista.vista_modulo_tutor_empresarial.CrearOferta import Ui_CrearOferta
from vista.vista_modulo_tutor_empresarial.AceptarEstudiante import Ui_AceptarEstudiante
from vista.vista_modulo_tutor_empresarial.Formulario2 import Ui_Formulario2
from vista.vista_modulo_tutor_empresarial.ListarPracticasActivas import Ui_ListarPracticasActivas
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI
from vista.ventanas_generales.rutas_recursos import ruta_recurso
from modelo.formulario import HABILIDADES_F2

OPCIONES_RUBRICA_F2 = ["A - Excelente", "B - Satisfactorio", "C - Poco Satisfactorio",
                       "D - Mejorable", "E - Insatisfactorio"]


class VistaTutorEmpresarialPrincipal(QtWidgets.QMainWindow, Ui_frmTutorEmpresarial):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Empresa", "Empresa_Principal.png")))
        self.lblImagen.setPixmap(QtGui.QPixmap(ruta_recurso("Iconos_Menu_Empresa", "Empresa_Principal.png")))
        self.actCrearOferta.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Oferta", "Oferta_Agregar.png")))
        self.actListarPracticas.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Listar.png")))
        self.actRecibirTernas.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Empresa", "Empresa_Confirmar_Postulacion.png")))
        self.actFormulario2.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Enviar_Formulario.png")))
        self.actInformacion.setIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        self.actSalir.setIcon(QtGui.QIcon(ruta_recurso("General", "Salir.png")))
        self.actCrearOferta.setToolTip("Crear una nueva oferta de práctica")
        self.actListarPracticas.setToolTip("Listar mis prácticas activas")
        self.actRecibirTernas.setToolTip("Recibir ternas y aceptar a un estudiante")
        self.actFormulario2.setToolTip("Evaluación empresarial (Formulario 2)")
        self.actInformacion.setToolTip("Acerca del sistema")
        self.actSalir.setToolTip("Cerrar esta ventana")


class VistaCrearOferta(QtWidgets.QWidget, Ui_CrearOferta):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Oferta", "Oferta_Principal.png")))
        UtilidadesGUI.aplicar_fuente_tabla(self.tblOfertas)


class VistaRecibirTernas(QtWidgets.QWidget, Ui_AceptarEstudiante):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Empresa", "Empresa_Confirmar_Postulacion.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdPostulacionAceptar)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblTernasEnviadas)


class VistaListarPracticasActivas(QtWidgets.QWidget, Ui_ListarPracticasActivas):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Listar.png")))
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPracticas)


class VistaFormulario2(QtWidgets.QWidget, Ui_Formulario2):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Estudiante", "Estudiante_Enviar_Formulario.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdPractica)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblRubrica)
        self.dtFechaRealInicio.setDate(QtCore.QDate.currentDate())
        self.dtFechaRealFin.setDate(QtCore.QDate.currentDate())
        self.poblar_rubrica()

    def showEvent(self, event):
        super().showEvent(event)
        UtilidadesGUI.centrar(self)

    def poblar_rubrica(self):
        self.tblRubrica.setRowCount(len(HABILIDADES_F2))
        self.combos_rubrica = []
        list(map(self._fila_rubrica, enumerate(HABILIDADES_F2)))
        self.tblRubrica.resizeRowsToContents()

    def _fila_rubrica(self, par):
        indice, habilidad = par
        item = QtWidgets.QTableWidgetItem(f"{indice + 1}) {habilidad}")
        item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
        self.tblRubrica.setItem(indice, 0, item)
        combo = QtWidgets.QComboBox()
        combo.addItems(OPCIONES_RUBRICA_F2)
        self.tblRubrica.setCellWidget(indice, 1, combo)
        self.combos_rubrica.append(combo)

    def calificaciones(self):
        return {indice + 1: combo.currentText().split(" ")[0]
                for indice, combo in enumerate(self.combos_rubrica)}
