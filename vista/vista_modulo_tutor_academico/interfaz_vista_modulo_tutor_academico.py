from PyQt6 import QtCore, QtWidgets, QtGui
from vista.vista_modulo_tutor_academico.VistaTutorAcademicoPrincipal import Ui_frmTutorAcademico
from vista.vista_modulo_tutor_academico.AprobarFormulario1 import Ui_AprobarFormulario1
from vista.vista_modulo_tutor_academico.Formulario3 import Ui_Formulario3
from vista.vista_modulo_tutor_academico.ListarPracticasActivas import Ui_ListarPracticasActivas
from vista.ventanas_generales.utilidades_gui import UtilidadesGUI
from vista.ventanas_generales.rutas_recursos import ruta_recurso
from modelo.formulario import CRITERIOS_F3

OPCIONES_NIVEL_F3 = ["1 (Mínimo)", "2", "3", "4 (Máximo)"]


class VistaTutorAcademicoPrincipal(QtWidgets.QMainWindow, Ui_frmTutorAcademico):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.lblImagen.setPixmap(QtGui.QPixmap(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Principal.png")))
        self.actListarPracticas.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Listar.png")))
        self.actAprobarF1.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Validar_Postulacion.png")))
        self.actFormulario3.setIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Principal.png")))
        self.actInformacion.setIcon(QtGui.QIcon(ruta_recurso("General", "Info.png")))
        self.actSalir.setIcon(QtGui.QIcon(ruta_recurso("General", "Salir.png")))
        self.actListarPracticas.setToolTip("Listar mis prácticas activas")
        self.actAprobarF1.setToolTip("Revisar y aprobar el Formulario 1 de los estudiantes")
        self.actFormulario3.setToolTip("Evaluación académica (Formulario 3) y asentar la nota")
        self.actInformacion.setToolTip("Acerca del sistema")
        self.actSalir.setToolTip("Cerrar esta ventana")


class VistaAprobarFormulario1(QtWidgets.QWidget, Ui_AprobarFormulario1):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Coordinador", "Coordinador_Validar_Postulacion.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdPractica)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPendientes)


class VistaListarPracticasActivas(QtWidgets.QWidget, Ui_ListarPracticasActivas):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Listar.png")))
        UtilidadesGUI.aplicar_fuente_tabla(self.tblPracticas)


class VistaFormulario3(QtWidgets.QWidget, Ui_Formulario3):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QtGui.QIcon(ruta_recurso("Iconos_Menu_Practica", "Practica_Principal.png")))
        UtilidadesGUI.aplicar_validador_numerico(self.txtIdPractica)
        UtilidadesGUI.aplicar_fuente_tabla(self.tblRubricaAcademica)
        self.poblar_rubrica()

    def showEvent(self, event):
        super().showEvent(event)
        UtilidadesGUI.centrar(self)

    def poblar_rubrica(self):
        self.tblRubricaAcademica.setRowCount(len(CRITERIOS_F3))
        self.checks_rubrica = []
        self.combos_rubrica = []
        list(map(self._fila_rubrica, enumerate(CRITERIOS_F3)))
        self.tblRubricaAcademica.resizeRowsToContents()

    def _fila_rubrica(self, par):
        indice, criterio = par
        codigo, descripcion, esperado = criterio
        item_crit = QtWidgets.QTableWidgetItem(f"{codigo} {descripcion}")
        item_crit.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
        self.tblRubricaAcademica.setItem(indice, 0, item_crit)
        item_esp = QtWidgets.QTableWidgetItem(str(esperado))
        item_esp.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
        item_esp.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.tblRubricaAcademica.setItem(indice, 1, item_esp)

        check = QtWidgets.QCheckBox()
        contenedor = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(contenedor)
        layout.addWidget(check)
        layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tblRubricaAcademica.setCellWidget(indice, 2, contenedor)

        combo = QtWidgets.QComboBox()
        combo.addItems(OPCIONES_NIVEL_F3)
        self.tblRubricaAcademica.setCellWidget(indice, 3, combo)
        check.toggled.connect(lambda marcado: combo.setEnabled(not marcado))

        self.checks_rubrica.append(check)
        self.combos_rubrica.append(combo)

    def evaluacion(self):
        return {CRITERIOS_F3[indice][0]: {
                    "no_aplica": check.isChecked(),
                    "nivel_alcanzado": int(self.combos_rubrica[indice].currentText()[0])}
                for indice, check in enumerate(self.checks_rubrica)}
