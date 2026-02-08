"""
Módulo de caché usando Redis (NoSQL) para mejorar el rendimiento de la API.

Este módulo implementa un sistema de caché distribuido usando Redis como base de datos
NoSQL, con operaciones asíncronas que utilizan hilos para no bloquear el event loop
de FastAPI.

CARACTERÍSTICAS PRINCIPALES:
- Base de datos NoSQL: Redis (almacenamiento clave-valor en memoria)
- Operaciones asíncronas: Uso de asyncio.to_thread() para ejecutar operaciones
  bloqueantes en hilos separados, evitando bloquear el event loop
- Invalidación en segundo plano: Las operaciones de invalidación se ejecutan de forma
  asíncrona (fire-and-forget) para no retrasar las respuestas HTTP
- Optimización: Uso de SCAN en lugar de KEYS para mejor rendimiento con muchas claves

IMPLEMENTACIÓN DE HILOS:
- get_from_cache_async(): Lee de Redis en un hilo separado usando asyncio.to_thread()
- set_to_cache_async(): Escribe en Redis en un hilo separado
- invalidate_cache_pattern_async(): Invalida caché usando SCAN en un hilo separado
- invalidate_cache_pattern_background(): Ejecuta invalidación en segundo plano sin esperar

VENTAJAS:
- No bloquea el event loop de FastAPI
- Mejor rendimiento con múltiples peticiones concurrentes
- Escalabilidad mejorada
- Tolerancia a fallos: Si Redis no está disponible, el sistema funciona sin caché
"""
import os
import json
import asyncio
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
        
        # Si es Upstash (tiene .upstash.io), cambiar redis:// por rediss:// para SSL
        if '.upstash.io' in redis_url and redis_url.startswith('redis://'):
            redis_url = redis_url.replace('redis://', 'rediss://', 1)
        
        try:
            _redis_client = redis.from_url(
                redis_url, 
                decode_responses=True
            )
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
    Invalida todas las claves que coincidan con un patrón (versión síncrona).
    
    NOTA: Esta función puede ser lenta con muchas claves. 
    Para mejor rendimiento, usa invalidate_cache_pattern_async() o 
    invalidate_cache_pattern_background().
    
    Args:
        pattern: Patrón de búsqueda (ej: "vehiculos:*")
    
    Returns:
        Número de claves eliminadas
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        # Usar SCAN en lugar de KEYS para mejor rendimiento (no bloquea Redis)
        keys = []
        cursor = 0
        while True:
            cursor, partial_keys = client.scan(cursor, match=pattern, count=100)
            keys.extend(partial_keys)
            if cursor == 0:
                break
        
        if keys:
            return client.delete(*keys)
    except redis.RedisError as e:
        print(f"⚠️  Error al invalidar caché ({pattern}): {e}")
    
    return 0


# ============================================================================
# FUNCIONES ASÍNCRONAS CON HILOS (Implementación de concurrencia)
# ============================================================================

async def get_from_cache_async(key: str) -> Optional[Any]:
    """
    Obtiene un valor de la caché de forma asíncrona usando hilos.
    
    Esta función ejecuta la operación bloqueante de Redis en un hilo separado
    usando asyncio.to_thread(), evitando bloquear el event loop de FastAPI.
    
    IMPLEMENTACIÓN DE HILOS:
    - asyncio.to_thread() ejecuta client.get() en un ThreadPoolExecutor
    - El event loop puede procesar otras peticiones mientras espera la respuesta de Redis
    - Mejora significativamente el rendimiento con múltiples peticiones concurrentes
    
    Args:
        key: Clave de caché
    
    Returns:
        Valor deserializado o None si no existe
    """
    client = get_redis_client()
    if not client:
        return None
    
    try:
        # Ejecutar operación bloqueante en un hilo separado
        # Esto permite que FastAPI procese otras peticiones mientras espera Redis
        value = await asyncio.to_thread(client.get, key)
        if value:
            return json.loads(value)
    except (json.JSONDecodeError, redis.RedisError) as e:
        print(f"⚠️  Error al leer de caché ({key}): {e}")
    
    return None


async def set_to_cache_async(key: str, value: Any, expire: int = 300) -> bool:
    """
    Almacena un valor en la caché de forma asíncrona usando hilos.
    
    Esta función ejecuta la operación bloqueante de Redis en un hilo separado,
    mejorando el rendimiento de la API al no bloquear el event loop.
    
    IMPLEMENTACIÓN DE HILOS:
    - Serializa los datos en el hilo principal (operación rápida)
    - Ejecuta client.setex() en un ThreadPoolExecutor usando asyncio.to_thread()
    - El event loop puede procesar otras peticiones durante la escritura
    
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
        # Serializar en el hilo principal (operación rápida)
        serialized = json.dumps(value, default=str)
        
        # Ejecutar escritura en Redis en un hilo separado
        await asyncio.to_thread(client.setex, key, expire, serialized)
        return True
    except (TypeError, redis.RedisError) as e:
        print(f"⚠️  Error al escribir en caché ({key}): {e}")
    
    return False


async def invalidate_cache_pattern_async(pattern: str) -> int:
    """
    Invalida todas las claves que coincidan con un patrón de forma asíncrona usando hilos.
    
    Esta función usa SCAN en lugar de KEYS para mejor rendimiento y ejecuta
    la operación en un hilo separado para no bloquear el event loop.
    
    IMPLEMENTACIÓN DE HILOS:
    - Ejecuta SCAN y DELETE en un ThreadPoolExecutor usando asyncio.to_thread()
    - SCAN es más eficiente que KEYS porque no bloquea Redis durante la búsqueda
    - Permite procesar otras peticiones mientras se invalida la caché
    
    Args:
        pattern: Patrón de búsqueda (ej: "vehiculos:*")
    
    Returns:
        Número de claves eliminadas
    """
    client = get_redis_client()
    if not client:
        return 0
    
    try:
        # Función auxiliar para ejecutar en hilo
        def _invalidate():
            keys = []
            cursor = 0
            # SCAN es más eficiente que KEYS (no bloquea Redis)
            while True:
                cursor, partial_keys = client.scan(cursor, match=pattern, count=100)
                keys.extend(partial_keys)
                if cursor == 0:
                    break
            
            if keys:
                return client.delete(*keys)
            return 0
        
        # Ejecutar en un hilo separado para no bloquear el event loop
        return await asyncio.to_thread(_invalidate)
    except redis.RedisError as e:
        print(f"⚠️  Error al invalidar caché ({pattern}): {e}")
    
    return 0


def invalidate_cache_pattern_background(pattern: str) -> None:
    """
    Invalida la caché en segundo plano (fire-and-forget) usando hilos.
    
    Esta función ejecuta la invalidación de forma asíncrona sin esperar a que termine,
    ideal para operaciones CRUD donde no queremos retrasar la respuesta al usuario.
    
    IMPLEMENTACIÓN DE HILOS:
    - Crea una tarea asíncrona (asyncio.create_task) que ejecuta la invalidación
    - La invalidación se ejecuta en un hilo separado usando asyncio.to_thread()
    - La respuesta HTTP se envía inmediatamente sin esperar la invalidación
    - Mejora la experiencia del usuario al no retrasar las respuestas
    
    Args:
        pattern: Patrón de búsqueda (ej: "vehiculos:*")
    """
    # Crear tarea en segundo plano sin esperar
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Si el loop está corriendo, crear tarea en segundo plano
            # Esta tarea ejecutará la invalidación en un hilo separado
            asyncio.create_task(invalidate_cache_pattern_async(pattern))
        else:
            # Si no hay loop corriendo, ejecutar directamente
            loop.run_until_complete(invalidate_cache_pattern_async(pattern))
    except RuntimeError:
        # Si no hay event loop disponible, ejecutar de forma síncrona
        # (fallback para compatibilidad)
        invalidate_cache_pattern(pattern)


def cached(prefix: str, expire: int = 300):
    """
    Decorador para cachear respuestas de funciones async usando hilos.
    
    Este decorador utiliza las funciones asíncronas que ejecutan operaciones
    de Redis en hilos separados, mejorando el rendimiento de la API.
    
    IMPLEMENTACIÓN DE HILOS:
    - Usa get_from_cache_async() que ejecuta Redis GET en un hilo
    - Usa set_to_cache_async() que ejecuta Redis SET en un hilo
    - No bloquea el event loop durante las operaciones de caché
    
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
            
            # Intentar obtener de caché (versión async con hilos)
            cached_result = await get_from_cache_async(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Ejecutar función y cachear resultado (versión async con hilos)
            result = await func(*args, **kwargs)
            await set_to_cache_async(cache_key, result, expire)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# FUNCIONES DE INVALIDACIÓN POR TIPO DE RECURSO
# Todas usan invalidación en segundo plano (fire-and-forget) con hilos
# ============================================================================

def invalidate_vehiculos_cache():
    """
    Invalida toda la caché relacionada con vehículos (en segundo plano con hilos).
    
    Esta función ejecuta la invalidación de forma asíncrona sin bloquear la respuesta HTTP.
    """
    invalidate_cache_pattern_background("vehiculos:*")


def invalidate_rutas_cache():
    """Invalida toda la caché relacionada con rutas (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("rutas:*")


def invalidate_incidencias_cache():
    """Invalida toda la caché relacionada con incidencias (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("incidencias:*")


def invalidate_pedidos_cache():
    """Invalida toda la caché relacionada con pedidos (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("pedidos:*")


def invalidate_mantenimientos_cache():
    """Invalida toda la caché relacionada con mantenimientos (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("mantenimientos:*")


def invalidate_inmuebles_cache():
    """Invalida toda la caché relacionada con inmuebles (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("inmuebles:*")


def invalidate_comunidades_cache():
    """Invalida toda la caché relacionada con comunidades (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("comunidades:*")


def invalidate_conductores_cache():
    """Invalida toda la caché relacionada con conductores (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("conductores:*")


def invalidate_proveedores_cache():
    """Invalida toda la caché relacionada con proveedores (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("proveedores:*")


def invalidate_propietarios_cache():
    """Invalida toda la caché relacionada con propietarios (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("propietarios:*")


def invalidate_usuarios_cache():
    """Invalida toda la caché relacionada con usuarios (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("usuarios:*")


def invalidate_documentos_cache():
    """Invalida toda la caché relacionada con documentos (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("documentos:*")


def invalidate_actuaciones_cache():
    """Invalida toda la caché relacionada con actuaciones (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("actuaciones:*")


def invalidate_mensajes_cache():
    """Invalida toda la caché relacionada con mensajes (en segundo plano con hilos)."""
    invalidate_cache_pattern_background("mensajes:*")


async def invalidate_all_cache_async():
    """
    Invalida toda la caché de forma asíncrona usando hilos (usar con precaución).
    
    Esta función ejecuta FLUSHDB en un hilo separado para no bloquear el event loop.
    """
    client = get_redis_client()
    if client:
        try:
            await asyncio.to_thread(client.flushdb)
        except redis.RedisError as e:
            print(f"⚠️  Error al limpiar caché: {e}")


def invalidate_all_cache():
    """Invalida toda la caché (versión síncrona, usar con precaución)."""
    client = get_redis_client()
    if client:
        try:
            client.flushdb()
        except redis.RedisError as e:
            print(f"⚠️  Error al limpiar caché: {e}")
