"""Progreso de la zona de cómics (migración 015): una fila por episodio, jugador
y slot, y otra con las visitas a la sala. Todo se borra con el usuario."""
import pytest
from sqlalchemy.exc import IntegrityError

from helpers import crear_usuario
from models import ComicProgress, ComicZoneVisit, User


def test_progreso_unico_por_episodio_y_slot(db):
    usuario, slot = crear_usuario(db)
    db.add(ComicProgress(user_id=usuario.id, slot_id=slot.id, episode_id="ep01", last_page=2))
    db.commit()
    db.add(ComicProgress(user_id=usuario.id, slot_id=slot.id, episode_id="ep01"))
    with pytest.raises(IntegrityError):
        db.commit()


def test_visitas_unicas_por_jugador_y_slot(db):
    usuario, slot = crear_usuario(db)
    db.add(ComicZoneVisit(user_id=usuario.id, slot_id=slot.id))
    db.commit()
    db.add(ComicZoneVisit(user_id=usuario.id, slot_id=slot.id))
    with pytest.raises(IntegrityError):
        db.commit()


def test_valores_por_defecto(db):
    usuario, slot = crear_usuario(db)
    db.add_all([
        ComicProgress(user_id=usuario.id, slot_id=slot.id, episode_id="ep01"),
        ComicZoneVisit(user_id=usuario.id, slot_id=slot.id),
    ])
    db.commit()
    progreso = db.query(ComicProgress).one()
    visita = db.query(ComicZoneVisit).one()
    assert (progreso.last_page, progreso.finished) == (0, False)
    assert progreso.created_at is not None and progreso.updated_at is not None
    assert visita.visits == 1
    assert visita.first_visit_at is not None and visita.last_visit_at is not None


def test_borrar_usuario_arrastra_su_progreso_de_comics(db):
    usuario, slot = crear_usuario(db)
    db.add_all([
        ComicProgress(user_id=usuario.id, slot_id=slot.id, episode_id="ep01", last_page=3),
        ComicZoneVisit(user_id=usuario.id, slot_id=slot.id, visits=4),
    ])
    db.commit()
    db.delete(db.get(User, usuario.id))
    db.commit()
    assert db.query(ComicProgress).count() == 0
    assert db.query(ComicZoneVisit).count() == 0
