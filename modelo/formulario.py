"""
Uno los formulario en un solo archivo ya que al ser tres disintos mejor los junto para que no hagan vulto en la carpeta de modelo
y los manejo los tres desde aqui
"""
from modelo.validaciones import Validaciones

class Formulario1:
    TIPOS_DOCUMENTO = ("Convenio", "Carta de Compromiso")
    TIPOS_PRACTICA = ("Preprofesional", "Pasantía")

    def __init__(self, id_formulario1, id_practica, tipo_documento, numero_documento, tipo_practica,
                 remuneracion, fecha_inicial, fecha_final_aprox, horas_aprox, actividades,
                 estado_aprobacion="Pendiente", eliminado=False):
        if tipo_documento not in self.TIPOS_DOCUMENTO:
            raise ValueError("El tipo de documento debe ser 'Convenio' o 'Carta de Compromiso'.")
        if tipo_practica not in self.TIPOS_PRACTICA:
            raise ValueError("El tipo de práctica debe ser 'Preprofesional' o 'Pasantía'.")
        if not Validaciones.validar_texto_no_vacio(numero_documento):
            raise ValueError("El número de documento no puede estar vacío.")
        if not Validaciones.validar_decimal_no_negativo(remuneracion):
            raise ValueError("La remuneración debe ser un valor numérico no negativo.")
        if not Validaciones.validar_entero_positivo(horas_aprox):
            raise ValueError("Las horas estimadas deben ser un entero positivo.")
        if not Validaciones.validar_fecha_no_pasada(fecha_inicial):
            raise ValueError("La fecha de inicio de la práctica no puede ser anterior a la fecha actual.")
        if not Validaciones.validar_orden_fechas(fecha_inicial, fecha_final_aprox):
            raise ValueError("La fecha final no puede ser anterior a la fecha de inicio.")
        if not (isinstance(actividades, list) and len(actividades) > 0):
            raise ValueError("Debe registrar al menos una actividad.")

        self.id_formulario1 = id_formulario1
        self.id_practica = id_practica
        self.tipo_documento = tipo_documento
        self.numero_documento = numero_documento
        self.tipo_practica = tipo_practica
        self.remuneracion = remuneracion
        self.fecha_inicial = fecha_inicial
        self.fecha_final_aprox = fecha_final_aprox
        self.horas_aprox = horas_aprox
        self.actividades = actividades
        self.estado_aprobacion = estado_aprobacion
        self.eliminado = eliminado

    @staticmethod
    def buscar_por_id(diccionario, id_buscado):
        return diccionario.get(id_buscado, None)

    def __repr__(self):
        return f"Formulario1(id='{self.id_formulario1}', practica='{self.id_practica}', estado='{self.estado_aprobacion}')"


class RepositorioFormulario1:
    ENTIDAD = 'formulario1'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.formularios = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.formularios = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.formularios)

    def listar(self):
        return list(filter(lambda f: not f.eliminado, self.formularios.values()))

    def buscar(self, id_formulario1):
        formulario = Formulario1.buscar_por_id(self.formularios, id_formulario1)
        return formulario if formulario is not None and not formulario.eliminado else None

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.formularios.keys()))),
            default=0) + 1)

    def buscar_por_practica(self, id_practica):
        return next(filter(lambda f: f.id_practica == id_practica and not f.eliminado, self.formularios.values()), None)

    def tiene(self, id_practica):
        return self.buscar_por_practica(id_practica) is not None

    def por_estado(self, estado):
        return list(filter(lambda f: f.estado_aprobacion == estado and not f.eliminado, self.formularios.values()))

    def agregar(self, id_practica, tipo_documento, numero_documento, tipo_practica,
                remuneracion, fecha_inicial, fecha_final_aprox, horas_aprox, actividades):
        if self.tiene(id_practica):
            raise ValueError("El Formulario 1 ya fue registrado para esta práctica.")
        nuevo_id = self.siguiente_id()
        nuevo = Formulario1(nuevo_id, id_practica, tipo_documento, numero_documento, tipo_practica,
                            remuneracion, fecha_inicial, fecha_final_aprox, horas_aprox, actividades)
        self.formularios[nuevo_id] = nuevo
        self.guardar()
        return nuevo


HABILIDADES_F2 = (
    "Habilidad para aplicar conocimiento de matemática, ciencia e ingeniería.",
    "Habilidad para diseñar y conducir experimentos, así como analizar e interpretar datos.",
    "Habilidad para diseñar un sistema, componente o proceso para cubrir necesidades deseadas.",
    "Habilidad para trabajar en equipo y comunicarse efectivamente.",
    "Habilidad para identificar, formular y solucionar problemas de ingeniería.",
    "Entendimiento de responsabilidad y ética profesional.",
    "Educación para entender el impacto de las soluciones de ingeniería en un contexto global y social.",
    "Reconocer la necesidad para aprender a lo largo de su vida.",
    "Conocimiento de temas de actualidad.",
    "Habilidad para usar técnicas, habilidades y herramientas modernas para la práctica de la ingeniería.",
)

ESCALA_F2 = ("A", "B", "C", "D", "E")


class Formulario2:

    def __init__(self, id_formulario2, id_practica, fecha_real_inicio, fecha_real_fin, horas_cumplidas,
                 calificaciones_rubrica, productos_relevantes, aspectos_relevantes, estado="Completado",
                 eliminado=False):
        if not Validaciones.validar_entero_positivo(horas_cumplidas):
            raise ValueError("Las horas cumplidas deben ser un entero positivo.")
        if not (isinstance(calificaciones_rubrica, dict) and len(calificaciones_rubrica) == len(HABILIDADES_F2)):
            raise ValueError("Debe calificar las 10 habilidades de la rúbrica.")
        if not all(map(lambda v: v in ESCALA_F2, calificaciones_rubrica.values())):
            raise ValueError("Las calificaciones deben estar en la escala A, B, C, D o E.")
        if not Validaciones.validar_fecha_no_futura(fecha_real_inicio):
            raise ValueError("La fecha real de inicio no puede ser posterior a la fecha actual.")
        if not Validaciones.validar_fecha_no_futura(fecha_real_fin):
            raise ValueError("La fecha real de fin no puede ser posterior a la fecha actual.")
        if not Validaciones.validar_orden_fechas(fecha_real_inicio, fecha_real_fin):
            raise ValueError("La fecha real de fin no puede ser anterior a la de inicio.")
        if not Validaciones.validar_texto_no_vacio(productos_relevantes, aspectos_relevantes):
            raise ValueError("Los productos y aspectos relevantes no pueden estar vacíos.")

        self.id_formulario2 = id_formulario2
        self.id_practica = id_practica
        self.fecha_real_inicio = fecha_real_inicio
        self.fecha_real_fin = fecha_real_fin
        self.horas_cumplidas = horas_cumplidas
        self.calificaciones_rubrica = calificaciones_rubrica
        self.productos_relevantes = productos_relevantes
        self.aspectos_relevantes = aspectos_relevantes
        self.estado = estado
        self.eliminado = eliminado

    @staticmethod
    def buscar_por_id(diccionario, id_buscado):
        return diccionario.get(id_buscado, None)

    def __repr__(self):
        return f"Formulario2(id='{self.id_formulario2}', practica='{self.id_practica}')"


class RepositorioFormulario2:
    ENTIDAD = 'formulario2'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.formularios = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.formularios = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.formularios)

    def listar(self):
        return list(filter(lambda f: not f.eliminado, self.formularios.values()))

    def buscar(self, id_formulario2):
        formulario = Formulario2.buscar_por_id(self.formularios, id_formulario2)
        return formulario if formulario is not None and not formulario.eliminado else None

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.formularios.keys()))),
            default=0) + 1)

    def buscar_por_practica(self, id_practica):
        return next(filter(lambda f: f.id_practica == id_practica and not f.eliminado, self.formularios.values()), None)

    def tiene(self, id_practica):
        return self.buscar_por_practica(id_practica) is not None

    def agregar(self, id_practica, fecha_real_inicio, fecha_real_fin, horas_cumplidas,
                calificaciones_rubrica, productos_relevantes, aspectos_relevantes):
        if self.tiene(id_practica):
            raise ValueError("El Formulario 2 ya fue registrado para esta práctica.")
        nuevo_id = self.siguiente_id()
        nuevo = Formulario2(nuevo_id, id_practica, fecha_real_inicio, fecha_real_fin, horas_cumplidas,
                            calificaciones_rubrica, productos_relevantes, aspectos_relevantes)
        self.formularios[nuevo_id] = nuevo
        self.guardar()
        return nuevo


SECCIONES_F3 = {
    "1": "1.- Aprendizaje relacionado a competencias específicas",
    "2": "2.- Normatividad y Protección del Medio Ambiente",
    "3": "3.- Aprendizaje relacionado a competencias generales",
}

CRITERIOS_F3 = (
    ("1.1", "Reconoce los principales componentes del campo ocupacional.", 3),
    ("1.2", "Identifica los materiales que se utilizan en el área.", 3),
    ("1.3", "Selecciona los materiales correctos según sus aplicaciones.", 3),
    ("1.4", "Determina adecuadamente parámetros, magnitudes y demás.", 3),
    ("1.5", "Utiliza los adecuados procedimientos para la ejecución.", 3),
    ("1.6", "Verifica las condiciones óptimas y adecuadas para la realización.", 2),
    ("1.7", "Posee conocimientos adecuados para el desarrollo de las PPP.", 3),
    ("1.8", "Elabora reportes técnicos finalizados los trabajos.", 3),
    ("1.9", "Posee conocimientos sobre algún software utilizado en su carrera.", 3),
    ("1.10", "Posee un nivel adecuado de la tecnología en equipos, herramientas.", 3),
    ("2.1", "Conoce las normativas generales respecto a la adquisición y manejo.", 2),
    ("2.2", "Comprende los impactos ambientales que puede ocasionar su futura profesión.", 2),
    ("2.3", "Conoce los principales lineamientos sobre el impacto ambiental.", 3),
    ("2.4", "Aplica normas mínimas para reducción de desperdicios y eliminación.", 3),
    ("3.1", "Practica actitudes de disciplina laboral, así como el trabajo colaborativo.", 3),
    ("3.2", "Practica actitudes de respeto a los individuos en términos de tolerancia.", 3),
    ("3.3", "Asocia el accionar laboral con la importancia de una comunicación efectiva.", 4),
    ("3.4", "Aplica los procedimientos, protocolos e instrucciones de seguridad laboral.", 3),
)


class Formulario3:

    def __init__(self, id_formulario3, id_practica, campo_ocupacional, calificacion_sobre_100,
                 evaluacion_escenario, estado="Completado", eliminado=False):
        if not Validaciones.validar_texto_no_vacio(campo_ocupacional):
            raise ValueError("El campo ocupacional no puede estar vacío.")
        if not Validaciones.validar_rango(calificacion_sobre_100, 0, 100):
            raise ValueError("La calificación final debe estar entre 0 y 100.")
        if not (isinstance(evaluacion_escenario, dict) and len(evaluacion_escenario) == len(CRITERIOS_F3)):
            raise ValueError("Debe evaluar los 18 criterios del escenario de la práctica.")
        if not all(map(self._criterio_valido, evaluacion_escenario.values())):
            raise ValueError("Cada criterio requiere 'No Aplica' o un nivel alcanzado entre 1 y 4.")

        self.id_formulario3 = id_formulario3
        self.id_practica = id_practica
        self.campo_ocupacional = campo_ocupacional
        self.calificacion_sobre_100 = calificacion_sobre_100
        self.evaluacion_escenario = evaluacion_escenario
        self.estado = estado
        self.eliminado = eliminado

    @staticmethod
    def _criterio_valido(criterio):
        return (isinstance(criterio, dict) and isinstance(criterio.get("no_aplica"), bool) and
                (criterio["no_aplica"] or Validaciones.validar_rango(criterio.get("nivel_alcanzado"), 1, 4)))

    @staticmethod
    def buscar_por_id(diccionario, id_buscado):
        return diccionario.get(id_buscado, None)

    def __repr__(self):
        return f"Formulario3(id='{self.id_formulario3}', practica='{self.id_practica}', nota={self.calificacion_sobre_100})"


class RepositorioFormulario3:
    ENTIDAD = 'formulario3'

    def __init__(self, persistencia):
        self.persistencia = persistencia
        self.formularios = self.persistencia.cargar(self.ENTIDAD)

    def recargar(self):
        self.formularios = self.persistencia.cargar(self.ENTIDAD)

    def guardar(self):
        self.persistencia.guardar(self.ENTIDAD, self.formularios)

    def listar(self):
        return list(filter(lambda f: not f.eliminado, self.formularios.values()))

    def buscar(self, id_formulario3):
        formulario = Formulario3.buscar_por_id(self.formularios, id_formulario3)
        return formulario if formulario is not None and not formulario.eliminado else None

    def siguiente_id(self):
        return str(max(
            list(map(int, filter(lambda k: k.isdigit(), self.formularios.keys()))),
            default=0) + 1)

    def buscar_por_practica(self, id_practica):
        return next(filter(lambda f: f.id_practica == id_practica and not f.eliminado, self.formularios.values()), None)

    def tiene(self, id_practica):
        return self.buscar_por_practica(id_practica) is not None

    def agregar(self, id_practica, campo_ocupacional, calificacion_sobre_100, evaluacion_escenario):
        if self.tiene(id_practica):
            raise ValueError("El Formulario 3 ya fue registrado para esta práctica.")
        nuevo_id = self.siguiente_id()
        nuevo = Formulario3(nuevo_id, id_practica, campo_ocupacional, calificacion_sobre_100, evaluacion_escenario)
        self.formularios[nuevo_id] = nuevo
        self.guardar()
        return nuevo
