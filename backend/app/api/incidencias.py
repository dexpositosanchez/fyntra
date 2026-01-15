from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from datetime import datetime, timezone
from app.database import get_db
from app.models.incidencia import Incidencia, EstadoIncidencia, PrioridadIncidencia
from app.models.usuario import Usuario
from app.models.propietario import Propietario
from app.models.inmueble import Inmueble
from app.models.historial_incidencia import HistorialIncidencia
from app.schemas.incidencia import IncidenciaCreate, IncidenciaUpdate, IncidenciaResponse, HistorialIncidenciaResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/incidencias", tags=["incidencias"])

def registrar_cambio_estado(db: Session, incidencia_id: int, usuario_id: int, 
                            estado_anterior: Optional[str], estado_nuevo: str, 
                            comentario: Optional[str] = None):
    """Registra un cambio de estado en el historial"""
    historial = HistorialIncidencia(
        incidencia_id=incidencia_id,
        usuario_id=usuario_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        comentario=comentario
    )
    db.add(historial)

def incidencia_to_response(incidencia: Incidencia, db: Session) -> dict:
    """Convierte una incidencia a dict con historial y actuaciones_count"""
    historial = []
    for h in incidencia.historial:
        usuario = db.query(Usuario).filter(Usuario.id == h.usuario_id).first()
        historial.append({
            "id": h.id,
            "estado_anterior": h.estado_anterior,
            "estado_nuevo": h.estado_nuevo,
            "comentario": h.comentario,
            "fecha": h.fecha,
            "usuario_nombre": usuario.nombre if usuario else None
        })
    
    # Contar actuaciones y documentos
    from app.models.actuacion import Actuacion
    from app.models.documento import Documento
    actuaciones_count = db.query(Actuacion).filter(Actuacion.incidencia_id == incidencia.id).count()
    documentos_count = db.query(Documento).filter(Documento.incidencia_id == incidencia.id).count()
    
    return {
        "id": incidencia.id,
        "titulo": incidencia.titulo,
        "descripcion": incidencia.descripcion,
        "prioridad": incidencia.prioridad,
        "inmueble_id": incidencia.inmueble_id,
        "creador_usuario_id": incidencia.creador_usuario_id,
        "proveedor_id": incidencia.proveedor_id,
        "estado": incidencia.estado,
        "fecha_alta": incidencia.fecha_alta,
        "fecha_cierre": incidencia.fecha_cierre,
        "version": incidencia.version,
        "creado_en": incidencia.creado_en,
        "inmueble": incidencia.inmueble,
        "historial": historial,
        "actuaciones_count": actuaciones_count,
        "documentos_count": documentos_count
    }

def get_inmuebles_propietario(db: Session, usuario_id: int) -> List[int]:
    """Obtiene los IDs de inmuebles asociados al propietario del usuario"""
    propietario = db.query(Propietario).filter(Propietario.usuario_id == usuario_id).first()
    if not propietario:
        return []
    return [inmueble.id for inmueble in propietario.inmuebles]

@router.get("/", response_model=List[IncidenciaResponse])
async def listar_incidencias(
    estado: Optional[EstadoIncidencia] = Query(None),
    prioridad: Optional[PrioridadIncidencia] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Incidencia).options(
        joinedload(Incidencia.inmueble),
        joinedload(Incidencia.historial)
    )
    
    # Filtros según rol
    if current_user.rol == "propietario":
        # Propietarios solo ven incidencias de sus inmuebles
        inmueble_ids = get_inmuebles_propietario(db, current_user.id)
        if inmueble_ids:
            query = query.filter(Incidencia.inmueble_id.in_(inmueble_ids))
        else:
            return []  # Sin inmuebles, sin incidencias
    elif current_user.rol == "proveedor":
        # Proveedores solo ven incidencias asignadas a ellos
        from app.models.proveedor import Proveedor
        proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == current_user.id).first()
        if proveedor:
            query = query.filter(Incidencia.proveedor_id == proveedor.id)
        else:
            return []  # Sin proveedor asociado, sin incidencias
    
    if estado:
        query = query.filter(Incidencia.estado == estado)
    if prioridad:
        query = query.filter(Incidencia.prioridad == prioridad)
    
    incidencias = query.order_by(Incidencia.fecha_alta.desc()).offset(skip).limit(limit).all()
    return [IncidenciaResponse.model_validate(incidencia_to_response(inc, db)) for inc in incidencias]

@router.get("/sin-resolver", response_model=List[IncidenciaResponse])
async def listar_incidencias_sin_resolver(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista incidencias que no están cerradas"""
    query = db.query(Incidencia).options(
        joinedload(Incidencia.inmueble),
        joinedload(Incidencia.historial)
    ).filter(Incidencia.estado != EstadoIncidencia.CERRADA)
    
    # Filtros según rol
    if current_user.rol == "propietario":
        inmueble_ids = get_inmuebles_propietario(db, current_user.id)
        if inmueble_ids:
            query = query.filter(Incidencia.inmueble_id.in_(inmueble_ids))
        else:
            return []
    elif current_user.rol == "proveedor":
        from app.models.proveedor import Proveedor
        proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == current_user.id).first()
        if proveedor:
            query = query.filter(Incidencia.proveedor_id == proveedor.id)
        else:
            return []
    
    incidencias = query.order_by(Incidencia.fecha_alta.desc()).all()
    return [IncidenciaResponse.model_validate(incidencia_to_response(inc, db)) for inc in incidencias]

@router.get("/{incidencia_id}", response_model=IncidenciaResponse)
async def obtener_incidencia(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencia = db.query(Incidencia).options(
        joinedload(Incidencia.inmueble),
        joinedload(Incidencia.historial)
    ).filter(Incidencia.id == incidencia_id).first()
    
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidencia no encontrada"
        )
    
    # Propietarios solo pueden ver incidencias de sus inmuebles
    if current_user.rol == "propietario":
        inmueble_ids = get_inmuebles_propietario(db, current_user.id)
        if incidencia.inmueble_id not in inmueble_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a esta incidencia"
            )
    
    return IncidenciaResponse.model_validate(incidencia_to_response(incidencia, db))

@router.post("/", response_model=IncidenciaResponse, status_code=status.HTTP_201_CREATED)
async def crear_incidencia(
    incidencia_data: IncidenciaCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Propietarios solo pueden crear incidencias en sus inmuebles
    if current_user.rol == "propietario" and incidencia_data.inmueble_id:
        inmueble_ids = get_inmuebles_propietario(db, current_user.id)
        if incidencia_data.inmueble_id not in inmueble_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puede crear incidencias en inmuebles que no le pertenecen"
            )
    
    # Verificar que el inmueble existe
    inmueble = db.query(Inmueble).filter(Inmueble.id == incidencia_data.inmueble_id).first()
    if not inmueble:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inmueble no encontrado"
        )
    
    nueva_incidencia = Incidencia(
        **incidencia_data.model_dump(),
        creador_usuario_id=current_user.id,
        estado=EstadoIncidencia.ABIERTA
    )
    db.add(nueva_incidencia)
    db.flush()
    
    # Registrar en historial
    registrar_cambio_estado(
        db, nueva_incidencia.id, current_user.id,
        None, EstadoIncidencia.ABIERTA.value,
        "Incidencia creada"
    )
    
    db.commit()
    db.refresh(nueva_incidencia)
    return IncidenciaResponse.model_validate(incidencia_to_response(nueva_incidencia, db))

@router.put("/{incidencia_id}", response_model=IncidenciaResponse)
async def actualizar_incidencia(
    incidencia_id: int,
    incidencia_data: IncidenciaUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidencia = db.query(Incidencia).options(
        joinedload(Incidencia.inmueble),
        joinedload(Incidencia.historial)
    ).filter(Incidencia.id == incidencia_id).first()
    
    if not incidencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incidencia no encontrada"
        )
    
    # Propietarios solo pueden actualizar sus incidencias
    if current_user.rol == "propietario":
        inmueble_ids = get_inmuebles_propietario(db, current_user.id)
        if incidencia.inmueble_id not in inmueble_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a esta incidencia"
            )
    
    # Optimistic locking
    if incidencia_data.version and incidencia.version != incidencia_data.version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="La incidencia ha sido modificada por otro usuario"
        )
    
    # Detectar cambio de estado para historial
    estado_anterior = incidencia.estado.value if incidencia.estado else None
    nuevo_estado = incidencia_data.estado.value if incidencia_data.estado else None
    
    update_data = incidencia_data.model_dump(exclude_unset=True, exclude={'comentario_cambio'})
    for field, value in update_data.items():
        setattr(incidencia, field, value)
    
    # Si cambió el estado, registrar en historial
    if nuevo_estado and nuevo_estado != estado_anterior:
        registrar_cambio_estado(
            db, incidencia.id, current_user.id,
            estado_anterior, nuevo_estado,
            incidencia_data.comentario_cambio
        )
        
        # Si se cierra, registrar fecha de cierre
        if incidencia_data.estado == EstadoIncidencia.CERRADA:
            incidencia.fecha_cierre = datetime.now(timezone.utc)
    
    incidencia.version += 1
    db.commit()
    db.refresh(incidencia)
    return IncidenciaResponse.model_validate(incidencia_to_response(incidencia, db))

@router.delete("/{incidencia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_incidencia(
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
    
    # Permisos: super_admin, admin_fincas, o el propietario que creó la incidencia
    puede_eliminar = False
    
    if current_user.rol in ["super_admin", "admin_fincas"]:
        puede_eliminar = True
    elif current_user.rol == "propietario":
        # El propietario puede eliminar si es el creador de la incidencia
        if incidencia.creador_usuario_id == current_user.id:
            puede_eliminar = True
        else:
            # También puede eliminar si la incidencia es de uno de sus inmuebles
            inmueble_ids = get_inmuebles_propietario(db, current_user.id)
            if incidencia.inmueble_id in inmueble_ids:
                puede_eliminar = True
    
    if not puede_eliminar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar esta incidencia"
        )
    
    # Eliminar historial asociado primero (no tiene cascade configurado)
    db.query(HistorialIncidencia).filter(HistorialIncidencia.incidencia_id == incidencia_id).delete()
    
    # Eliminar la incidencia (las relaciones con cascade se eliminarán automáticamente)
    db.delete(incidencia)
    db.commit()
    return None

