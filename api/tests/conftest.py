"""
Configuración común de los tests de la API.

Los tests corren contra una base APARTE, godot_readings_test, en el mismo
Postgres local. Nunca contra la de desarrollo: si TEST_DATABASE_URL no apunta a
una base cuyo nombre termine en _test, pytest ni arranca.
"""
import os

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

_URL_PRUEBAS = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://DB-virtual-world-reading-ai:GodotWorldAdmin@db:5432/godot_readings_test",
)
_NOMBRE_BASE = make_url(_URL_PRUEBAS).database or ""
if not _NOMBRE_BASE.endswith("_test"):
    raise pytest.UsageError(
        f"TEST_DATABASE_URL debe apuntar a una base *_test (apunta a '{_NOMBRE_BASE}')"
    )

# database.py crea el engine al importarse y main.py ejecuta create_all al
# importarse: DATABASE_URL tiene que apuntar a la base de pruebas ANTES.
os.environ["DATABASE_URL"] = _URL_PRUEBAS


def _crear_base_si_falta() -> None:
    url = make_url(_URL_PRUEBAS)
    servidor = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with servidor.connect() as conn:
        existe = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :nombre"),
            {"nombre": url.database},
        ).scalar()
        if not existe:
            conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    servidor.dispose()


_crear_base_si_falta()

from fastapi.testclient import TestClient  # noqa: E402

from database import Base, SessionLocal, engine  # noqa: E402
import main  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _esquema():
    """Esquema recién creado desde los modelos en cada ejecución de pytest."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(autouse=True)
def _vaciar_tablas():
    yield
    tablas = ", ".join(f'"{t.name}"' for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tablas} RESTART IDENTITY CASCADE"))


@pytest.fixture
def db():
    sesion = SessionLocal()
    try:
        yield sesion
    finally:
        sesion.close()


@pytest.fixture
def client():
    return TestClient(main.app)
