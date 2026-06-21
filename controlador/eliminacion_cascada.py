from modelo.proceso import RepositorioPostulacion, RepositorioPractica, RepositorioOferta, RepositorioSolicitud
from modelo.formulario import RepositorioFormulario1, RepositorioFormulario2, RepositorioFormulario3

REPOS_FORMULARIO = (RepositorioFormulario1, RepositorioFormulario2, RepositorioFormulario3)


def _marcar(objetos):
    list(map(lambda o: setattr(o, "eliminado", True), objetos))


def _eliminar_formularios_de_practicas(persistencia, ids_practicas):
    def eliminar_en(Repo):
        repo = Repo(persistencia)
        formularios = list(filter(None, map(repo.buscar_por_practica, ids_practicas)))
        _marcar(formularios)
        repo.guardar()
    list(map(eliminar_en, REPOS_FORMULARIO))


def por_estudiante(persistencia, cedula):
    repo_post = RepositorioPostulacion(persistencia)
    postulaciones = repo_post.de_estudiante(cedula)
    _marcar(postulaciones)
    repo_post.guardar()

    repo_pract = RepositorioPractica(persistencia)
    practicas = repo_pract.de_postulaciones([p.id_postulacion for p in postulaciones])
    _marcar(practicas)
    repo_pract.guardar()

    _eliminar_formularios_de_practicas(persistencia, [pr.id_practica for pr in practicas])

    repo_sol = RepositorioSolicitud(persistencia)
    solicitudes = repo_sol.de_estudiante(cedula)
    list(map(lambda s: s.__setitem__("eliminado", True), solicitudes))
    repo_sol.guardar()


def por_empresa(persistencia, cedula, ruc_empresa):
    repo_of = RepositorioOferta(persistencia)
    ofertas = repo_of.de_empresa(ruc_empresa)
    _marcar(ofertas)
    repo_of.guardar()

    repo_post = RepositorioPostulacion(persistencia)
    postulaciones = repo_post.de_ofertas([o.id_oferta for o in ofertas])
    _marcar(postulaciones)
    repo_post.guardar()

    repo_pract = RepositorioPractica(persistencia)
    practicas = repo_pract.de_tutor_empresarial(cedula)
    _marcar(practicas)
    repo_pract.guardar()

    _eliminar_formularios_de_practicas(persistencia, [pr.id_practica for pr in practicas])
