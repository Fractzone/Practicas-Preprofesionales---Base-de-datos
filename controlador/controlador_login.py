from modelo.seguridad import verificar_password
from vista.vista_login.interfaz_vista_login import VistaLogin
from vista.ventanas_generales.vista_error import VistaError
from vista.ventanas_generales.vista_informacion import VistaInformacion
from controlador.controlador_administrador import ControladorAdministrador
from controlador.controlador_estudiante import ControladorEstudiante
from controlador.controlador_coordinador_vinculacion import ControladorCoordinadorVinculacion
from controlador.controlador_tutor_empresarial import ControladorTutorEmpresarial
from controlador.controlador_tutor_academico import ControladorTutorAcademico

class ControladorLogin:
    ENTIDAD = 'login'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.vista_login = VistaLogin()
        self.controlador_activo = None
        self.conectar_signals()

    def iniciar(self):
        self.vista_login.show()

    def conectar_signals(self):
        self.vista_login.btnIngresar.clicked.connect(self.slot_ingresar)
        self.vista_login.actSalir.triggered.connect(self.vista_login.close)
        self.vista_login.actInfo.triggered.connect(self.slot_mostrar_informacion)

    def slot_mostrar_informacion(self):
        VistaInformacion(self.vista_login).exec()

    def slot_ingresar(self):
        identificador = self.vista_login.txtUsuario.text().strip()
        contrasena = self.vista_login.txtContrasena.text().strip()

        try:
            if not (identificador and contrasena):
                raise ValueError("Por favor, ingrese su usuario y contraseña.")

            credencial = self.persistencia.obtener(self.ENTIDAD, identificador)

            if (credencial is None or credencial.eliminado or
                    not verificar_password(contrasena, credencial.contrasena)):
                raise ValueError("Usuario o contraseña incorrectos.")

            self.abrir_modulo(credencial)

        except ValueError as e:
            VistaError(str(e), self.vista_login).exec()

    def abrir_modulo(self, credencial):
        modulos = {
            "administrador": lambda: ControladorAdministrador(self.persistencia),
            "estudiante": lambda: ControladorEstudiante(self.persistencia, credencial.identificador),
            "coordinador_vinculacion": lambda: ControladorCoordinadorVinculacion(self.persistencia, credencial.identificador),
            "tutor_empresarial": lambda: ControladorTutorEmpresarial(self.persistencia, credencial.identificador),
            "tutor_academico": lambda: ControladorTutorAcademico(self.persistencia, credencial.identificador),
        }
        constructor = modulos.get(credencial.rol)

        if constructor is None:
            VistaError(f"El módulo para el rol '{credencial.rol}' aún no está implementado.", self.vista_login).exec()
            return

        self.controlador_activo = constructor()
        self.vista_login.close()
        self.controlador_activo.iniciar()
