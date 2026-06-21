from vista.vista_administrador.interfaz_vista_administrador import VistaPrincipalAdministrador
from vista.ventanas_generales.vista_informacion import VistaInformacion
from controlador.controlador_crud_administrador import ControladorCRUDAdministrador
from controlador.controlador_crud_estudiante import ControladorCRUDEstudiante
from controlador.controlador_crud_tutor_academico import ControladorCRUDTutorAcademico
from controlador.controlador_crud_vinculacion import ControladorCRUDVinculacion

class ControladorAdministrador:

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.vista_principal = VistaPrincipalAdministrador()
        self.sub_controlador = None
        self.conectar_signals()

    def iniciar(self):
        self.vista_principal.show()

    def conectar_signals(self):
        self.vista_principal.actMantenimientoAdministrador.triggered.connect(
            lambda: self.abrir_modulo(ControladorCRUDAdministrador))
        self.vista_principal.actMantenimientoEstudiante.triggered.connect(
            lambda: self.abrir_modulo(ControladorCRUDEstudiante))
        self.vista_principal.actMantenimientoTutorAcademico.triggered.connect(
            lambda: self.abrir_modulo(ControladorCRUDTutorAcademico))
        self.vista_principal.actMantenimientoCoordinador.triggered.connect(
            lambda: self.abrir_modulo(ControladorCRUDVinculacion))
        self.vista_principal.actSalir.triggered.connect(self.vista_principal.close)
        self.vista_principal.actInformacion.triggered.connect(self.slot_mostrar_informacion)

    def abrir_modulo(self, clase_controlador):
        self.sub_controlador = clase_controlador(self.persistencia)
        self.sub_controlador.iniciar()

    def slot_mostrar_informacion(self):
        VistaInformacion(self.vista_principal).exec()
