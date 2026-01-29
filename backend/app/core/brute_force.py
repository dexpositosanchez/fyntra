"""
Protección contra ataques de fuerza bruta en el login mediante Redis.

- Cuenta intentos fallidos por identificador (IP o X-Forwarded-For).
- Tras N intentos en una ventana de tiempo, bloquea temporalmente.
- Devuelve tiempo restante de bloqueo para informar al usuario.
"""
from typing import Tuple

from fastapi import Request

from app.core.cache import get_redis_client
from app.core.config import settings


def _key_attempts(identifier: str) -> str:
    return f"login_attempts:{identifier}"


def _key_blocked(identifier: str) -> str:
    return f"login_blocked:{identifier}"


def get_client_identifier(request: Request) -> str:
    """
    Obtiene el identificador del cliente (IP).
    Usa X-Forwarded-For si está detrás de proxy (ej. Nginx), sino client.host.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Primera IP de la lista es la del cliente original
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def is_login_blocked(identifier: str) -> Tuple[bool, int]:
    """
    Comprueba si el identificador está bloqueado por fuerza bruta.

    Returns:
        (blocked, seconds_remaining): True si bloqueado y segundos que quedan de bloqueo.
    """
    client = get_redis_client()
    if not client:
        return False, 0

    try:
        key = _key_blocked(identifier)
        if not client.exists(key):
            return False, 0
        ttl = client.ttl(key)
        return True, max(0, ttl)
    except Exception:
        return False, 0


def record_failed_attempt(identifier: str) -> Tuple[int, bool]:
    """
    Registra un intento fallido de login. Incrementa el contador en Redis.

    Returns:
        (current_attempts, now_blocked): intentos en esta ventana y si acaba de activarse el bloqueo.
    """
    client = get_redis_client()
    if not client:
        return 1, False

    key_attempts = _key_attempts(identifier)
    key_blocked = _key_blocked(identifier)

    try:
        pipe = client.pipeline()
        pipe.incr(key_attempts)
        pipe.get(key_attempts)
        results = pipe.execute()
        count = int(results[1] or 0)

        # Fijar TTL de la ventana solo en el primer intento
        if count == 1:
            client.expire(key_attempts, settings.LOGIN_ATTEMPT_WINDOW_SECONDS)

        now_blocked = False
        if count >= settings.LOGIN_MAX_ATTEMPTS:
            client.setex(key_blocked, settings.LOGIN_BLOCK_SECONDS, "1")
            client.delete(key_attempts)
            now_blocked = True

        return count, now_blocked
    except Exception:
        return 1, False


def clear_login_attempts(identifier: str) -> None:
    """Borra contador de intentos al hacer login correcto (opcional, buena práctica)."""
    client = get_redis_client()
    if not client:
        return
    try:
        client.delete(_key_attempts(identifier))
    except Exception:
        pass
