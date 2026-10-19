"""Administración de entornos: crear (nace inactivo), editar, activar uno solo,
apagar, eliminar (solo inactivo, no el último y con el nombre exacto, borrando
sus cuentas con todo lo suyo) y alta de jugadores con contraseña temporal."""
from helpers import cabeceras, crear_entorno, crear_lectura, crear_usuario, payload_sesion
from models import (
    ActiveReading, NpcInteraction, PlayerAchievement, PlayerAnswer, PlayerNote,
    PlayerSession, PlayerSlot, PlayerTypologyProgress, SessionTool, User, Workspace,
)

NO_PERTENECE = "Tu cuenta no pertenece al entorno activo del juego."


def _admin(db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    return admin, cabeceras(admin)


def _alta(client, h, entorno, jugadores):
    return client.post(f"/admin/workspaces/{entorno.id}/players", json={"players": jugadores}, headers=h)


def test_crear_entorno_nace_inactivo(client, db):
    _, h = _admin(db)
    r = client.post("/admin/workspaces", json={"name": "Pruebas", "color": "#d97706"}, headers=h)
    assert r.status_code == 201
    datos = r.json()
    assert (datos["name"], datos["color"], datos["is_active"], datos["player_count"]) == (
        "Pruebas", "#d97706", False, 0,
    )


def test_crear_entorno_valida_nombre_y_color(client, db):
    _, h = _admin(db)
    for cuerpo in (
        {"name": "   ", "color": "#059669"},
        {"name": "x" * 41, "color": "#059669"},
        {"name": "Real", "color": "#000000"},
    ):
        assert client.post("/admin/workspaces", json=cuerpo, headers=h).status_code == 422, cuerpo
    r = client.post("/admin/workspaces", json={"name": "  Real 2026  ", "color": "#059669"}, headers=h)
    assert r.status_code == 201
    assert r.json()["name"] == "Real 2026"


def test_crear_entorno_nombre_repetido(client, db):
    _, h = _admin(db)
    client.post("/admin/workspaces", json={"name": "Pruebas", "color": "#d97706"}, headers=h)
    r = client.post("/admin/workspaces", json={"name": "pruebas", "color": "#2563eb"}, headers=h)
    assert r.status_code == 409
    assert r.json()["detail"] == "Ya existe un entorno con ese nombre."


def test_editar_entorno(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A")
    crear_entorno(db, "B")
    r = client.patch(f"/admin/workspaces/{a.id}", json={"name": "Real", "color": "#2563eb"}, headers=h)
    assert r.status_code == 200
    assert (r.json()["name"], r.json()["color"]) == ("Real", "#2563eb")
    assert client.patch(f"/admin/workspaces/{a.id}", json={"name": "b"}, headers=h).status_code == 409
    assert client.patch(f"/admin/workspaces/{a.id}", json={"color": "#123456"}, headers=h).status_code == 422
    r = client.patch("/admin/workspaces/9999", json={"name": "Z"}, headers=h)
    assert r.status_code == 404
    assert r.json()["detail"] == "Entorno no encontrado"


def test_listar_cuenta_los_jugadores(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A")
    crear_entorno(db, "B")
    crear_usuario(db, "uno@test.com", entorno=a)
    crear_usuario(db, "dos@test.com", entorno=a)
    r = client.get("/admin/workspaces", headers=h)
    assert {w["name"]: w["player_count"] for w in r.json()} == {"A": 2, "B": 0}


def test_activar_apaga_los_demas(client, db):
    _, h = _admin(db)
    crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    r = client.post(f"/admin/workspaces/{b.id}/activate", headers=h)
    assert r.status_code == 200
    assert [w["name"] for w in r.json() if w["is_active"]] == ["B"]


def test_desactivar_deja_ninguno(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A", activo=True)
    r = client.post(f"/admin/workspaces/{a.id}/deactivate", headers=h)
    assert r.status_code == 200
    assert [w for w in r.json() if w["is_active"]] == []


def test_eliminar_reglas(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    r = client.delete(f"/admin/workspaces/{a.id}", params={"confirm_name": "A"}, headers=h)
    assert (r.status_code, r.json()["detail"]) == (409, "No se puede eliminar el entorno activo.")
    r = client.delete(f"/admin/workspaces/{b.id}", params={"confirm_name": "b"}, headers=h)
    assert (r.status_code, r.json()["detail"]) == (400, "El nombre no coincide.")
    assert client.delete(f"/admin/workspaces/{b.id}", params={"confirm_name": "B"}, headers=h).status_code == 204
    client.post(f"/admin/workspaces/{a.id}/deactivate", headers=h)
    r = client.delete(f"/admin/workspaces/{a.id}", params={"confirm_name": "A"}, headers=h)
    assert (r.status_code, r.json()["detail"]) == (409, "No se puede eliminar el último entorno.")


def test_eliminar_borra_todo_lo_del_entorno(client, db):
    admin, h = _admin(db)
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    jugador, slot = crear_usuario(db, "uno@test.com", entorno=a)
    crear_usuario(db, "dos@test.com", entorno=b)
    lectura = crear_lectura(db, "Lectura")
    r = client.post("/progress/sessions", json=payload_sesion(db, lectura), headers=cabeceras(jugador))
    assert r.status_code == 201
    sesion_id = r.json()["id"]
    db.add_all([
        PlayerNote(user_id=jugador.id, slot_id=slot.id, reading_id=lectura.id,
                   session_id=sesion_id, note_content="Nota"),
        NpcInteraction(user_id=jugador.id, slot_id=slot.id, npc_type="sabio", reading_id=lectura.id),
        ActiveReading(user_id=jugador.id, slot_id=slot.id, reading_id=lectura.id, typology="Narrativo"),
        PlayerAchievement(user_id=jugador.id, slot_id=slot.id, achievement_id="first_reading",
                          achievement_name="Primera lectura"),
        PlayerSlot(user_id=jugador.id, slot_number=2, label="Sesión 2", is_active=False,
                   created_by=admin.id),
    ])
    db.commit()
    jugador_id, a_id = jugador.id, a.id

    client.post(f"/admin/workspaces/{b.id}/activate", headers=h)
    r = client.delete(f"/admin/workspaces/{a_id}", params={"confirm_name": "A"}, headers=h)
    assert r.status_code == 204

    db.expire_all()
    assert db.get(Workspace, a_id) is None
    assert db.get(User, jugador_id) is None
    for modelo in (PlayerSlot, PlayerSession, PlayerNote, NpcInteraction, ActiveReading,
                   PlayerAchievement, PlayerTypologyProgress):
        assert db.query(modelo).filter(modelo.user_id == jugador_id).count() == 0, modelo.__name__
    assert db.query(PlayerAnswer).filter_by(session_id=sesion_id).count() == 0
    assert db.query(SessionTool).filter_by(session_id=sesion_id).count() == 0
    # Lo del otro entorno y el administrador siguen ahí.
    assert db.query(User).filter_by(email="dos@test.com").count() == 1
    assert db.get(User, admin.id) is not None


def test_alta_de_jugadores(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A", activo=True)
    r = _alta(client, h, a, [{"email": "ana@x.com", "display_name": "Ana Torres"}, {"email": "luis@x.com"}])
    assert r.status_code == 200
    assert r.json()["skipped"] == []
    creados = {c["email"]: c for c in r.json()["created"]}
    assert set(creados) == {"ana@x.com", "luis@x.com"}
    assert creados["ana@x.com"]["display_name"] == "Ana Torres"
    assert creados["luis@x.com"]["display_name"] == "luis"
    assert all(len(c["temp_password"]) == 10 for c in creados.values())

    luis = db.query(User).filter_by(email="luis@x.com").one()
    assert luis.workspace_id == a.id
    assert luis.must_change_password is True
    assert db.query(PlayerSlot).filter_by(user_id=luis.id, slot_number=1, is_active=True).count() == 1
    assert db.query(PlayerTypologyProgress).filter_by(user_id=luis.id).count() == 4

    r = client.post("/auth/login", json={"email": "luis@x.com", "password": creados["luis@x.com"]["temp_password"]})
    assert r.status_code == 200
    assert r.json()["must_change_password"] is True


def test_alta_de_jugadores_texto_desordenado(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A", activo=True)
    crear_usuario(db, "ya@x.com", entorno=a)
    r = _alta(client, h, a, [
        {"email": "no-es-un-correo"},
        {"email": "  ana@X.com  ", "display_name": "  Ana  "},
        {"email": "ana@x.com", "display_name": "Otra Ana"},
        {"email": "ya@x.com"},
        {"email": "admin@test.com"},
        {"email": ""},
    ])
    assert r.status_code == 200
    assert [(c["email"], c["display_name"]) for c in r.json()["created"]] == [("ana@x.com", "Ana")]
    assert [(s["email"], s["reason"]) for s in r.json()["skipped"]] == [
        ("no-es-un-correo", "el correo no es válido"),
        ("ana@x.com", "está repetido en la lista"),
        ("ya@x.com", "ya tiene cuenta en este entorno"),
        ("admin@test.com", "es el correo de un administrador"),
        ("", "el correo no es válido"),
    ]


def test_alta_en_entorno_inactivo(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A")
    crear_entorno(db, "B", activo=True)
    r = _alta(client, h, a, [{"email": "luis@x.com"}])
    clave = r.json()["created"][0]["temp_password"]
    r = client.post("/auth/login", json={"email": "luis@x.com", "password": clave})
    assert (r.status_code, r.json()["detail"]) == (403, NO_PERTENECE)
    client.post(f"/admin/workspaces/{a.id}/activate", headers=h)
    assert client.post("/auth/login", json={"email": "luis@x.com", "password": clave}).status_code == 200


def test_alta_tamano_de_la_lista(client, db):
    _, h = _admin(db)
    a = crear_entorno(db, "A")
    muchos = [{"email": f"alumno{i}@x.com"} for i in range(201)]
    assert _alta(client, h, a, muchos).status_code == 422
    assert _alta(client, h, a, []).status_code == 422
    r = client.post("/admin/workspaces/9999/players", json={"players": [{"email": "a@x.com"}]}, headers=h)
    assert r.status_code == 404


def test_endpoints_de_entornos_solo_admin(client, db):
    jugador, _ = crear_usuario(db, "uno@test.com")
    assert client.get("/admin/workspaces", headers=cabeceras(jugador)).status_code == 403
