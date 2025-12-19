from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioResponse, CambiarPassword
from app.api.dependencies import get_current_user
from app.core.security import get_password_hash

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

# Roles válidos según módulo
ROLES_VALIDOS = {
    "fincas": ["admin_fincas", "propietario", "proveedor"],
    "transportes": ["admin_transportes", "conductor"],
    "sistema": ["super_admin"]
}

def verificar_super_admin(usuario: Usuario):
    """Verifica que el usuario sea super_admin"""
    if usuario.rol != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los super administradores pueden acceder a esta funcionalidad"
        )

@router.get("/", response_model=List[UsuarioResponse])
async def listar_usuarios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los usuarios (solo super_admin)"""
    verificar_super_admin(current_user)
    
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return usuarios

@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene un usuario por ID (solo super_admin)"""
    verificar_super_admin(current_user)
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.post("/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def crear_usuario(
    usuario_data: UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo usuario (solo super_admin)"""
    verificar_super_admin(current_user)
    
    # Verificar que el email no exista
    existente = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
    
    # Validar rol
    roles_todos = []
    for roles_modulo in ROLES_VALIDOS.values():
        roles_todos.extend(roles_modulo)
    
    if usuario_data.rol not in roles_todos:
        raise HTTPException(
            status_code=400,
            detail=f"Rol inválido. Roles válidos: {', '.join(roles_todos)}"
        )
    
    nuevo_usuario = Usuario(
        nombre=usuario_data.nombre,
        email=usuario_data.email,
        hash_password=get_password_hash(usuario_data.password),
        rol=usuario_data.rol,
        activo=True
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def actualizar_usuario(
    usuario_id: int,
    usuario_data: UsuarioUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Actualiza un usuario (solo super_admin)"""
    verificar_super_admin(current_user)
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir modificar el último super_admin activo
    if usuario.rol == "super_admin" and not usuario_data.activo and usuario.activo:
        otros_super_admins = db.query(Usuario).filter(
            Usuario.rol == "super_admin",
            Usuario.id != usuario_id,
            Usuario.activo == True
        ).count()
        if otros_super_admins == 0:
            raise HTTPException(
                status_code=400,
                detail="No se puede desactivar el último super administrador activo"
            )
    
    # Verificar email único si se cambia
    if usuario_data.email and usuario_data.email != usuario.email:
        existente = db.query(Usuario).filter(Usuario.email == usuario_data.email).first()
        if existente:
            raise HTTPException(status_code=400, detail="Ya existe un usuario con ese email")
    
    # Validar rol si se cambia
    if usuario_data.rol:
        roles_todos = []
        for roles_modulo in ROLES_VALIDOS.values():
            roles_todos.extend(roles_modulo)
        
        if usuario_data.rol not in roles_todos:
            raise HTTPException(
                status_code=400,
                detail=f"Rol inválido. Roles válidos: {', '.join(roles_todos)}"
            )
    
    update_data = usuario_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(usuario, field, value)
    
    db.commit()
    db.refresh(usuario)
    return usuario

@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un usuario (solo super_admin)"""
    verificar_super_admin(current_user)
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # No permitir eliminar el último super_admin activo
    if usuario.rol == "super_admin" and usuario.activo:
        otros_super_admins = db.query(Usuario).filter(
            Usuario.rol == "super_admin",
            Usuario.id != usuario_id,
            Usuario.activo == True
        ).count()
        if otros_super_admins == 0:
            raise HTTPException(
                status_code=400,
                detail="No se puede eliminar el último super administrador activo"
            )
    
    # No permitir auto-eliminarse
    if usuario_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    
    db.delete(usuario)
    db.commit()
    return None

@router.put("/{usuario_id}/password", status_code=status.HTTP_204_NO_CONTENT)
async def cambiar_password_usuario(
    usuario_id: int,
    password_data: CambiarPassword,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Cambia la contraseña de un usuario (solo super_admin)"""
    verificar_super_admin(current_user)
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    if len(password_data.password) < 6:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 6 caracteres")
    
    usuario.hash_password = get_password_hash(password_data.password)
    db.commit()
    return None

