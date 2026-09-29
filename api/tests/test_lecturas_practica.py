from helpers import crear_lectura


def test_random_full_sin_parametro_solo_da_progresion(client, db):
    crear_lectura(db, "Progresión", "Narrativo")
    crear_lectura(db, "Práctica", "Narrativo", practica=True)
    for _ in range(15):
        r = client.get("/readings/random/full", params={"typology": "Narrativo"})
        assert r.status_code == 200
        assert r.json()["title"] == "Progresión"
        assert r.json()["is_practice"] is False


def test_random_full_con_practice_solo_da_practica(client, db):
    crear_lectura(db, "Progresión", "Narrativo")
    crear_lectura(db, "Práctica", "Narrativo", practica=True)
    for _ in range(15):
        r = client.get("/readings/random/full", params={"typology": "Narrativo", "practice": "true"})
        assert r.status_code == 200
        assert r.json()["title"] == "Práctica"
        assert r.json()["is_practice"] is True


def test_random_full_practice_sin_lecturas_da_404(client, db):
    crear_lectura(db, "Progresión", "Expositivo")
    r = client.get("/readings/random/full", params={"typology": "Expositivo", "practice": "true"})
    assert r.status_code == 404


def test_random_simple_respeta_la_marca(client, db):
    crear_lectura(db, "Progresión", "Descriptivo")
    crear_lectura(db, "Práctica", "Descriptivo", practica=True)
    for _ in range(10):
        normal = client.get("/readings/random", params={"typology": "Descriptivo"})
        practica = client.get("/readings/random", params={"typology": "Descriptivo", "practice": "true"})
        assert normal.json()["title"] == "Progresión"
        assert practica.json()["title"] == "Práctica"


def test_lectura_por_id_expone_la_marca(client, db):
    practica = crear_lectura(db, "Práctica", "Narrativo", practica=True)
    assert client.get(f"/readings/{practica.id}").json()["is_practice"] is True
    assert client.get(f"/readings/{practica.id}/full").json()["is_practice"] is True


def test_typologies_cuenta_solo_progresion(client, db):
    crear_lectura(db, "P1", "Narrativo")
    crear_lectura(db, "Práctica", "Narrativo", practica=True)
    conteo = {t["name"]: t["count"] for t in client.get("/typologies").json()["typologies"]}
    assert conteo["Narrativo"] == 1
