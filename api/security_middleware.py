"""Límites de entrada y trazabilidad sin guardar tokens, consultas ni cuerpos."""
import logging
import os
import time
from collections import OrderedDict
from starlette.responses import JSONResponse

logger = logging.getLogger('uvicorn.error')


class SecurityMiddleware:
    def __init__(self, app):
        self.app = app
        self.buckets = OrderedDict()

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        headers = dict(scope.get('headers', []))
        path, method = scope['path'], scope['method']
        client = scope.get('client') or ('unknown', 0)
        if path in {'/auth/login', '/auth/admin/login', '/auth/register', '/auth/change-password'} and method == 'POST' and os.getenv('APP_ENV') != 'test':
            now = time.monotonic()
            key = (client[0], path)
            start, count = self.buckets.pop(key, (now, 0))
            if now - start >= 60:
                start, count = now, 0
            self.buckets[key] = (start, count + 1)
            while len(self.buckets) > 10000:
                self.buckets.popitem(last=False)
            if count >= 60:
                return await JSONResponse({'detail': 'Demasiados intentos. Inténtalo en un minuto.'}, 429, headers={'Retry-After': '60'})(scope, receive, send)

        maximum = 11 * 1024 * 1024 if headers.get(b'content-type', b'').startswith(b'multipart/form-data') else 1024 * 1024
        body, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            chunk = message.get('body', b'')
            size += len(chunk)
            if size > maximum:
                return await JSONResponse({'detail': 'Solicitud demasiado grande'}, 413)(scope, receive, send)
            body.append(chunk)
            if not message.get('more_body', False):
                break
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {'type': 'http.request', 'body': b''.join(body), 'more_body': False}
            return await receive()

        async def secure_send(message):
            if message['type'] == 'http.response.start':
                message['headers'] = list(message.get('headers', [])) + [
                    (b'x-content-type-options', b'nosniff'),
                    (b'referrer-policy', b'no-referrer'),
                ]
                if path.startswith(('/auth/', '/admin/', '/progress/', '/evaluation/')):
                    message['headers'].append((b'cache-control', b'no-store'))
                if method not in {'GET', 'HEAD', 'OPTIONS'}:
                    logger.info('security.request method=%s path=%r actor=%s status=%s', method, path,
                                scope.get('state', {}).get('security_user_id', 'anonymous'), message['status'])
            await send(message)

        await self.app(scope, replay, secure_send)
