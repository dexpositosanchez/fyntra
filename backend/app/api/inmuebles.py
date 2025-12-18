from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models.inmueble import Inmueble
from app.models.comunidad import Comunidad
from app.models.propietario import Propietario
from app.models.usuario import Usuario
from app.schemas.inmueble import InmuebleCreate, InmuebleUpdate, InmuebleResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/inmuebles", tags=["inmuebles"])

def get_propietario_by_usuario(db: Session, usuario_id: int) -> Optional[Propietario]:
    """Obtiene el propietario asociado al usuario"""
    return db.query(Propietario).filter(Propietario.usuario_id == usuario_id).first()

@router.get("/", response_model=List[InmuebleResponse])
async def listar_inmuebles(
    comunidad_id: Optional[int] = Query(None, description="Filtrar por comunidad"),
    tipo: Optional[str] = Query(None, description="Filtrar por tipo"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    )
    
    # Propietarios solo ven sus inmuebles
    if current_user.rol == "propietario":
        propietario = get_propietario_by_usuario(db, current_user.id)
        if propietario:
            inmueble_ids = [i.id for i in propietario.inmuebles]
            query = query.filter(Inmueble.id.in_(inmueble_ids))
        else:
            return []
    
    if comunidad_id:
        query = query.filter(Inmueble.comunidad_id == comunidad_id)
    if tipo:
        query = query.filter(Inmueble.tipo == tipo)
    
    inmuebles = query.offset(skip).limit(limit).all()
    return [InmuebleResponse.model_validate(inm) for inm in inmuebles]

@router.get("/{inmueble_id}", response_model=InmuebleResponse)
async def obtener_inmueble(
    inmueble_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    inmueble = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == inmueble_id).first()
    
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    # Propietarios solo pueden ver sus inmuebles
    if current_user.rol == "propietario":
        propietario = get_propietario_by_usuario(db, current_user.id)
        if not propietario or inmueble_id not in [i.id for i in propietario.inmuebles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a este inmueble"
            )
    
    return InmuebleResponse.model_validate(inmueble)

@router.post("/", response_model=InmuebleResponse, status_code=status.HTTP_201_CREATED)
async def crear_inmueble(
    inmueble_data: InmuebleCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear inmuebles"
        )
    
    # Verificar que la comunidad existe
    comunidad = db.query(Comunidad).filter(Comunidad.id == inmueble_data.comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    # Crear inmueble
    data = inmueble_data.model_dump(exclude={'propietario_ids'})
    nuevo_inmueble = Inmueble(**data)
    
    # Asociar propietarios si se proporcionan
    if inmueble_data.propietario_ids:
        propietarios = db.query(Propietario).filter(
            Propietario.id.in_(inmueble_data.propietario_ids)
        ).all()
        nuevo_inmueble.propietarios = propietarios
    
    db.add(nuevo_inmueble)
    db.commit()
    db.refresh(nuevo_inmueble)
    
    # Cargar relaciones
    db.refresh(nuevo_inmueble)
    return InmuebleResponse.model_validate(nuevo_inmueble)

@router.put("/{inmueble_id}", response_model=InmuebleResponse)
async def actualizar_inmueble(
    inmueble_id: int,
    inmueble_data: InmuebleUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar inmuebles"
        )
    
    inmueble = db.query(Inmueble).options(
        joinedload(Inmueble.comunidad),
        joinedload(Inmueble.propietarios)
    ).filter(Inmueble.id == inmueble_id).first()
    
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    update_data = inmueble_data.model_dump(exclude_unset=True, exclude={'propietario_ids'})
    for field, value in update_data.items():
        setattr(inmueble, field, value)
    
    # Actualizar propietarios si se proporcionan
    if inmueble_data.propietario_ids is not None:
        propietarios = db.query(Propietario).filter(
            Propietario.id.in_(inmueble_data.propietario_ids)
        ).all()
        inmueble.propietarios = propietarios
    
    db.commit()
    db.refresh(inmueble)
    return InmuebleResponse.model_validate(inmueble)

@router.delete("/{inmueble_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_inmueble(
    inmueble_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar inmuebles"
        )
    
    inmueble = db.query(Inmueble).filter(Inmueble.id == inmueble_id).first()
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    db.delete(inmueble)
    db.commit()
    return None

