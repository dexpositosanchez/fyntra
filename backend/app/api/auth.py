from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioLogin, UsuarioCreate, UsuarioResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.core.brute_force import (
    get_client_identifier,
    is_login_blocked,
    record_failed_attempt,
    clear_login_attempts,
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

