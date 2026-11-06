"""Regresión de los hallazgos: autorización, sesiones y evaluación autoritativa."""
import io
from unittest.mock import Mock
import pytest
from fastapi import HTTPException
from openpyxl import Workbook, load_workbook
from auth import ADMIN_COOKIE, hash_password, verify_password
from helpers import cabeceras, crear_lectura, crear_usuario
from models import GameAttempt, PlayerSession
from safe_exports import SafeWriter, secure_workbook
from safe_images import resize_image_to_256


def _login(client, email, admin=False):
    return client.post('/auth/admin/login' if admin else '/auth/login', json={'email': email, 'password': 'Test1234!'})


def test_crud_requiere_admin(client, db):
    player, _ = crear_usuario(db)
    reading = crear_lectura(db)
    for method, path, body in [('post', '/readings', {'title': 'X', 'typology': 'Narrativo', 'content': 'x'*100}),
                                ('put', f'/readings/{reading.id}', {'title': 'X'}),
                                ('delete', f'/readings/{reading.id}', None)]:
        args = {'json': body} if body is not None else {}
        assert getattr(client, method)(path, **args).status_code == 401
        assert getattr(client, method)(path, headers=cabeceras(player), **args).status_code == 403


def test_token_previo_no_revive_al_omitir_cabeceras(client, db):
    player, _ = crear_usuario(db)
    old = cabeceras(player)
    response = _login(client, player.email)
    assert response.status_code == 200
    assert client.get('/progress/me', headers=old).status_code == 409
    old.update({'X-Session-Version': '999999', 'X-Slot-Id': '1'})
    assert client.get('/progress/me', headers=old).status_code == 409
    assert client.get('/progress/me', headers={'Authorization': 'Bearer '+response.json()['access_token']}).status_code == 200


def test_reset_revoca_incluso_si_hay_login_concurrente(client, db, monkeypatch):
    from sqlalchemy import update
    from sqlalchemy.orm import Session
    from auth import create_access_token
    from models import User
    from routers import admin_router

    admin, _ = crear_usuario(db, 'admin-race@test.com', admin=True)
    player, _ = crear_usuario(db, 'player-race@test.com')
    concurrent_token = []

    def password_after_concurrent_login():
        # El reset ya leyó al jugador; otra transacción inicia sesión antes del UPDATE.
        with Session(db.get_bind()) as other:
            version = other.execute(update(User).where(User.id == player.id)
                .values(session_version=User.session_version + 1)
                .returning(User.session_version)).scalar_one()
            other.commit()
        concurrent_token.append(create_access_token(player.id, session_version=version))
        return 'Temporal1234!'

    monkeypatch.setattr(admin_router, 'generate_temp_password', password_after_concurrent_login)
    response = client.post(f'/admin/players/{player.id}/reset-password', headers=cabeceras(admin))
    assert response.status_code == 200
    assert client.get('/auth/me', headers={'Authorization': 'Bearer '+concurrent_token[0]}).status_code == 409


def test_password_obligatorio_y_reautenticacion(client, db):
    player, _ = crear_usuario(db)
    player.must_change_password = True
    db.commit()
    headers = cabeceras(player)
    assert client.get('/progress/me', headers=headers).status_code == 403
    assert client.post('/auth/change-password', headers=headers, json={'new_password': 'Nueva1234!'}).status_code == 422
    assert client.post('/auth/change-password', headers=headers, json={'current_password': 'Mala1234!', 'new_password': 'Nueva1234!'}).status_code == 403
    response = client.post('/auth/change-password', headers=headers, json={'current_password': 'Test1234!', 'new_password': 'Nueva1234!'})
    assert response.status_code == 200
    assert client.get('/progress/me', headers=headers).status_code == 409
    assert client.get('/progress/me', headers={'Authorization': 'Bearer '+response.json()['access_token']}).status_code == 200


def test_contrasenas_difieren_despues_del_byte_72():
    a, b = 'A1' + 'x'*70 + 'first', 'A1' + 'x'*70 + 'second'
    hashed = hash_password(a)
    assert verify_password(a, hashed)
    assert not verify_password(b, hashed)


def test_dashboard_cookie_httponly_y_csrf(client, db):
    admin, _ = crear_usuario(db, 'admin@test.com', admin=True)
    response = _login(client, admin.email, admin=True)
    assert response.status_code == 200
    assert 'access_token' not in response.json()
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert 'samesite=strict' in response.headers['set-cookie'].lower()
    assert client.get('/auth/me').json()['id'] == admin.id
    assert client.post('/admin/workspaces', json={'name': 'Intento CSRF', 'color': '#059669'}).status_code == 403
    assert client.post('/auth/logout', headers={'Origin': 'http://testserver'}).status_code == 204
    assert ADMIN_COOKIE not in client.cookies
    assert client.get('/auth/me').status_code == 401


def test_no_revela_soluciones_y_no_acepta_puntajes_fabricados(client, db):
    player, slot = crear_usuario(db)
    reading = crear_lectura(db)
    headers = cabeceras(player)
    data = client.get('/progress/next-reading', params={'typology': 'Narrativo'}, headers=headers).json()
    assert len(data['questions']) == 6
    assert all('correct_answer' not in q and 'justification' not in q for q in data['questions'])
    payload = {'reading_id': reading.id, 'typology': 'Expositivo', 'attempt_id': data['attempt_id'], 'session_score': 2000000000,
               'correct_count': 999, 'is_perfect': False, 'tool_bonus': 999999}
    assert client.post('/progress/sessions', headers=headers, json=payload).status_code == 409
    for question in data['questions']:
        result = client.post('/progress/answers', headers=headers, json={'reading_id': reading.id,
                             'attempt_id': data['attempt_id'], 'question_id': question['id'], 'selected_answer': 'A'})
        assert result.status_code == 200
        assert result.json()['correct'] is True
    response = client.post('/progress/sessions', headers=headers, json=payload)
    assert response.status_code == 201
    assert response.json()['session_score'] == 240
    assert response.json()['correct_count'] == 6
    again = client.post('/progress/sessions', headers=headers, json=payload)
    assert again.status_code == 201 and again.json()['id'] == response.json()['id']
    assert db.query(PlayerSession).filter_by(user_id=player.id, slot_id=slot.id).count() == 1


def test_no_responde_preguntas_de_otro_intento(client, db):
    player, _ = crear_usuario(db)
    reading = crear_lectura(db)
    other = crear_lectura(db, 'Otra')
    headers = cabeceras(player)
    data = client.get(f'/readings/{reading.id}/full', headers=headers).json()
    assert client.post('/progress/answers', headers=headers, json={'reading_id': other.id,
                       'attempt_id': data['attempt_id'], 'question_id': data['questions'][0]['id'], 'selected_answer': 'A'}).status_code == 409
    assert client.post('/progress/achievements', headers=headers,
                       json={'achievement_id': 'half_millennium', 'achievement_name': 'Falso'}).status_code == 403


def test_exportaciones_no_guardan_formulas():
    output = io.StringIO()
    SafeWriter(output).writerow(['=1+1', 'Normal', 3])
    assert "'=1+1" in output.getvalue()
    wb = Workbook()
    wb.active['A1'] = '=1+1'
    binary = io.BytesIO()
    secure_workbook(wb).save(binary)
    binary.seek(0)
    assert load_workbook(binary).active['A1'].data_type == 's'


def test_imagenes_no_abren_plugins_ajenos():
    with pytest.raises(ValueError):
        resize_image_to_256(b'#define image_width 1\n#define image_height 1\nstatic char image_bits[] = { 0x00 };')
