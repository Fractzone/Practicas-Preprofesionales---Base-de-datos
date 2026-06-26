"""
Eliminación lógica en cascada.

Recorre las dependencias de un estudiante o de una empresa/tutor empresarial y
marca como eliminados (borrado lógico) todos los registros relacionados. La
lectura de los registros relacionados se hace con los repositorios (SQL con
WHERE) y el marcado en lote con UPDATE ... WHERE columna = ANY(...).

Cada cascada es atómica: todos los marcados se hacen dentro de un único bloque
`with persistencia.transaccion():`, de modo que se confirman juntos al final (o
se revierten por completo si algo falla) y nunca quede una eliminación a medias.
"""
from modelo.proceso import RepositorioPostulacion, RepositorioPractica, RepositorioOferta
from modelo.proceso import RepositorioSolicitud

ENTIDADES_FORMULARIO = ("formulario1", "formulario2", "formulario3")


def _eliminar_formularios_de_practicas(persistencia, ids_practicas):
    for entidad in ENTIDADES_FORMULARIO:
        persistencia.marcar_eliminados_por(entidad, "id_practica", ids_practicas)


def por_estudiante(persistencia, cedula):
    postulaciones = RepositorioPostulacion(persistencia).de_estudiante(cedula)
    ids_postulacion = [p.id_postulacion for p in postulaciones]

    practicas = RepositorioPractica(persistencia).de_postulaciones(ids_postulacion)
    ids_practica = [pr.id_practica for pr in practicas]

    with persistencia.transaccion():
        persistencia.marcar_eliminados_por("postulacion", "id_postulacion", ids_postulacion)
        persistencia.marcar_eliminados_por("practica", "id_practica", ids_practica)
        _eliminar_formularios_de_practicas(persistencia, ids_practica)
        persistencia.marcar_eliminados_por("solicitud", "cedula_estudiante", [cedula])


def por_empresa(persistencia, cedula, ruc_empresa):
    ofertas = RepositorioOferta(persistencia).de_empresa(ruc_empresa)
    ids_oferta = [o.id_oferta for o in ofertas]

    postulaciones = RepositorioPostulacion(persistencia).de_ofertas(ids_oferta)
    ids_postulacion = [p.id_postulacion for p in postulaciones]

    practicas = RepositorioPractica(persistencia).de_tutor_empresarial(cedula)
    ids_practica = [pr.id_practica for pr in practicas]

    with persistencia.transaccion():
        persistencia.marcar_eliminados_por("oferta", "id_oferta", ids_oferta)
        persistencia.marcar_eliminados_por("postulacion", "id_postulacion", ids_postulacion)
        persistencia.marcar_eliminados_por("practica", "id_practica", ids_practica)
        _eliminar_formularios_de_practicas(persistencia, ids_practica)
