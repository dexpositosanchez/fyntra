from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.comunidad import Comunidad
from app.models.usuario import Usuario
from app.schemas.comunidad import ComunidadCreate, ComunidadUpdate, ComunidadResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/comunidades", tags=["comunidades"])

@router.get("/", response_model=List[ComunidadResponse])
async def listar_comunidades(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    comunidades = db.query(Comunidad).offset(skip).limit(limit).all()
    return [ComunidadResponse.model_validate(com) for com in comunidades]

@router.get("/{comunidad_id}", response_model=ComunidadResponse)
async def obtener_comunidad(
    comunidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    comunidad = db.query(Comunidad).filter(Comunidad.id == comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    return ComunidadResponse.model_validate(comunidad)

@router.post("/", response_model=ComunidadResponse, status_code=status.HTTP_201_CREATED)
async def crear_comunidad(
    comunidad_data: ComunidadCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear comunidades"
        )
    
    nueva_comunidad = Comunidad(**comunidad_data.model_dump())
    db.add(nueva_comunidad)
    db.commit()
    db.refresh(nueva_comunidad)
    return ComunidadResponse.model_validate(nueva_comunidad)

@router.put("/{comunidad_id}", response_model=ComunidadResponse)
async def actualizar_comunidad(
    comunidad_id: int,
    comunidad_data: ComunidadUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar comunidades"
        )
    
    comunidad = db.query(Comunidad).filter(Comunidad.id == comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    update_data = comunidad_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comunidad, field, value)
    
    db.commit()
    db.refresh(comunidad)
    return ComunidadResponse.model_validate(comunidad)

@router.delete("/{comunidad_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_comunidad(
    comunidad_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar comunidades"
        )
    
    comunidad = db.query(Comunidad).filter(Comunidad.id == comunidad_id).first()
    if not comunidad:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comunidad no encontrada"
        )
    
    db.delete(comunidad)
    db.commit()
    return None

