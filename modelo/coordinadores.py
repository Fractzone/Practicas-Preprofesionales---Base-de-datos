"""
Agrupo la familia de Coordinadores en un solo archivo ya que cree una clase padre coordinador
y los coordinadores usados heredan de este por lo que todos los coordinadores los modifico desde aqui.
"""
from modelo.validaciones import Validaciones


class Coordinador:

    def __init__(self, cedula, contrasena, nombres, apellidos, telefono, email, eliminado=False):
        if not Validaciones.validar_cedula(cedula):
            raise ValueError(f"La cédula '{cedula}' es inválida.")
        if not Validaciones.validar_contrasena(contrasena):
            raise ValueError("La contraseña debe tener entre 4 y 10 caracteres.")
        if not Validaciones.validar_telefono(telefono):
            raise ValueError("El teléfono debe tener 10 dígitos y comenzar con '09'.")
        if not Validaciones.validar_email(email):
            raise ValueError("El correo electrónico no tiene un formato válido (ejemplo@dominio.com).")
        if not Validaciones.validar_texto_no_vacio(nombres, apellidos):
            raise ValueError("Los nombres y apellidos no pueden estar vacíos.")

        self.cedula = cedula
        self.contrasena = contrasena
        self.nombres = nombres
        self.apellidos = apellidos
        self.telefono = telefono
        self.email = email
        self.eliminado = eliminado


class TutorAcademico(Coordinador):
    ROL = "tutor_academico"

    def __init__(self, cedula, contrasena, nombres, apellidos, telefono, email, carrera):
        super().__init__(cedula, contrasena, nombres, apellidos, telefono, email)
        if not Validaciones.validar_texto_no_vacio(carrera):
            raise ValueError("La carrera no puede estar vacía.")
        self.carrera = carrera

    def __repr__(self):
        return f"TutorAcademico(cedula='{self.cedula}', nombres='{self.nombres}', carrera='{self.carrera}')"


class RepositorioTutorAcademico:
    ENTIDAD = 'tutor_academico'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def recargar(self):
        # Compatibilidad: ya no hay caché en memoria; cada método consulta la BD.
        pass

    def actualizar(self, tutor):
        self.persistencia.actualizar(self.ENTIDAD, tutor)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, cedula):
        tutor = self.persistencia.obtener(self.ENTIDAD, cedula)
        return tutor if tutor is not None and not tutor.eliminado else None

    def por_carrera(self, carrera):
        tutores = self.persistencia.listar(self.ENTIDAD, where="carrera = %s", params=(carrera,))
        return tutores[0] if tutores else None

    def agregar(self, cedula, contrasena, nombres, apellidos, telefono, email, carrera):
        if not all([cedula, contrasena, nombres, apellidos, telefono, email, carrera]):
            raise ValueError("Por favor, complete todos los campos obligatorios.")
        if self.persistencia.existe(self.ENTIDAD, cedula):
            raise ValueError(f"El tutor académico con cédula {cedula} ya está registrado.")
        nuevo = TutorAcademico(cedula, contrasena, nombres, apellidos, telefono, email, carrera)
        self.persistencia.insertar(self.ENTIDAD, nuevo)
        return nuevo

    def eliminar(self, cedula):
        if self.buscar(cedula) is None:
            raise ValueError("No existe un tutor académico registrado con la cédula ingresada.")
        self.persistencia.marcar_eliminado(self.ENTIDAD, cedula)


class TutorEmpresarial(Coordinador):
    ROL = "tutor_empresarial"

    def __init__(self, cedula, contrasena, nombres, apellidos, telefono, email,
                 cargo, ruc_empresa, nombre_empresa, direccion_empresa):
        super().__init__(cedula, contrasena, nombres, apellidos, telefono, email)
        if not Validaciones.validar_ruc(ruc_empresa):
            raise ValueError("El RUC de la empresa debe tener 13 dígitos y terminar en '001'.")
        if not Validaciones.validar_texto_no_vacio(cargo, nombre_empresa, direccion_empresa):
            raise ValueError("El cargo, el nombre y la dirección de la empresa no pueden estar vacíos.")
        self.cargo = cargo
        self.ruc_empresa = ruc_empresa
        self.nombre_empresa = nombre_empresa
        self.direccion_empresa = direccion_empresa

    def __repr__(self):
        return f"TutorEmpresarial(cedula='{self.cedula}', empresa='{self.nombre_empresa}', ruc='{self.ruc_empresa}')"


class RepositorioTutorEmpresarial:
    ENTIDAD = 'tutor_empresarial'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def recargar(self):
        # Compatibilidad: ya no hay caché en memoria; cada método consulta la BD.
        pass

    def actualizar(self, tutor):
        self.persistencia.actualizar(self.ENTIDAD, tutor)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, cedula):
        tutor = self.persistencia.obtener(self.ENTIDAD, cedula)
        return tutor if tutor is not None and not tutor.eliminado else None

    def buscar_por_ruc(self, ruc):
        tutores = self.persistencia.listar(self.ENTIDAD, where="ruc_empresa = %s", params=(ruc,))
        return tutores[0] if tutores else None

    def agregar(self, cedula, contrasena, nombres, apellidos, telefono, email,
                cargo, ruc_empresa, nombre_empresa, direccion_empresa):
        if not all([cedula, contrasena, nombres, apellidos, telefono, email,
                    cargo, ruc_empresa, nombre_empresa, direccion_empresa]):
            raise ValueError("Por favor, complete todos los campos obligatorios.")
        if self.persistencia.existe(self.ENTIDAD, cedula):
            raise ValueError(f"El tutor empresarial con cédula {cedula} ya está registrado.")
        if self.buscar_por_ruc(ruc_empresa) is not None:
            raise ValueError(f"Ya existe una empresa registrada con el RUC {ruc_empresa}.")
        nuevo = TutorEmpresarial(cedula, contrasena, nombres, apellidos, telefono, email,
                                 cargo, ruc_empresa, nombre_empresa, direccion_empresa)
        self.persistencia.insertar(self.ENTIDAD, nuevo)
        return nuevo

    def eliminar(self, cedula):
        if self.buscar(cedula) is None:
            raise ValueError("No existe un tutor empresarial registrado con la cédula ingresada.")
        self.persistencia.marcar_eliminado(self.ENTIDAD, cedula)


class CoordinadorVinculacion(Coordinador):
    ROL = "coordinador_vinculacion"

    def __init__(self, cedula, contrasena, nombres, apellidos, telefono, email,
                 fecha_nacimiento, direccion, carrera):
        super().__init__(cedula, contrasena, nombres, apellidos, telefono, email)
        if not Validaciones.validar_edad(fecha_nacimiento):
            raise ValueError("La fecha de nacimiento es inválida o el coordinador supera los 80 años permitidos.")
        if not Validaciones.validar_texto_no_vacio(direccion, carrera):
            raise ValueError("La dirección y la carrera no pueden estar vacías.")
        self.fecha_nacimiento = fecha_nacimiento
        self.direccion = direccion
        self.carrera = carrera

    def __repr__(self):
        return f"CoordinadorVinculacion(cedula='{self.cedula}', nombres='{self.nombres}', carrera='{self.carrera}')"


class RepositorioCoordinadorVinculacion:
    ENTIDAD = 'coordinador_vinculacion'

    def __init__(self, persistencia):
        self.persistencia = persistencia

    def recargar(self):
        # Compatibilidad: ya no hay caché en memoria; cada método consulta la BD.
        pass

    def actualizar(self, coordinador):
        self.persistencia.actualizar(self.ENTIDAD, coordinador)

    def listar(self):
        return self.persistencia.listar(self.ENTIDAD)

    def buscar(self, cedula):
        coordinador = self.persistencia.obtener(self.ENTIDAD, cedula)
        return coordinador if coordinador is not None and not coordinador.eliminado else None

    def agregar(self, cedula, contrasena, nombres, apellidos, telefono, email,
                fecha_nacimiento, direccion, carrera):
        if not all([cedula, contrasena, nombres, apellidos, telefono, email, direccion, carrera]):
            raise ValueError("Por favor, complete todos los campos obligatorios.")
        if self.persistencia.existe(self.ENTIDAD, cedula):
            raise ValueError(f"El coordinador de vinculación con cédula {cedula} ya está registrado.")
        nuevo = CoordinadorVinculacion(cedula, contrasena, nombres, apellidos, telefono, email,
                                       fecha_nacimiento, direccion, carrera)
        self.persistencia.insertar(self.ENTIDAD, nuevo)
        return nuevo

    def eliminar(self, cedula):
        if self.buscar(cedula) is None:
            raise ValueError("No existe un coordinador de vinculación registrado con la cédula ingresada.")
        self.persistencia.marcar_eliminado(self.ENTIDAD, cedula)
