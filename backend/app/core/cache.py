"""
Módulo de caché usando Redis para mejorar el rendimiento de la API.

Proporciona funciones para almacenar y recuperar datos de caché,
con invalidación automática cuando se modifican los recursos.
"""
import os
import json
import hashlib
from typing import Optional, Any, Callable
from functools import wraps
import redis
from fastapi import Request

# Cliente Redis global (se inicializa al importar)
_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """Obtiene el cliente Redis, inicializándolo si es necesario."""
    global _redis_client
    
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        try:
            _redis_client = redis.from_url(redis_url, decode_responses=True)
            # Verificar conexión
            _redis_client.ping()
        except (redis.ConnectionError, redis.TimeoutError) as e:
            print(f"⚠️  Redis no disponible: {e}. El sistema funcionará sin caché.")
            _redis_client = None
    
    return _redis_client


def generate_cache_key(prefix: str, **kwargs) -> str:
    """
    Genera una clave de caché única basada en un prefijo y parámetros.
    
    Args:
        prefix: Prefijo para la clave (ej: "vehiculos:list")
        **kwargs: Parámetros que forman parte de la clave (skip, limit, estado, etc.)
    
    Returns:
        Clave de caché formateada
    """
    # Ordenar kwargs para consistencia
    sorted_params = sorted(kwargs.items())
    params_str = ":".join(f"{k}={v}" for k, v in sorted_params if v is not None)
    
    if params_str:
        return f"{prefix}:{params_str}"
    return prefix


def get_from_cache(key: str) -> Optional[Any]:
    """
    Obtiene un valor de la caché.
    
    Args:
        key: Clave de caché
    
    Returns:
        Valor deserializado o None si no existe
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except (json.JSONDecodeError, redis.RedisError) as e:
        print(f"⚠️  Error al leer de caché ({key}): {e}")
    
    return None


def set_to_cache(key: str, value: Any, expire: int = 300) -> bool:
    """
    Almacena un valor en la caché con expiración.
    
    Args:
        key: Clave de caché
        value: Valor a almacenar (debe ser serializable a JSON)
        expire: Tiempo de expiración en segundos (por defecto 5 minutos)
    
    Returns:
        True si se almacenó correctamente, False en caso contrario
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        serialized = json.dumps(value, default=str)  # default=str para manejar datetime
        client.setex(key, expire, serialized)
        return True
    except (TypeError, redis.RedisError) as e:
        print(f"⚠️  Error al escribir en caché ({key}): {e}")
    
    return False


def delete_from_cache(key: str) -> bool:
    """
    Elimina una clave de la caché.
    
    Args:
        key: Clave de caché
    
    Returns:
        True si se eliminó correctamente, False en caso contrario
    """
    client = get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except redis.RedisError as e:
        print(f"⚠️  Error al eliminar de caché ({key}): {e}")
    
    return False


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Invalida todas las claves que coincidan con un patrón.
    
    Args:
        pattern: Patrón de búsqueda (ej: "vehiculos:*")
    
    Returns:
        Número de claves eliminadas
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
    except redis.RedisError as e:
        print(f"⚠️  Error al invalidar caché ({pattern}): {e}")
    
    return 0


def cached(prefix: str, expire: int = 300):
    """
    Decorador para cachear respuestas de funciones async.
    
    Args:
        prefix: Prefijo para las claves de caché
        expire: Tiempo de expiración en segundos (por defecto 5 minutos)
    
    Uso:
        @cached("vehiculos:list", expire=300)
        async def listar_vehiculos(skip: int, limit: int, estado: Optional[str] = None):
            # ... código ...
            return resultado
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generar clave de caché basada en los parámetros
            # Excluir 'db' y 'current_user' de la clave ya que no afectan el resultado
            cache_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['db', 'current_user', 'request']}
            
            # Incluir args posicionales si hay
            if args:
                # Asumir que los primeros args son parámetros de la función
                # (skip, limit, etc.)
                for i, arg in enumerate(args):
                    if i < 3:  # Solo los primeros 3 args típicamente
                        cache_kwargs[f"arg_{i}"] = arg
            
            cache_key = generate_cache_key(prefix, **cache_kwargs)
            
            # Intentar obtener de caché
            cached_result = get_from_cache(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            set_to_cache(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator


# Funciones de invalidación por tipo de recurso
def invalidate_vehiculos_cache():
    """Invalida toda la caché relacionada con vehículos."""
    invalidate_cache_pattern("vehiculos:*")


def invalidate_rutas_cache():
    """Invalida toda la caché relacionada con rutas."""
    invalidate_cache_pattern("rutas:*")


def invalidate_incidencias_cache():
    """Invalida toda la caché relacionada con incidencias."""
    invalidate_cache_pattern("incidencias:*")


def invalidate_pedidos_cache():
    """Invalida toda la caché relacionada con pedidos."""
    invalidate_cache_pattern("pedidos:*")


def invalidate_mantenimientos_cache():
    """Invalida toda la caché relacionada con mantenimientos."""
    invalidate_cache_pattern("mantenimientos:*")


def invalidate_inmuebles_cache():
    """Invalida toda la caché relacionada con inmuebles."""
    invalidate_cache_pattern("inmuebles:*")


def invalidate_comunidades_cache():
    """Invalida toda la caché relacionada con comunidades."""
    invalidate_cache_pattern("comunidades:*")


def invalidate_conductores_cache():
    """Invalida toda la caché relacionada con conductores."""
    invalidate_cache_pattern("conductores:*")


def invalidate_proveedores_cache():
    """Invalida toda la caché relacionada con proveedores."""
    invalidate_cache_pattern("proveedores:*")


def invalidate_propietarios_cache():
    """Invalida toda la caché relacionada con propietarios."""
    invalidate_cache_pattern("propietarios:*")


def invalidate_usuarios_cache():
    """Invalida toda la caché relacionada con usuarios."""
    invalidate_cache_pattern("usuarios:*")


def invalidate_documentos_cache():
    """Invalida toda la caché relacionada con documentos."""
    invalidate_cache_pattern("documentos:*")


def invalidate_actuaciones_cache():
    """Invalida toda la caché relacionada con actuaciones."""
    invalidate_cache_pattern("actuaciones:*")


def invalidate_mensajes_cache():
    """Invalida toda la caché relacionada con mensajes."""
    invalidate_cache_pattern("mensajes:*")


def invalidate_all_cache():
    """Invalida toda la caché (usar con precaución)."""
    client = get_redis_client()
    if client:
        try:
            client.flushdb()
        except redis.RedisError as e:
            print(f"⚠️  Error al limpiar caché: {e}")
