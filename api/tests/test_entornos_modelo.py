"""Entornos de trabajo: la tabla workspaces y users.workspace_id (migración
011). La migración no crea entornos ni toca las cuentas que ya existen y se
puede aplicar las veces que haga falta; el correo pasa a ser único dentro de
cada entorno, y entre las cuentas sin entorno (administradores)."""
import threading

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import engine
from esquema import aplicar_migraciones, preparar_base
from helpers import crear_entorno, crear_usuario
from models import User


def _indices(db, tabla):
    return set(db.execute(text(
        "SELECT indexname FROM pg_indexes WHERE schemaname = current_schema() AND tablename = :t"
    ), {"t": tabla}).scalars())


def _restricciones(db, tabla):
    return set(db.execute(text(
        "SELECT conname FROM pg_constraint WHERE conrelid = CAST(:t AS regclass)"
    ), {"t": tabla}).scalars())


@pytest.fixture(params=["indice", "restriccion"])
def base_de_antes(request, db):
    """La base de antes de los entornos: sin workspaces ni users.workspace_id y
    con el correo único en toda la tabla, como índice (base hecha por la API)
    o como restricción (base hecha por initdb con 004_users_schema.sql)."""
    db.rollback()
    with engine.begin() as conn:
        conn.execute(text("DROP INDEX IF EXISTS ux_users_workspace_email"))
        conn.execute(text("DROP INDEX IF EXISTS ix_users_email_login"))
        conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS workspace_id"))
        conn.execute(text("DROP TABLE IF EXISTS workspaces CASCADE"))
        if request.param == "indice":
            conn.execute(text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))
        else:
            conn.execute(text("ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email)"))
    yield
    # El esquema de pruebas es compartido: la migración lo deja como el modelo.
    db.rollback()
    aplicar_migraciones(engine)


def test_migracion_no_crea_entornos_ni_toca_cuentas(db, base_de_antes):
    db.execute(text(
        "INSERT INTO users (email, hashed_password, display_name, is_admin, session_version) VALUES "
        "('alumno@test.com', 'x', 'Alumno', false, 1), ('admin@test.com', 'x', 'Admin', true, 1)"
    ))
    db.commit()

    aplicar_migraciones(engine)

    assert db.execute(text("SELECT count(*) FROM workspaces")).scalar() == 0
    assert db.execute(text("SELECT count(*) FROM users WHERE workspace_id IS NOT NULL")).scalar() == 0
    assert db.execute(text("SELECT count(*) FROM users")).scalar() == 2
    indices = _indices(db, "users")
    assert "ix_users_email" not in indices
    assert "users_email_key" not in _restricciones(db, "users")
    assert {"ux_users_workspace_email", "ix_users_email_login", "ix_users_workspace_id"} <= indices
    assert {"ux_workspaces_nombre", "ux_workspaces_un_activo"} <= _indices(db, "workspaces")


def test_migracion_dos_veces(db):
    aplicar_migraciones(engine)
    aplicar_migraciones(engine)


def test_preparar_la_base_en_paralelo(db, base_de_antes):
    # La API arranca varios procesos (2 en producción, 4 en local) y cada uno
    # prepara la base al importarse (create_all y migraciones): no pueden
    # pisarse creando la misma tabla. Pasó al añadir workspaces: un proceso se
    # cayó con «duplicate key … workspaces_id_seq».
    procesos = 4
    salida = threading.Barrier(procesos)
    errores = []

    def preparar():
        try:
            salida.wait()
            preparar_base(engine)
        except Exception as exc:  # noqa: BLE001
            errores.append(repr(exc))

    hilos = [threading.Thread(target=preparar) for _ in range(procesos)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join(timeout=60)
    assert errores == []
    assert "workspace_id" in {c for (c,) in db.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = 'users'"
    )).all()}


def test_correo_unico_por_entorno(db):
    a = crear_entorno(db, "A")
    b = crear_entorno(db, "B")
    crear_usuario(db, "x@test.com", entorno=a)
    crear_usuario(db, "x@test.com", entorno=b)
    with pytest.raises(IntegrityError):
        crear_usuario(db, "x@test.com", entorno=a)
    db.rollback()
    assert db.query(User).filter_by(email="x@test.com").count() == 2


def test_sin_entorno_el_correo_es_unico(db):
    crear_usuario(db, "admin@test.com", admin=True)
    with pytest.raises(IntegrityError):
        crear_usuario(db, "admin@test.com", admin=True)
    db.rollback()


def test_solo_un_entorno_activo(db):
    crear_entorno(db, "A", activo=True)
    crear_entorno(db, "B")
    with pytest.raises(IntegrityError):
        crear_entorno(db, "C", activo=True)
    db.rollback()


def test_nombre_unico_sin_mayusculas(db):
    crear_entorno(db, "Pruebas")
    with pytest.raises(IntegrityError):
        crear_entorno(db, "pruebas")
    db.rollback()


def test_borrar_un_entorno_borra_sus_cuentas(db):
    a = crear_entorno(db, "A")
    b = crear_entorno(db, "B")
    crear_usuario(db, "uno@test.com", entorno=a)
    crear_usuario(db, "dos@test.com", entorno=b)
    db.execute(text("DELETE FROM workspaces WHERE id = :id"), {"id": a.id})
    db.commit()
    assert [u.email for u in db.query(User).all()] == ["dos@test.com"]
