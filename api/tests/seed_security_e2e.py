"""Datos sintéticos exclusivamente para la pila desechable vw-security-test."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ['DATABASE_URL'] = os.environ['TEST_DATABASE_URL']
from database import Base, SessionLocal, engine
from models import AchievementCatalog
from catalogo_logros import INITIAL_ACHIEVEMENTS
from helpers import crear_usuario, crear_lectura
from game_rules import DIFFICULTY_ORDER

if engine.url.database != 'vw_security_test' or engine.url.host != 'test-db':
    raise RuntimeError('Solo se permite la base desechable de esta auditoría')
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)
with SessionLocal() as db:
    admin, _ = crear_usuario(db, 'security-admin@example.com', admin=True)
    player, _ = crear_usuario(db, 'security-player@example.com')
    for typology in DIFFICULTY_ORDER:
        crear_lectura(db, 'Lectura de seguridad ' + typology, typology)
    for achievement in INITIAL_ACHIEVEMENTS:
        db.add(AchievementCatalog(**achievement))
    db.commit()
    print('Datos sintéticos preparados; admin_id=%s player_id=%s' % (admin.id, player.id))
