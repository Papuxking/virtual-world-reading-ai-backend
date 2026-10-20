"""Lo que el jugador habla con el asistente IA queda guardado y el dashboard lo
muestra, solo para los jugadores del entorno que mira."""
from helpers import cabeceras, crear_entorno, crear_lectura, crear_usuario, entorno_activo_de_prueba


def _hablar(client, usuario, lectura, pregunta, respuesta, npc="robot"):
    return client.post("/progress/npc-interaction", headers=cabeceras(usuario), json={
        "npc_type": npc, "reading_id": lectura.id,
        "user_message": pregunta, "assistant_reply": respuesta,
    })


def test_guarda_pregunta_y_respuesta(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db, "El zorro", "Narrativo")
    assert _hablar(client, usuario, lectura, "¿Quién es el protagonista?", "Piensa en quién actúa.").status_code == 201
    _hablar(client, usuario, lectura, "¿Y el final?", "Relee el último párrafo.", npc="sabio")

    entorno = entorno_activo_de_prueba(db)
    r = client.get("/admin/metrics/npc-conversations", params={"player_id": usuario.id},
                   headers=cabeceras(admin, entorno))
    assert r.status_code == 200
    mensajes = r.json()
    assert [m["user_message"] for m in mensajes] == ["¿Quién es el protagonista?", "¿Y el final?"]
    assert mensajes[0]["assistant_reply"] == "Piensa en quién actúa."
    assert mensajes[0]["reading_title"] == "El zorro"
    assert mensajes[1]["npc_type"] == "sabio"


def test_sin_texto_sigue_contando_la_interaccion(client, db):
    """Un juego viejo que no manda el texto sigue registrando la interacción."""
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    r = client.post("/progress/npc-interaction", headers=cabeceras(usuario),
                    json={"npc_type": "robot", "reading_id": lectura.id})
    assert r.status_code == 201


def test_no_muestra_conversaciones_de_otro_entorno(client, db):
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    usuario, _ = crear_usuario(db)
    lectura = crear_lectura(db)
    _hablar(client, usuario, lectura, "Hola", "Hola, ¿en qué te ayudo?")
    otro = crear_entorno(db, "Otro")
    r = client.get("/admin/metrics/npc-conversations", params={"player_id": usuario.id},
                   headers=cabeceras(admin, otro))
    assert r.status_code == 200
    assert r.json() == []
