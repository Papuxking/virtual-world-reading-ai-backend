"""Respaldo cifrado, claves locales y rol VW limitado. No contacta servidores remotos.

Solo trabaja con los contenedores locales nombrados abajo. No imprime secretos.
El respaldo se cifra con AES-GCM y su clave se protege con DPAPI del usuario Windows.
"""
import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
from datetime import datetime, timezone
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[2]


def command(args, data=None):
    result = subprocess.run(args, input=data, capture_output=True)
    if result.returncode:
        raise RuntimeError('Falló la operación local: ' + ' '.join(args[:4]) + '; no se muestran datos de configuración')
    return result.stdout


def container_env(name):
    entries = json.loads(command(['docker', 'inspect', name, '--format', '{{json .Config.Env}}']))
    return dict(item.split('=', 1) for item in entries if '=' in item)


def read_env(path):
    if not path.exists():
        return {}
    return dict(line.split('=', 1) for line in path.read_text(encoding='utf-8-sig').splitlines()
                if line and not line.lstrip().startswith('#') and '=' in line)


def write_env(path, values):
    path.write_text(''.join(f'{key}={value}\n' for key, value in values.items()), encoding='utf-8')


def protect_key(key):
    if os.name != 'nt':
        raise RuntimeError('Este configurador usa DPAPI y solo se ejecuta en Windows')
    class Blob(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    buffer = ctypes.create_string_buffer(key)
    original = Blob(len(key), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    protected = Blob()
    protect = ctypes.windll.crypt32.CryptProtectData
    protect.argtypes = [ctypes.POINTER(Blob), wintypes.LPCWSTR, ctypes.POINTER(Blob), ctypes.c_void_p,
                        ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    protect.restype = wintypes.BOOL
    if not protect(ctypes.byref(original), 'VW security backup', None, None, None, 1, ctypes.byref(protected)):
        raise ctypes.WinError()
    result = ctypes.string_at(protected.data, protected.length)
    ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    ctypes.windll.kernel32.LocalFree(protected.data)
    return result


BOOTSTRAP = r'''
import json, os, sys
import psycopg2
from psycopg2 import sql
config = json.load(sys.stdin)
os.environ['DATABASE_URL'] = config['old_url']
os.environ['VW_DATA_ENCRYPTION_KEY'] = config['data_key']
from database import engine, SessionLocal
from esquema import preparar_base
preparar_base(engine)
from models import NpcInteraction
from conversation_crypto import encrypt_message, PREFIX
tables = ['users','readings','player_sessions','player_answers','npc_interactions']
def counts(connection):
    with connection.cursor() as cursor:
        result = {}
        for table in tables:
            cursor.execute(sql.SQL('SELECT count(*) FROM vw.{}').format(sql.Identifier(table)))
            result[table] = cursor.fetchone()[0]
        return result
connection = psycopg2.connect(config['old_url'])
before = counts(connection)
with SessionLocal() as db:
    for record in db.query(NpcInteraction).yield_per(200):
        for field in ['user_message', 'assistant_reply']:
            value = getattr(record, field)
            if value and not value.startswith(PREFIX):
                setattr(record, field, encrypt_message(value, record))
    db.commit()
with connection.cursor() as cursor:
    cursor.execute('SELECT 1 FROM pg_roles WHERE rolname=%s', ('vw_runtime',))
    if cursor.fetchone() is None:
        cursor.execute('CREATE ROLE vw_runtime LOGIN')
    cursor.execute('ALTER ROLE vw_runtime WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD %s', (config['app_password'],))
    cursor.execute('GRANT USAGE ON SCHEMA vw TO vw_runtime')
    cursor.execute('REVOKE CREATE ON SCHEMA vw FROM PUBLIC')
    cursor.execute('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA vw TO vw_runtime')
    cursor.execute('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA vw TO vw_runtime')
    cursor.execute(sql.SQL('ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA vw GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO vw_runtime').format(sql.Identifier(connection.info.user)))
    cursor.execute(sql.SQL('ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA vw GRANT USAGE, SELECT ON SEQUENCES TO vw_runtime').format(sql.Identifier(connection.info.user)))
    cursor.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO vw_runtime').format(sql.Identifier(connection.info.dbname)))
    cursor.execute(sql.SQL('ALTER ROLE {} PASSWORD %s').format(sql.Identifier(connection.info.user)), (config['super_password'],))
connection.commit()
after = counts(connection)
assert before == after, 'Cambió el número de registros'
connection.close()
standalone = psycopg2.connect(config['standalone_url'])
with standalone.cursor() as cursor:
    cursor.execute(sql.SQL('ALTER ROLE {} PASSWORD %s').format(sql.Identifier(standalone.info.user)), (config['local_db_password'],))
standalone.commit()
standalone.close()
print(json.dumps({'before': before, 'after': after, 'records_preserved': before == after}))
'''


def main():
    api = container_env('docker-api-1')
    backend = container_env('lecturaia-backend-1')
    standalone = container_env('docker-db-1')
    config_path = ROOT / 'Docker/.env'
    values = read_env(config_path)
    old_url = make_url(api['DATABASE_URL'])
    if old_url.host not in {'lecturaia-db-1', 'db'} or old_url.database != 'lecturaia':
        raise RuntimeError('La conexión local no coincide con la topología revisada')
    configured = values.get('VW_SECURITY_CONFIG_VERSION') == '1'
    if configured:
        old_url = make_url(values['MIGRATION_DATABASE_URL'])
    app_password = make_url(values['DATABASE_URL']).password if configured else secrets.token_urlsafe(32)
    super_password = make_url(values['MIGRATION_DATABASE_URL']).password if configured else secrets.token_urlsafe(32)
    local_password = values.get('LOCAL_DB_PASSWORD') if configured else secrets.token_urlsafe(32)
    values.update({
        'DATABASE_URL': old_url.set(username='vw_runtime', password=app_password).render_as_string(hide_password=False),
        'MIGRATION_DATABASE_URL': old_url.set(password=super_password).render_as_string(hide_password=False),
        'LOCAL_DB_PASSWORD': local_password,
        'JWT_SECRET_KEY': values['JWT_SECRET_KEY'] if configured else secrets.token_hex(32),
        'VW_DATA_ENCRYPTION_KEY': values['VW_DATA_ENCRYPTION_KEY'] if configured else base64.b64encode(secrets.token_bytes(32)).decode(),
        'PUBLIC_ORIGIN': 'http://localhost:5173',
        'SYNC_SECRET_KEY': '',
        'LECTURAIA_API_URL': 'http://lecturaia-backend-1:8000',
        'VW_SECURITY_CONFIG_VERSION': '1',
    })
    backup_dir = ROOT / 'backups' / ('security-local-' + datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S'))
    backup_dir.mkdir(parents=True)
    backup_key = secrets.token_bytes(32)
    protected = protect_key(backup_key)
    dump = command(['docker', 'exec', 'lecturaia-db-1', 'pg_dump', '-U', 'postgres', '-d', 'lecturaia', '-Fc'])
    backup_payload = json.dumps({'database_dump_b64': base64.b64encode(dump).decode(),
                                 'previous_api_configuration': api, 'previous_backend_configuration': backend,
                                 'new_security_configuration': values}).encode()
    nonce = secrets.token_bytes(12)
    (backup_dir / 'backup.aesgcm').write_bytes(nonce + AESGCM(backup_key).encrypt(nonce, backup_payload, b'vw-security-backup-v1'))
    (backup_dir / 'backup-key.dpapi').write_bytes(protected)
    write_env(config_path, values)
    companion_root = ROOT / 'Steeven/LecturaIA'
    companion_values = read_env(companion_root / '.env')
    backend_url = make_url(backend['DATABASE_URL']).set(password=super_password).render_as_string(hide_password=False)
    companion_values.update({'POSTGRES_PASSWORD': super_password, 'DATABASE_URL': backend_url})
    write_env(companion_root / '.env', companion_values)
    backend_values = read_env(companion_root / 'backend/.env')
    backend_values.update({'POSTGRES_PASSWORD': super_password, 'DATABASE_URL': backend_url,
                           'VW_AUTH_API_URL': 'http://docker-api-1:8000'})
    write_env(companion_root / 'backend/.env', backend_values)
    compose = companion_root / 'docker-compose.yml'
    source = compose.read_text(encoding='utf-8')
    source = re.sub(r'(POSTGRES_PASSWORD:)\s*[^\r\n]+', r'\1 ${POSTGRES_PASSWORD:?Configura .env}', source)
    source = re.sub(r'(DATABASE_URL:)\s*postgresql[^\r\n]+', r'\1 ${DATABASE_URL:?Configura .env}', source)
    for port in ('5434:5432', '8000:8000', '3000:3000'):
        source = source.replace('"'+port+'"', '"127.0.0.1:'+port+'"')
    compose.write_text(source, encoding='utf-8')
    standalone_url = make_url('postgresql://localhost').set(username=standalone['POSTGRES_USER'],
        password=standalone['POSTGRES_PASSWORD'], host='docker-db-1', database=standalone['POSTGRES_DB'])
    payload = {'old_url': old_url.render_as_string(hide_password=False), 'data_key': values['VW_DATA_ENCRYPTION_KEY'],
               'app_password': app_password, 'super_password': super_password,
               'local_db_password': local_password, 'standalone_url': standalone_url.render_as_string(hide_password=False)}
    result = command(['docker', 'exec', '-i', 'docker-api-1', 'python', '-c', BOOTSTRAP], json.dumps(payload).encode())
    (backup_dir / 'verification.json').write_bytes(result)
    print('Respaldo cifrado creado:', backup_dir.relative_to(ROOT))
    print('Claves actualizadas, conversaciones cifradas, rol VW limitado y conteos conservados. Recrear los servicios locales para aplicar las variables nuevas.')


if __name__ == '__main__':
    main()
