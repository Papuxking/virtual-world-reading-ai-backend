"""Comprueba el respaldo cifrado con DPAPI, sin volcar datos ni restaurar la BD."""
import argparse
import base64
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def open_backup(directory: Path):
    if os.name != 'nt':
        raise RuntimeError('Se necesita el usuario Windows que creó el respaldo DPAPI')
    class Blob(ctypes.Structure):
        _fields_ = [('length', wintypes.DWORD), ('data', ctypes.POINTER(ctypes.c_ubyte))]
    wrapped_key = (directory / 'backup-key.dpapi').read_bytes()
    buffer = ctypes.create_string_buffer(wrapped_key)
    original = Blob(len(wrapped_key), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_ubyte)))
    clear = Blob()
    unprotect = ctypes.windll.crypt32.CryptUnprotectData
    unprotect.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.POINTER(Blob), ctypes.c_void_p,
                         ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    unprotect.restype = wintypes.BOOL
    if not unprotect(ctypes.byref(original), None, None, None, None, 1, ctypes.byref(clear)):
        raise ctypes.WinError()
    try:
        key = ctypes.string_at(clear.data, clear.length)
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(clear.data)
    encrypted = (directory / 'backup.aesgcm').read_bytes()
    return json.loads(AESGCM(key).decrypt(encrypted[:12], encrypted[12:], b'vw-security-backup-v1'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    arguments = parser.parse_args()
    payload = open_backup(arguments.directory)
    dump = base64.b64decode(payload['database_dump_b64'], validate=True)
    assert dump.startswith(b'PGDMP')
    assert all(isinstance(payload[name], dict) for name in [
        'previous_api_configuration', 'previous_backend_configuration', 'new_security_configuration'])
    print(json.dumps({'result': 'PASS', 'aead_verified': True, 'pg_dump_format': 'custom',
                      'dump_bytes': len(dump), 'configurations_present': 3}))
