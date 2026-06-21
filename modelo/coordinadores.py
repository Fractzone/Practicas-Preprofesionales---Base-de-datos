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

    @staticmethod
    def buscar_por_cedula(diccionario, cedula):
        return diccionario.get(cedula, None)


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
        self.tutores = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.tutores = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.tutores)

    def listar(self):
        return list(filter(lambda t: not t.eliminado, self.tutores.values()))

    def buscar(self, cedula):
        tutor = TutorAcademico.buscar_por_cedula(self.tutores, cedula)
        return tutor if tutor is not None and not tutor.eliminado else None

    def por_carrera(self, carrera):
        return next(filter(lambda t: t.carrera == carrera and not t.eliminado, self.tutores.values()), None)

    def agregar(self, cedula, contrasena, nombres, apellidos, telefono, email, carrera):
        if not all([cedula, contrasena, nombres, apellidos, telefono, email, carrera]):
            raise ValueError("Por favor, complete todos los campos obligatorios.")
        if cedula in self.tutores:
            raise ValueError(f"El tutor académico con cédula {cedula} ya está registrado.")
        nuevo = TutorAcademico(cedula, contrasena, nombres, apellidos, telefono, email, carrera)
        self.tutores[nuevo.cedula] = nuevo
        self.guardar()
        return nuevo

    def eliminar(self, cedula):
        tutor = self.tutores.get(cedula)
        if tutor is None or tutor.eliminado:
            raise ValueError("No existe un tutor académico registrado con la cédula ingresada.")
        tutor.eliminado = True
        self.guardar()


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
        self.tutores = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.tutores = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.tutores)

    def listar(self):
        return list(filter(lambda t: not t.eliminado, self.tutores.values()))

    def buscar(self, cedula):
        tutor = TutorEmpresarial.buscar_por_cedula(self.tutores, cedula)
        return tutor if tutor is not None and not tutor.eliminado else None

    def buscar_por_ruc(self, ruc):
        return next(filter(lambda t: t.ruc_empresa == ruc and not t.eliminado, self.tutores.values()), None)

    def agregar(self, cedula, contrasena, nombres, apellidos, telefono, email,
                cargo, ruc_empresa, nombre_empresa, direccion_empresa):
        if not all([cedula, contrasena, nombres, apellidos, telefono, email,
                    cargo, ruc_empresa, nombre_empresa, direccion_empresa]):
            raise ValueError("Por favor, complete todos los campos obligatorios.")
        if cedula in self.tutores:
            raise ValueError(f"El tutor empresarial con cédula {cedula} ya está registrado.")
        if self.buscar_por_ruc(ruc_empresa) is not None:
            raise ValueError(f"Ya existe una empresa registrada con el RUC {ruc_empresa}.")
        nuevo = TutorEmpresarial(cedula, contrasena, nombres, apellidos, telefono, email,
                                 cargo, ruc_empresa, nombre_empresa, direccion_empresa)
        self.tutores[nuevo.cedula] = nuevo
        self.guardar()
        return nuevo

    def eliminar(self, cedula):
        tutor = self.tutores.get(cedula)
        if tutor is None or tutor.eliminado:
            raise ValueError("No existe un tutor empresarial registrado con la cédula ingresada.")
        tutor.eliminado = True
        self.guardar()


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
        self.coordinadores = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.coordinadores = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.coordinadores)

    def listar(self):
        return list(filter(lambda c: not c.eliminado, self.coordinadores.values()))

    def buscar(self, cedula):
        coordinador = CoordinadorVinculacion.buscar_por_cedula(self.coordinadores, cedula)
        return coordinador if coordinador is not None and not coordinador.eliminado else None

    def agregar(self, cedula, contrasena, nombres, apellidos, telefono, email,
                fecha_nacimiento, direccion, carrera):
        if not all([cedula, contrasena, nombres, apellidos, telefono, email, direccion, carrera]):
            raise ValueError("Por favor, complete todos los campos obligatorios.")
        if cedula in self.coordinadores:
            raise ValueError(f"El coordinador de vinculación con cédula {cedula} ya está registrado.")
        nuevo = CoordinadorVinculacion(cedula, contrasena, nombres, apellidos, telefono, email,
                                       fecha_nacimiento, direccion, carrera)
        self.coordinadores[nuevo.cedula] = nuevo
        self.guardar()
        return nuevo

    def eliminar(self, cedula):
        coordinador = self.coordinadores.get(cedula)
        if coordinador is None or coordinador.eliminado:
            raise ValueError("No existe un coordinador de vinculación registrado con la cédula ingresada.")
        coordinador.eliminado = True
        self.guardar()
