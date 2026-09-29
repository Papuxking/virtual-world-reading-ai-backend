from database import engine


def test_la_base_es_la_de_pruebas():
    assert engine.url.database.endswith("_test")


def test_health_responde_con_la_base_de_pruebas(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["database"] == "connected"
