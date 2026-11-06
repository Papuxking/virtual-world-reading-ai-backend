"""Lectura de configuración efectiva y conteos, sin mensajes ni credenciales."""
import json
import os
from sqlalchemy import text
from database import engine, SessionLocal
from models import NpcInteraction
from conversation_crypto import decrypt_message, PREFIX

with engine.connect() as connection:
    role = dict(connection.execute(text('SELECT current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')).mappings().one())
    can_create = connection.execute(text("SELECT has_schema_privilege(current_user, 'vw', 'CREATE')")).scalar()
    counts = {name: connection.execute(text('SELECT count(*) FROM ' + name)).scalar()
              for name in ['users', 'readings', 'player_sessions', 'player_answers', 'npc_interactions']}
assert not role['rolsuper'] and not role['rolcreatedb'] and not role['rolcreaterole'] and not can_create
assert os.getuid() != 0
fields = 0
with SessionLocal() as db:
    for record in db.query(NpcInteraction).yield_per(200):
        for value in [record.user_message, record.assistant_reply]:
            if value:
                assert value.startswith(PREFIX)
                assert isinstance(decrypt_message(value, record), str)
                fields += 1
print(json.dumps({'uid': os.getuid(), 'database_role': role, 'schema_create': can_create,
                  'counts': counts, 'encrypted_fields_verified': fields, 'result': 'PASS'}, indent=2))
