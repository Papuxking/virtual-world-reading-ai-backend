"""El perfil se valida con los desbloqueos de la partida, también al publicarlo."""
import pytest

from helpers import cabeceras, crear_usuario
from models import AchievementCatalog, PlayerAchievement, PlayerSlot, PlayerTypologyProgress
from routers.leaderboard_router import _cache


def test_perfil_por_defecto_y_alias_nulo(client, db):
    usuario, _ = crear_usuario(db)
    headers = cabeceras(usuario)
    assert client.get('/progress/profile', headers=headers).json() == {'alias': None, 'vitrina': []}
    assert client.put('/progress/profile', headers=headers, json={
        'alias': 'intuicion', 'vitrina': [],
    }).status_code == 200
    assert client.put('/progress/profile', headers=headers, json={
        'alias': None, 'vitrina': [],
    }).json() == {'alias': None, 'vitrina': []}


@pytest.mark.parametrize('cuerpo', [
    {'alias': 'inexistente'}, {'alias': 'interes'},
    {'vitrina': [{'tipo': 'medalla', 'id': 'medalla_narrativo'}]},
    {'vitrina': [{'tipo': 'logro', 'id': 'ajeno'}]},
    {'vitrina': [{'tipo': 'otro', 'id': 'x'}]},
    {'vitrina': [{'tipo': 'logro', 'id': 'x'}] * 2},
    {'vitrina': [{'tipo': 'logro', 'id': str(i)} for i in range(4)]},
])
def test_rechaza_perfil_invalido_sin_guardarlo(client, db, cuerpo):
    usuario, slot = crear_usuario(db)
    assert client.put('/progress/profile', headers=cabeceras(usuario), json=cuerpo).status_code == 422
    db.refresh(slot)
    assert slot.alias is None and slot.vitrina == []


def test_alias_suma_tipologias_y_vitrina_resuelta(client, db):
    usuario, slot = crear_usuario(db)
    filas = db.query(PlayerTypologyProgress).filter_by(slot_id=slot.id).all()
    filas[0].total_sessions = 2
    filas[0].best_score = 300
    filas[1].total_sessions = 1
    db.add(AchievementCatalog(
        id='lector', name='Lector', description='Lee', how_to_unlock='Lee',
        category='general', medal_name='Lector', icon='📖',
        medal_image_path='/static/medals/lector.png',
    ))
    db.add(PlayerAchievement(user_id=usuario.id, slot_id=slot.id,
                             achievement_id='lector', achievement_name='Lector'))
    db.commit()
    cuerpo = {'alias': 'curiosidad', 'vitrina': [
        {'tipo': 'logro', 'id': 'lector'},
        {'tipo': 'medalla', 'id': 'medalla_narrativo'},
    ]}
    headers = cabeceras(usuario)
    assert client.put('/progress/profile', headers=headers, json=cuerpo).json() == cuerpo
    assert client.get('/progress/profile', headers=headers).json() == cuerpo
    _cache.clear()
    try:
        jugador = client.get('/leaderboard/top', headers=headers).json()['players'][0]
        assert jugador['alias'] == 'Curiosidad'
        assert jugador['vitrina'][0] == {
            'tipo': 'logro', 'id': 'lector', 'nombre': 'Lector', 'emoji': '📖',
            'tier': 'bronce', 'imagen': '/static/medals/lector.png',
        }
        assert jugador['vitrina'][1]['tier'] == 'plata'
    finally:
        _cache.clear()


def test_no_hereda_desbloqueos_de_otro_slot(client, db):
    usuario, anterior = crear_usuario(db)
    anterior.is_active = False
    db.add(PlayerTypologyProgress(user_id=usuario.id, slot_id=anterior.id,
                                  typology='Extra', total_sessions=20))
    db.add(PlayerAchievement(user_id=usuario.id, slot_id=anterior.id,
                             achievement_id='lector', achievement_name='Lector'))
    nuevo = PlayerSlot(user_id=usuario.id, slot_number=2, is_active=True)
    db.add(nuevo)
    db.commit()
    headers = cabeceras(usuario)
    assert client.get('/progress/profile', headers=headers).json() == {'alias': None, 'vitrina': []}
    for cuerpo in ({'alias': 'interes'}, {'vitrina': [{'tipo': 'logro', 'id': 'lector'}]}):
        assert client.put('/progress/profile', headers=headers, json=cuerpo).status_code == 422
    headers['X-Slot-Id'] = str(anterior.id)
    assert client.put('/progress/profile', headers=headers, json={}).status_code == 409
    assert client.get('/progress/profile', headers=headers).status_code == 409
