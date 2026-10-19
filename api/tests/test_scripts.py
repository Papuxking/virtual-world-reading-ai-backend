import re
from pathlib import Path

from sqlalchemy import func

from game_rules import DIFFICULTY_ORDER, MAX_SESSION_SCORE
from helpers import crear_lectura, entorno_activo_de_prueba
from models import AchievementCatalog, PlayerSession, PlayerTypologyProgress

RAIZ_API = Path(__file__).resolve().parents[1]


def test_orden_de_tipologias_definido_en_un_solo_sitio():
    ficheros = list(RAIZ_API.glob("*.py")) + list((RAIZ_API / "routers").glob("*.py"))
    definiciones = sorted(
        p.relative_to(RAIZ_API).as_posix()
        for p in ficheros
        if re.search(r"^DIFFICULTY_ORDER\s*=", p.read_text(encoding="utf-8"), re.MULTILINE)
    )
    assert definiciones == ["game_rules.py"]


def test_registro_crea_las_cuatro_filas(client, db):
    entorno_activo_de_prueba(db)  # el registro va al entorno activo
    r = client.post("/auth/register", json={
        "email": "nuevo@test.com", "password": "Test1234!",
        "display_name": "Nuevo", "character": "male",
    })
    assert r.status_code == 201
    filas = db.query(PlayerTypologyProgress).filter_by(user_id=r.json()["id"]).all()
    assert sorted(f.typology for f in filas) == sorted(DIFFICULTY_ORDER)


def test_seed_de_prueba_respeta_el_maximo(db):
    for tipologia in DIFFICULTY_ORDER:
        for i in range(5):
            crear_lectura(db, f"{tipologia} {i}", tipologia)
    import seed_entorno_prueba
    seed_entorno_prueba.sembrar(db)
    db.expire_all()
    assert db.query(func.max(PlayerTypologyProgress.best_score)).scalar() <= MAX_SESSION_SCORE
    assert db.query(func.max(PlayerSession.session_score)).scalar() <= MAX_SESSION_SCORE
    fuera = (
        db.query(PlayerTypologyProgress)
        .filter(PlayerTypologyProgress.typology.notin_(DIFFICULTY_ORDER))
        .count()
    )
    assert fuera == 0
    assert "4 tipologías" in db.get(AchievementCatalog, "explorer").how_to_unlock
