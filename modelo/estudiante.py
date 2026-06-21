from modelo.validaciones import Validaciones

class Estudiante:
    ROL = "estudiante"

    def __init__(self, cedula, contrasena, apellidos, nombres, telefono, email, carrera, ciclo, num_practicas_realizadas=0, total_horas_realizadas=0, eliminado=False):
        if not Validaciones.validar_cedula(cedula):
            raise ValueError(f"La cédula '{cedula}' es inválida.")
        if not Validaciones.validar_contrasena(contrasena):
            raise ValueError("La contraseña debe tener entre 4 y 10 caracteres.")
        if not Validaciones.validar_telefono(telefono):
            raise ValueError("El teléfono debe tener 10 dígitos y comenzar con '09'.")
        if not Validaciones.validar_email(email):
            raise ValueError("El correo electrónico no tiene un formato válido (ejemplo@dominio.com).")
        if not Validaciones.validar_texto_no_vacio(apellidos, nombres, carrera):
            raise ValueError("Apellidos, nombres y carrera no pueden estar vacíos.")
        if not (isinstance(ciclo, int) and 1 <= ciclo <= 10):
            raise ValueError("El ciclo debe ser un número entero entre 1 y 10.")
        if not (isinstance(num_practicas_realizadas, int) and num_practicas_realizadas >= 0):
            raise ValueError("El número de prácticas realizadas debe ser un entero no negativo.")
        if not (isinstance(total_horas_realizadas, int) and total_horas_realizadas >= 0):
            raise ValueError("El total de horas realizadas debe ser un entero no negativo.")

        self.cedula = cedula
        self.contrasena = contrasena
        self.apellidos = apellidos
        self.nombres = nombres
        self.telefono = telefono
        self.email = email
        self.carrera = carrera
        self.ciclo = ciclo
        self.num_practicas_realizadas = num_practicas_realizadas
        self.total_horas_realizadas = total_horas_realizadas
        self.eliminado = eliminado

    @staticmethod
    def buscar_por_cedula(diccionario_estudiantes, cedula):
        return diccionario_estudiantes.get(cedula, None)

    def __repr__(self):
        return f"Estudiante(cedula='{self.cedula}', nombres='{self.nombres}', apellidos='{self.apellidos}')"


class RepositorioEstudiante:
    ENTIDAD = 'estudiante'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.estudiantes = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.estudiantes = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.estudiantes)

    def listar(self):
        return list(filter(lambda e: not e.eliminado, self.estudiantes.values()))

    def buscar(self, cedula):
        estudiante = Estudiante.buscar_por_cedula(self.estudiantes, cedula)
        return estudiante if estudiante is not None and not estudiante.eliminado else None

    def agregar(self, cedula, contrasena, apellidos, nombres, telefono, email, carrera, ciclo):
        if not all([cedula, contrasena, apellidos, nombres, telefono, email, carrera]):
            raise ValueError("Por favor, complete todos los campos de texto obligatorios.")
        if cedula in self.estudiantes:
            raise ValueError(f"El estudiante con cédula {cedula} ya está registrado.")
        nuevo = Estudiante(cedula, contrasena, apellidos, nombres, telefono, email, carrera, ciclo)
        self.estudiantes[nuevo.cedula] = nuevo
        self.guardar()
        return nuevo

    def eliminar(self, cedula):
        estudiante = self.estudiantes.get(cedula)
        if estudiante is None or estudiante.eliminado:
            raise ValueError("No existe un estudiante registrado con la cédula ingresada.")
        estudiante.eliminado = True
        self.guardar()
