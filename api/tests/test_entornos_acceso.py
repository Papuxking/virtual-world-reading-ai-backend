"""Quién entra al juego: solo los jugadores del entorno activo (los
administradores, siempre). El registro crea la cuenta en el entorno activo, y
un jugador cuyo entorno se apaga queda fuera en su siguiente petición."""
from auth import hash_password
from helpers import cabeceras, crear_entorno, crear_usuario
from models import PlayerSlot, PlayerTypologyProgress, User
from routers import leaderboard_router

NO_PERTENECE = "Tu cuenta no pertenece al entorno activo del juego."
NO_DISPONIBLE = "El juego no está disponible en este momento."
YA_EXISTE = "Ya existe un usuario con ese correo electrónico"


def _login(client, email, clave="Test1234!"):
    return client.post("/auth/login", json={"email": email, "password": clave})


def _registro(client, email="nuevo@test.com"):
    return client.post("/auth/register", json={
        "email": email, "password": "Nueva1234", "display_name": "Nuevo", "character": "male",
    })


def test_login_jugador_del_activo(client, db):
    a = crear_entorno(db, "A", activo=True)
    usuario, _ = crear_usuario(db, "uno@test.com", entorno=a)
    r = _login(client, "uno@test.com")
    assert r.status_code == 200
    assert r.json()["user"]["id"] == usuario.id


def test_login_admin_sin_entorno_activo(client, db):
    crear_usuario(db, "admin@test.com", admin=True)
    assert _login(client, "admin@test.com").status_code == 200


def test_login_cuenta_de_otro_entorno(client, db):
    crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    crear_usuario(db, "uno@test.com", entorno=b)
    r = _login(client, "uno@test.com")
    assert r.status_code == 403
    assert r.json()["detail"] == NO_PERTENECE


def test_login_cuenta_sin_entorno(client, db):
    crear_entorno(db, "A", activo=True)
    crear_usuario(db, "viejo@test.com", entorno=False)
    r = _login(client, "viejo@test.com")
    assert r.status_code == 403
    assert r.json()["detail"] == NO_PERTENECE


def test_login_contrasena_mala_no_revela(client, db):
    crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    crear_usuario(db, "uno@test.com", entorno=b)
    for email, clave in (("uno@test.com", "Otra1234!"), ("nadie@test.com", "Test1234!")):
        r = _login(client, email, clave)
        assert r.status_code == 401
        assert r.json()["detail"] == "Correo o contraseña incorrectos"


def test_login_mismo_correo_en_activo_y_otro(client, db):
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    del_activo, _ = crear_usuario(db, "uno@test.com", entorno=a)
    del_otro, _ = crear_usuario(db, "uno@test.com", entorno=b)
    del_otro.hashed_password = hash_password("Otra1234!")
    db.commit()
    r = _login(client, "uno@test.com")
    assert r.status_code == 200
    assert r.json()["user"]["id"] == del_activo.id
    # Con la contraseña de la cuenta del otro entorno: incorrecta, sin más.
    assert _login(client, "uno@test.com", "Otra1234!").status_code == 401


def test_login_sin_entorno_activo(client, db):
    b = crear_entorno(db, "B")
    crear_usuario(db, "uno@test.com", entorno=b)
    r = _login(client, "uno@test.com")
    assert r.status_code == 403
    assert r.json()["detail"] == NO_DISPONIBLE


def test_registro_va_al_activo(client, db):
    a = crear_entorno(db, "A", activo=True)
    r = _registro(client)
    assert r.status_code == 201
    usuario = db.query(User).filter_by(email="nuevo@test.com").one()
    assert usuario.workspace_id == a.id
    assert db.query(PlayerSlot).filter_by(user_id=usuario.id, is_active=True).count() == 1
    filas = db.query(PlayerTypologyProgress).filter_by(user_id=usuario.id).all()
    assert sorted((f.typology, f.is_unlocked) for f in filas) == [
        ("Argumentativo", False), ("Descriptivo", False), ("Expositivo", False), ("Narrativo", True),
    ]


def test_registro_correo_de_otro_entorno_crea_cuenta_nueva(client, db):
    crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    crear_usuario(db, "nuevo@test.com", entorno=b)
    assert _registro(client).status_code == 201
    assert db.query(User).filter_by(email="nuevo@test.com").count() == 2


def test_registro_correo_repetido_en_el_activo(client, db):
    a = crear_entorno(db, "A", activo=True)
    crear_usuario(db, "nuevo@test.com", entorno=a)
    r = _registro(client)
    assert r.status_code == 409
    assert r.json()["detail"] == YA_EXISTE


def test_registro_correo_de_admin(client, db):
    crear_entorno(db, "A", activo=True)
    crear_usuario(db, "nuevo@test.com", admin=True)
    r = _registro(client)
    assert r.status_code == 409
    assert r.json()["detail"] == YA_EXISTE


def test_registro_sin_entorno_activo(client, db):
    crear_entorno(db, "B")
    r = _registro(client)
    assert r.status_code == 403
    assert r.json()["detail"] == NO_DISPONIBLE


def test_peticion_con_entorno_apagado(client, db):
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    usuario, _ = crear_usuario(db, "uno@test.com", entorno=a)
    assert client.get("/progress/validate-session", headers=cabeceras(usuario)).status_code == 200
    a.is_active = False
    db.commit()
    b.is_active = True
    db.commit()
    for ruta in ("/progress/validate-session", "/progress/me", "/auth/me"):
        r = client.get(ruta, headers=cabeceras(usuario))
        assert r.status_code == 409, ruta
        assert r.json()["detail"] == "WORKSPACE_INACTIVE"


def test_admin_no_recibe_workspace_inactive(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    crear_entorno(db, "B")
    assert client.get("/auth/me", headers=cabeceras(admin)).status_code == 200


def test_ranking_solo_del_activo_y_cache_por_entorno(client, db):
    leaderboard_router._cache.clear()
    a = crear_entorno(db, "A", activo=True)
    b = crear_entorno(db, "B")
    de_a, slot_a = crear_usuario(db, "a@test.com", entorno=a)
    de_b, slot_b = crear_usuario(db, "b@test.com", entorno=b)
    for slot, puntaje in ((slot_a, 200), (slot_b, 150)):
        fila = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id, typology="Narrativo").one()
        fila.best_score = puntaje
    db.commit()

    r = client.get("/leaderboard/top", headers=cabeceras(de_a))
    assert [p["display_name"] for p in r.json()["players"]] == ["a"]

    a.is_active = False
    db.commit()
    b.is_active = True
    db.commit()
    # Dentro de los 60 s de caché: la del entorno A no sirve para el B.
    r = client.get("/leaderboard/top", headers=cabeceras(de_b))
    assert [p["display_name"] for p in r.json()["players"]] == ["b"]
