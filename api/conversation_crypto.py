"""Cifrado de la copia del dashboard. Es cifrado en reposo, no E2EE."""
import base64
import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

PREFIX = 'enc:v1:'


def _aad(record):
    # reading_id puede pasar a NULL al borrar una lectura; usar contexto inmutable.
    return json.dumps(['npc', 1, record.id, record.user_id, record.slot_id, record.npc_type],
                      separators=(',', ':')).encode()


def _key():
    try:
        key = base64.b64decode(os.environ['VW_DATA_ENCRYPTION_KEY'], validate=True)
        if len(key) != 32:
            raise ValueError()
        return key
    except (KeyError, ValueError):
        raise RuntimeError('Configura VW_DATA_ENCRYPTION_KEY con una clave aleatoria de 32 bytes en base64')


def encrypt_message(value, record):
    if value is None or value == '':
        return value
    nonce = os.urandom(12)
    return PREFIX + base64.b64encode(nonce + AESGCM(_key()).encrypt(nonce, value.encode(), _aad(record))).decode()


def decrypt_message(value, record):
    if value is None or not value.startswith(PREFIX):
        # Compatibilidad de lectura durante la migración de datos históricos.
        return value
    try:
        raw = base64.b64decode(value[len(PREFIX):], validate=True)
        return AESGCM(_key()).decrypt(raw[:12], raw[12:], _aad(record)).decode()
    except (ValueError, InvalidTag, UnicodeDecodeError):
        raise RuntimeError('No se pudo verificar el contenido de una conversación')
