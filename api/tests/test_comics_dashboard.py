"""Endpoints del módulo de cómics del dashboard: resumen y jugadores, acotados
al entorno que mira el administrador."""
from datetime import datetime, timezone

from game_rules import DIFFICULTY_ORDER, pass_threshold
from helpers import cabeceras, crear_entorno, crear_usuario
from models import ComicProgress, ComicZoneVisit, PlayerTypologyProgress


def aprobar_las_cuatro(db, usuario, slot):
    for tipologia in DIFFICULTY_ORDER:
        fila = (
            db.query(PlayerTypologyProgress)
            .filter_by(user_id=usuario.id, slot_id=slot.id, typology=tipologia)
            .one()
        )
        fila.best_score = pass_threshold(tipologia)
        fila.is_unlocked = True
    db.commit()


def entrar(db, usuario, slot, visitas=1):
    db.add(ComicZoneVisit(user_id=usuario.id, slot_id=slot.id, visits=visitas,
                          last_visit_at=datetime(2026, 10, 20, tzinfo=timezone.utc)))
    db.commit()


def leer(db, usuario, slot, episodio, pagina, terminado=False):
    db.add(ComicProgress(user_id=usuario.id, slot_id=slot.id, episode_id=episodio,
                         last_page=pagina, finished=terminado))
    db.commit()


def test_resumen_distingue_desbloqueo_entrada_y_lectura(client, db):
    entorno = crear_entorno(db, "Curso A", activo=True)
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    aprueba, s1 = crear_usuario(db, "a@test.com", entorno=entorno)
    entra, s2 = crear_usuario(db, "b@test.com", entorno=entorno)
    lee, s3 = crear_usuario(db, "c@test.com", entorno=entorno)
    for u, s in ((aprueba, s1), (entra, s2), (lee, s3)):
        aprobar_las_cuatro(db, u, s)
    entrar(db, entra, s2)
    entrar(db, lee, s3)
    leer(db, lee, s3, "ep01", 4, terminado=True)
    leer(db, lee, s3, "ep02", 2)

    r = client.get("/comics/admin/resumen", headers=cabeceras(admin, entorno)).json()
    assert (r["desbloquearon"], r["entraron"], r["lectores"]) == (3, 2, 1)
    assert {e["episode_id"]: e["lecturas"] for e in r["episodios_top"]} == {"ep01": 1, "ep02": 1}


def test_resumen_de_entorno_sin_lectores_devuelve_ceros(client, db):
    entorno = crear_entorno(db, "Vacío", activo=True)
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    crear_usuario(db, "a@test.com", entorno=entorno)
    r = client.get("/comics/admin/resumen", headers=cabeceras(admin, entorno))
    assert r.status_code == 200
    assert r.json() == {"desbloquearon": 0, "entraron": 0, "lectores": 0, "episodios_top": []}
    assert client.get("/comics/admin/jugadores", headers=cabeceras(admin, entorno)).json() == []


def test_tres_tipologias_no_bastan_para_desbloquear(client, db):
    entorno = crear_entorno(db, "Curso A", activo=True)
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    u, s = crear_usuario(db, "a@test.com", entorno=entorno)
    aprobar_las_cuatro(db, u, s)
    ultima = db.query(PlayerTypologyProgress).filter_by(
        user_id=u.id, typology=DIFFICULTY_ORDER[-1]).one()
    ultima.best_score = pass_threshold(DIFFICULTY_ORDER[-1]) - 1
    db.commit()
    r = client.get("/comics/admin/resumen", headers=cabeceras(admin, entorno)).json()
    assert r["desbloquearon"] == 0


def test_jugadores_no_mezcla_entornos(client, db):
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    ua, sa = crear_usuario(db, "ana@test.com", entorno=a)
    ub, sb = crear_usuario(db, "beto@test.com", entorno=b)
    for u, s in ((ua, sa), (ub, sb)):
        aprobar_las_cuatro(db, u, s)
        entrar(db, u, s)
    leer(db, ua, sa, "ep01", 5, terminado=True)
    leer(db, ua, sa, "ep02", 3)
    leer(db, ub, sb, "ep01", 9, terminado=True)

    filas = client.get("/comics/admin/jugadores", headers=cabeceras(admin, a)).json()
    assert [f["email"] for f in filas] == ["ana@test.com"]
    assert filas[0]["episodios_terminados"] == 1
    assert filas[0]["paginas_leidas"] == 8
    assert filas[0]["ultima_visita"] is not None
    resumen = client.get("/comics/admin/resumen", headers=cabeceras(admin, a)).json()
    assert (resumen["desbloquearon"], resumen["entraron"], resumen["lectores"]) == (1, 1, 1)
    assert resumen["episodios_top"][0] == {"episode_id": "ep01", "lecturas": 1}


def test_endpoints_admin_rechazan_a_un_alumno(client, db):
    entorno = crear_entorno(db, "A", activo=True)
    alumno, _ = crear_usuario(db, "alumno@test.com", entorno=entorno)
    for ruta in ("/comics/admin/resumen", "/comics/admin/jugadores"):
        assert client.get(ruta, headers=cabeceras(alumno, entorno)).status_code == 403


def test_id_de_episodio_demasiado_largo_es_422(client, db):
    usuario, _ = crear_usuario(db)
    r = client.put("/comics/progress/" + "e" * 21, json={"last_page": 1}, headers=cabeceras(usuario))
    assert r.status_code == 422
