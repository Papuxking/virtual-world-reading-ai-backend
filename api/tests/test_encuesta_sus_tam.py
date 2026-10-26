"""Contrato de la encuesta obligatoria SUS + TAM y su módulo administrativo."""
from game_rules import DIFFICULTY_ORDER, pass_threshold
from helpers import cabeceras, crear_entorno, crear_usuario
from models import PlayerTypologyProgress, TechnologySurveyResponse


def aprobar_las_cuatro(db, usuario, slot):
    for tipologia in DIFFICULTY_ORDER:
        fila = db.query(PlayerTypologyProgress).filter_by(
            user_id=usuario.id, slot_id=slot.id, typology=tipologia).one()
        fila.best_score = pass_threshold(tipologia)
        fila.is_unlocked = True
    db.commit()


def payload(sus=None, pu=None, peou=None):
    return {
        "sus": sus or [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "tam_usefulness": pu or [1, 2, 3, 4, 5, 6],
        "tam_ease": peou or [7, 6, 5, 4, 3, 2],
    }


def test_estado_inicial_y_no_disponible_antes_de_aprobar(client, db):
    usuario, _ = crear_usuario(db)
    headers = cabeceras(usuario)
    assert client.get("/evaluation/survey/status", headers=headers).json() == {
        "completed": False, "submitted_at": None}
    r = client.post("/evaluation/survey", headers=headers, json=payload())
    assert r.status_code == 403 and r.json()["detail"] == "SURVEY_NOT_AVAILABLE"


def test_guarda_una_respuesta_inmutable_y_calcula_escalas(client, db):
    usuario, slot = crear_usuario(db)
    aprobar_las_cuatro(db, usuario, slot)
    headers = cabeceras(usuario)
    r = client.post("/evaluation/survey", headers=headers, json=payload())
    assert r.status_code == 200
    datos = r.json()
    assert datos["completed"] is True
    assert datos["instrument_version"] == "sus10_tam12_v1"
    assert datos["sus_score"] == 50.0
    assert datos["tam_usefulness_score"] == 3.5
    assert datos["tam_ease_score"] == 4.5
    assert client.get("/evaluation/survey/status", headers=headers).json()["completed"] is True

    # Un reintento nunca reemplaza la primera respuesta.
    client.post("/evaluation/survey", headers=headers, json=payload(
        sus=[5] * 10, pu=[7] * 6, peou=[1] * 6))
    fila = db.query(TechnologySurveyResponse).one()
    assert fila.sus_1 == 1 and fila.tam_pu_1 == 1 and fila.tam_peou_1 == 7


def test_valida_cantidad_y_rangos_de_las_22_respuestas(client, db):
    usuario, slot = crear_usuario(db)
    aprobar_las_cuatro(db, usuario, slot)
    headers = cabeceras(usuario)
    assert client.post("/evaluation/survey", headers=headers,
                       json=payload(sus=[3] * 9)).status_code == 422
    assert client.post("/evaluation/survey", headers=headers,
                       json=payload(pu=[8] * 6)).status_code == 422
    assert client.post("/evaluation/survey", headers=headers,
                       json=payload(peou=[0] * 6)).status_code == 422


def test_dashboard_acota_entorno_agrega_items_y_exporta_crudos(client, db):
    a = crear_entorno(db, "Curso A", activo=True)
    b = crear_entorno(db, "Curso B")
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    ua, sa = crear_usuario(db, "ana@test.com", entorno=a)
    ub, sb = crear_usuario(db, "beto@test.com", entorno=b)
    for usuario, slot in ((ua, sa), (ub, sb)):
        aprobar_las_cuatro(db, usuario, slot)
        client.post("/evaluation/survey", headers=cabeceras(usuario), json=payload())

    resumen = client.get("/evaluation/admin/summary", headers=cabeceras(admin, a)).json()
    assert resumen["eligible_slots"] == 1
    assert resumen["responses"] == 1 and resumen["response_rate"] == 100.0
    assert resumen["sus_average"] == 50.0
    assert resumen["item_distributions"]["sus_1"] == [1, 0, 0, 0, 0]
    assert resumen["item_distributions"]["tam_peou_1"] == [0, 0, 0, 0, 0, 0, 1]

    filas = client.get("/evaluation/admin/responses", headers=cabeceras(admin, a)).json()
    assert len(filas) == 1 and filas[0]["email"] == "ana@test.com"
    assert filas[0]["sus"] == [1] * 10
    csv = client.get("/evaluation/admin/export.csv", headers=cabeceras(admin, a))
    assert csv.status_code == 200
    assert "ana@test.com" in csv.text and "beto@test.com" not in csv.text
    assert "sus_10" in csv.text and "tam_peou_6" in csv.text


def test_dashboard_rechaza_alumno_y_sin_token(client, db):
    entorno = crear_entorno(db, "Curso", activo=True)
    alumno, _ = crear_usuario(db, entorno=entorno)
    assert client.get("/evaluation/admin/summary",
                      headers=cabeceras(alumno, entorno)).status_code == 403
    assert client.get("/evaluation/survey/status").status_code == 401


def test_respuesta_sigue_en_denominador_si_reinician_el_progreso(client, db):
    entorno = crear_entorno(db, "Curso", activo=True)
    admin, _ = crear_usuario(db, "admin@test.com", admin=True)
    alumno, slot = crear_usuario(db, entorno=entorno)
    aprobar_las_cuatro(db, alumno, slot)
    client.post("/evaluation/survey", headers=cabeceras(alumno), json=payload())
    db.query(PlayerTypologyProgress).filter_by(user_id=alumno.id, slot_id=slot.id).update(
        {"best_score": 0})
    db.commit()
    resumen = client.get("/evaluation/admin/summary", headers=cabeceras(admin, entorno)).json()
    assert resumen["eligible_slots"] == 1
    assert resumen["responses"] == 1 and resumen["response_rate"] == 100.0
