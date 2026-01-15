from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioLogin, UsuarioCreate, UsuarioResponse, Token
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["autenticación"])

@router.post("/login", response_model=Token)
async def login(credentials: UsuarioLogin, db: Session = Depends(get_db)):
    """
    Endpoint de login optimizado para rendimiento.
    
    Optimizaciones implementadas:
    1. Índice en usuarios.email (idx_usuarios_email) acelera la búsqueda
    2. Verificación de existencia antes de operación costosa (bcrypt)
    3. Creación de token sin acceso adicional a BD
    
    Nota: La verificación de contraseña con bcrypt es intencionalmente lenta
    por seguridad (protección contra fuerza bruta). Esto es normal y deseable.
    """
    # Consulta optimizada: el índice idx_usuarios_email acelera esta búsqueda
    user = db.query(Usuario).filter(
        Usuario.email == credentials.email
    ).first()
    
    if not user:
        # No revelar si el email existe o no por seguridad
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    
    # Verificar contraseña (operación más costosa del login debido a bcrypt)
    # bcrypt es intencionalmente lento por seguridad (protección contra fuerza bruta)
    if not verify_password(credentials.password, user.hash_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    
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

