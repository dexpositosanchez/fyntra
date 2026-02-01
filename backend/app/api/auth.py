from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
import secrets

from app.database import get_db
from app.models.usuario import Usuario
from app.models.conductor import Conductor
from app.models.propietario import Propietario
from app.models.proveedor import Proveedor
from app.schemas.usuario import (
    UsuarioLogin,
    UsuarioCreate,
    UsuarioResponse,
    Token,
    EliminarCuentaConfirmacion,
)
from app.api.dependencies import get_current_user
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.brute_force import (
    get_client_identifier,
    is_login_blocked,
    record_failed_attempt,
    clear_login_attempts,
)
from app.core.cache import (
    invalidate_usuarios_cache,
    invalidate_conductores_cache,
    invalidate_propietarios_cache,
    invalidate_proveedores_cache,
)

router = APIRouter(prefix="/auth", tags=["autenticación"])


def _blocked_message(seconds_remaining: int) -> str:
    """Mensaje de aviso de bloqueo temporal con tiempo restante."""
    minutes = (seconds_remaining + 59) // 60
    if minutes <= 0:
        return "Demasiados intentos de inicio de sesión. Acceso bloqueado temporalmente. Intente de nuevo en breve."
    return (
        f"Demasiados intentos de inicio de sesión. Acceso bloqueado temporalmente. "
        f"Intente de nuevo en {minutes} minuto(s)."
    )

@router.post("/login", response_model=Token)
async def login(credentials: UsuarioLogin, request: Request, db: Session = Depends(get_db)):
    """
    Endpoint de login optimizado para rendimiento.

    Incluye protección contra fuerza bruta mediante Redis:
    - Se cuentan los intentos fallidos por IP (o X-Forwarded-For).
    - Tras N intentos en una ventana de tiempo, se bloquea el acceso temporalmente.
    - Se informa al usuario del tiempo restante de bloqueo.
    """
    identifier = get_client_identifier(request)

    # Comprobar si ya está bloqueado
    blocked, seconds_remaining = is_login_blocked(identifier)
    if blocked:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=_blocked_message(seconds_remaining),
            headers={"Retry-After": str(seconds_remaining)},
        )

    # Consulta optimizada: el índice idx_usuarios_email acelera esta búsqueda
    user = db.query(Usuario).filter(
        Usuario.email == credentials.email
    ).first()

    if not user:
        # No revelar si el email existe o no por seguridad; contar como intento fallido
        _, now_blocked = record_failed_attempt(identifier)
        if now_blocked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_blocked_message(settings.LOGIN_BLOCK_SECONDS),
                headers={"Retry-After": str(settings.LOGIN_BLOCK_SECONDS)},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    # Verificación de contraseña (operación más costosa del login debido a bcrypt)
    if not verify_password(credentials.password, user.hash_password):
        _, now_blocked = record_failed_attempt(identifier)
        if now_blocked:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=_blocked_message(settings.LOGIN_BLOCK_SECONDS),
                headers={"Retry-After": str(settings.LOGIN_BLOCK_SECONDS)},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    # Login correcto: limpiar contador de intentos
    clear_login_attempts(identifier)

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
        )

    # Crear token (operación rápida, no requiere acceso a BD)
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "rol": user.rol},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": UsuarioResponse.model_validate(user)
    }

@router.post("/register", response_model=UsuarioResponse)
async def register(user_data: UsuarioCreate, db: Session = Depends(get_db)):
    # Verificar si el email ya existe
    existing_user = db.query(Usuario).filter(Usuario.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )
    
    # Crear nuevo usuario
    hashed_password = get_password_hash(user_data.password)
    new_user = Usuario(
        nombre=user_data.nombre,
        email=user_data.email,
        hash_password=hashed_password,
        rol=user_data.rol
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UsuarioResponse.model_validate(new_user)


# --- RGPD: Derecho de acceso y portabilidad (Art. 15 y 20) ---

@router.get("/me/datos")
async def exportar_mis_datos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Exporta los datos personales del usuario autenticado (Art. 15 y 20 RGPD).
    Devuelve JSON con perfil de usuario y, si aplica, perfil asociado (conductor/propietario/proveedor)
    y resumen de actividad.
    """
    exportado_en = datetime.utcnow()
    usuario_data = {
        "id": current_user.id,
        "nombre": current_user.nombre,
        "email": current_user.email,
        "rol": current_user.rol,
        "activo": current_user.activo,
        "creado_en": current_user.creado_en.isoformat() if current_user.creado_en else None,
        "actualizado_en": current_user.actualizado_en.isoformat() if current_user.actualizado_en else None,
    }
    perfil_asociado = None
    resumen_actividad = {}

    if current_user.rol == "conductor":
        conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
        if conductor:
            perfil_asociado = {
                "tipo": "conductor",
                "id": conductor.id,
                "nombre": conductor.nombre,
                "apellidos": conductor.apellidos,
                "dni": conductor.dni,
                "telefono": conductor.telefono,
                "email": conductor.email,
                "licencia": conductor.licencia,
                "fecha_caducidad_licencia": conductor.fecha_caducidad_licencia.isoformat() if conductor.fecha_caducidad_licencia else None,
                "activo": conductor.activo,
            }
            from app.models.ruta import Ruta
            num_rutas = db.query(Ruta).filter(Ruta.conductor_id == conductor.id).count()
            resumen_actividad["rutas_asignadas"] = num_rutas

    elif current_user.rol == "propietario":
        propietario = db.query(Propietario).filter(Propietario.usuario_id == current_user.id).first()
        if propietario:
            perfil_asociado = {
                "tipo": "propietario",
                "id": propietario.id,
                "nombre": propietario.nombre,
                "apellidos": propietario.apellidos,
                "email": propietario.email,
                "telefono": propietario.telefono,
                "dni": propietario.dni,
            }
            from app.models.incidencia import Incidencia
            num_incidencias = db.query(Incidencia).filter(Incidencia.creador_usuario_id == current_user.id).count()
            num_inmuebles = len(propietario.inmuebles) if propietario.inmuebles else 0
            resumen_actividad["incidencias_creadas"] = num_incidencias
            resumen_actividad["inmuebles_asociados"] = num_inmuebles

    elif current_user.rol == "proveedor":
        proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == current_user.id).first()
        if proveedor:
            perfil_asociado = {
                "tipo": "proveedor",
                "id": proveedor.id,
                "nombre": proveedor.nombre,
                "email": proveedor.email,
                "telefono": proveedor.telefono,
                "especialidad": proveedor.especialidad,
                "activo": proveedor.activo,
            }
            from app.models.incidencia import Incidencia
            num_incidencias = db.query(Incidencia).filter(Incidencia.proveedor_id == proveedor.id).count()
            resumen_actividad["incidencias_asignadas"] = num_incidencias

    return {
        "exportado_en": exportado_en.isoformat(),
        "usuario": usuario_data,
        "perfil_asociado": perfil_asociado,
        "resumen_actividad": resumen_actividad or None,
    }


# --- RGPD: Derecho de supresión (Art. 17) ---

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_mi_cuenta(
    body: Optional[EliminarCuentaConfirmacion] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Ejercicio del derecho de supresión (Art. 17 RGPD). El usuario autenticado puede solicitar
    la eliminación de su cuenta. Se anonimizan los datos personales; se mantienen referencias
    para integridad del historial (incidencias, rutas, etc.).
    Opcionalmente se puede enviar la contraseña para confirmar.
    """
    # No permitir eliminar el último super_admin activo
    if current_user.rol == "super_admin":
        otros = db.query(Usuario).filter(
            Usuario.rol == "super_admin",
            Usuario.id != current_user.id,
            Usuario.activo == True,
        ).count()
        if otros == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede eliminar la cuenta: es el último super administrador activo. Asigne otro super_admin antes.",
            )

    if body and body.password:
        if not verify_password(body.password, current_user.hash_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña incorrecta",
            )

    # Anonimizar usuario (datos personales borrados; referencias se mantienen)
    current_user.nombre = "Usuario eliminado"
    current_user.email = f"eliminado_{current_user.id}@cuenta-eliminada.local"
    current_user.hash_password = get_password_hash(secrets.token_urlsafe(32))
    current_user.activo = False

    # Anonimizar perfil asociado si existe (conductor, propietario o proveedor)
    conductor = db.query(Conductor).filter(Conductor.usuario_id == current_user.id).first()
    if conductor:
        conductor.nombre = "Eliminado"
        conductor.apellidos = None
        conductor.dni = None
        conductor.telefono = None
        conductor.email = f"eliminado_c{conductor.id}@cuenta-eliminada.local"
        conductor.activo = False

    propietario = db.query(Propietario).filter(Propietario.usuario_id == current_user.id).first()
    if propietario:
        propietario.nombre = "Eliminado"
        propietario.apellidos = None
        propietario.email = f"eliminado_p{propietario.id}@cuenta-eliminada.local"
        propietario.telefono = None
        propietario.dni = None

    proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == current_user.id).first()
    if proveedor:
        proveedor.nombre = "Eliminado"
        proveedor.email = f"eliminado_pr{proveedor.id}@cuenta-eliminada.local"
        proveedor.telefono = None
        proveedor.activo = False

    db.commit()
    invalidate_usuarios_cache()
    if conductor:
        invalidate_conductores_cache()
    if propietario:
        invalidate_propietarios_cache()
    if proveedor:
        invalidate_proveedores_cache()
    return None

