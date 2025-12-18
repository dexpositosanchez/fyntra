from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.mensaje import Mensaje
from app.models.incidencia import Incidencia
from app.models.usuario import Usuario
from app.models.proveedor import Proveedor
from app.models.propietario import Propietario
from app.schemas.mensaje import MensajeCreate, MensajeResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/mensajes", tags=["mensajes"])

def verificar_acceso_incidencia(db: Session, incidencia_id: int, usuario: Usuario) -> Incidencia:
    """Verifica que el usuario tenga acceso a la incidencia"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    
    # Admins tienen acceso a todo
    if usuario.rol in ["super_admin", "admin_fincas"]:
        return incidencia
    
    # Propietario: solo si es dueño del inmueble
    if usuario.rol == "propietario":
        propietario = db.query(Propietario).filter(Propietario.usuario_id == usuario.id).first()
        if propietario:
            inmueble_ids = [i.id for i in propietario.inmuebles]
            if incidencia.inmueble_id in inmueble_ids:
                return incidencia
    
    # Proveedor: solo si está asignado
    if usuario.rol == "proveedor":
        proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == usuario.id).first()
        if proveedor and incidencia.proveedor_id == proveedor.id:
            return incidencia
    
    raise HTTPException(status_code=403, detail="No tiene acceso a esta incidencia")

def mensaje_to_response(mensaje: Mensaje, db: Session) -> dict:
    """Convierte un mensaje a response con datos del usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == mensaje.usuario_id).first()
    return {
        "id": mensaje.id,
        "incidencia_id": mensaje.incidencia_id,
        "usuario_id": mensaje.usuario_id,
        "usuario_nombre": usuario.nombre if usuario else "Usuario eliminado",
        "usuario_rol": usuario.rol if usuario else "desconocido",
        "contenido": mensaje.contenido,
        "creado_en": mensaje.creado_en
    }

@router.get("/incidencia/{incidencia_id}", response_model=List[MensajeResponse])
async def listar_mensajes(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los mensajes de una incidencia"""
    verificar_acceso_incidencia(db, incidencia_id, current_user)
    
    mensajes = db.query(Mensaje).filter(
        Mensaje.incidencia_id == incidencia_id
    ).order_by(Mensaje.creado_en.asc()).all()
    
    return [mensaje_to_response(m, db) for m in mensajes]

@router.post("/incidencia/{incidencia_id}", response_model=MensajeResponse, status_code=status.HTTP_201_CREATED)
async def crear_mensaje(
    incidencia_id: int,
    mensaje_data: MensajeCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un nuevo mensaje en una incidencia"""
    verificar_acceso_incidencia(db, incidencia_id, current_user)
    
    nuevo_mensaje = Mensaje(
        incidencia_id=incidencia_id,
        usuario_id=current_user.id,
        contenido=mensaje_data.contenido
    )
    db.add(nuevo_mensaje)
    db.commit()
    db.refresh(nuevo_mensaje)
    
    return mensaje_to_response(nuevo_mensaje, db)

@router.delete("/{mensaje_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_mensaje(
    mensaje_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un mensaje (solo el autor y si es el último mensaje)"""
    mensaje = db.query(Mensaje).filter(Mensaje.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    # Solo el autor puede eliminar
    if mensaje.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes eliminar tus propios mensajes")
    
    # Verificar que es el último mensaje de la incidencia
    ultimo_mensaje = db.query(Mensaje).filter(
        Mensaje.incidencia_id == mensaje.incidencia_id
    ).order_by(Mensaje.creado_en.desc()).first()
    
    if ultimo_mensaje.id != mensaje.id:
        raise HTTPException(status_code=403, detail="Solo puedes eliminar tu último mensaje")
    
    db.delete(mensaje)
    db.commit()
    return None

