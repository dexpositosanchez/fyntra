from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.incidencia import Incidencia, EstadoIncidencia, PrioridadIncidencia
from app.models.usuario import Usuario
from app.schemas.incidencia import IncidenciaCreate, IncidenciaUpdate, IncidenciaResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/incidencias", tags=["incidencias"])

@router.get("/", response_model=List[IncidenciaResponse])
async def listar_incidencias(
    estado: Optional[EstadoIncidencia] = Query(None),
    prioridad: Optional[PrioridadIncidencia] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Incidencia)
    
    # Filtros según rol
    if current_user.rol == "propietario":
        # Los propietarios solo ven sus propias incidencias
        # Necesitaríamos una relación con inmuebles del propietario
        pass
    
    if estado:
        query = query.filter(Incidencia.estado == estado)
    if prioridad:
        query = query.filter(Incidencia.prioridad == prioridad)
    
    incidencias = query.offset(skip).limit(limit).all()
    return [IncidenciaResponse.model_validate(inc) for inc in incidencias]

@router.get("/sin-resolver", response_model=List[IncidenciaResponse])
async def listar_incidencias_sin_resolver(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista incidencias que no están cerradas"""
    incidencias = db.query(Incidencia).filter(
        Incidencia.estado != EstadoIncidencia.CERRADA
    ).all()
    return [IncidenciaResponse.model_validate(inc) for inc in incidencias]

@router.get("/{incidencia_id}", response_model=IncidenciaResponse)
async def obtener_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidencia no encontrada"
        )
    return IncidenciaResponse.model_validate(incidencia)

@router.post("/", response_model=IncidenciaResponse, status_code=status.HTTP_201_CREATED)
async def crear_incidencia(
    incidencia_data: IncidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    nueva_incidencia = Incidencia(
        **incidencia_data.model_dump(),
        creador_usuario_id=current_user.id
    )
    db.add(nueva_incidencia)
    db.commit()
    db.refresh(nueva_incidencia)
    return IncidenciaResponse.model_validate(nueva_incidencia)

@router.put("/{incidencia_id}", response_model=IncidenciaResponse)
async def actualizar_incidencia(
    incidencia_id: int,
    incidencia_data: IncidenciaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidencia no encontrada"
        )
    
    # Optimistic locking
    if incidencia_data.version and incidencia.version != incidencia_data.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La incidencia ha sido modificada por otro usuario"
        )
    
    update_data = incidencia_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(incidencia, field, value)
    
    incidencia.version += 1
    db.commit()
    db.refresh(incidencia)
    return IncidenciaResponse.model_validate(incidencia)

@router.delete("/{incidencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_fincas"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar incidencias"
        )
    
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidencia no encontrada"
        )
    
    db.delete(incidencia)
    db.commit()
    return None

