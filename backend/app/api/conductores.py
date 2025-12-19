from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, timedelta
from app.database import get_db
from app.models.conductor import Conductor
from app.models.usuario import Usuario
from app.schemas.conductor import ConductorCreate, ConductorUpdate, ConductorResponse
from app.api.dependencies import get_current_user
from app.core.security import get_password_hash

router = APIRouter(prefix="/conductores", tags=["conductores"])

def calcular_dias_restantes(fecha_caducidad: date) -> int:
    """Calcula los días restantes hasta la caducidad de la licencia"""
    hoy = date.today()
    return (fecha_caducidad - hoy).days

def licencia_proxima_caducar(fecha_caducidad: date, dias_alerta: int = 30) -> bool:
    """Verifica si la licencia está próxima a caducar (dentro de los próximos N días)"""
    dias_restantes = calcular_dias_restantes(fecha_caducidad)
    return 0 <= dias_restantes <= dias_alerta

@router.get("/", response_model=List[ConductorResponse])
async def listar_conductores(
    activo: Optional[bool] = Query(None),
    licencias_proximas_caducar: Optional[bool] = Query(None, description="Filtrar solo licencias próximas a caducar (30 días)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Conductor)
    
    if activo is not None:
        query = query.filter(Conductor.activo == activo)
    
    conductores = query.offset(skip).limit(limit).all()
    resultados = []
    
    for conductor in conductores:
        dias_restantes = calcular_dias_restantes(conductor.fecha_caducidad_licencia)
        proxima_caducar = licencia_proxima_caducar(conductor.fecha_caducidad_licencia)
        
        # Filtrar por licencias próximas a caducar si se solicita
        if licencias_proximas_caducar and not proxima_caducar:
            continue
        
        # Crear respuesta con campos adicionales
        conductor_data = {
            "id": conductor.id,
            "nombre": conductor.nombre,
            "apellidos": conductor.apellidos,
            "dni": conductor.dni,
            "telefono": conductor.telefono,
            "email": conductor.email,
            "licencia": conductor.licencia,
            "fecha_caducidad_licencia": conductor.fecha_caducidad_licencia,
            "activo": conductor.activo,
            "usuario_id": conductor.usuario_id,
            "creado_en": conductor.creado_en,
            "dias_restantes_licencia": dias_restantes,
            "licencia_proxima_caducar": proxima_caducar
        }
        resultados.append(ConductorResponse(**conductor_data))
    
    return resultados

@router.get("/alertas", response_model=List[ConductorResponse])
async def obtener_alertas_licencias(
    dias_alerta: int = Query(30, ge=1, le=365, description="Días de anticipación para alertar"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtener conductores con licencias próximas a caducar"""
    hoy = date.today()
    fecha_limite = hoy + timedelta(days=dias_alerta)
    
    conductores = db.query(Conductor).filter(
        Conductor.activo == True,
        Conductor.fecha_caducidad_licencia >= hoy,
        Conductor.fecha_caducidad_licencia <= fecha_limite
    ).all()
    
    resultados = []
    for conductor in conductores:
        dias_restantes = calcular_dias_restantes(conductor.fecha_caducidad_licencia)
        conductor_data = {
            "id": conductor.id,
            "nombre": conductor.nombre,
            "apellidos": conductor.apellidos,
            "dni": conductor.dni,
            "telefono": conductor.telefono,
            "email": conductor.email,
            "licencia": conductor.licencia,
            "fecha_caducidad_licencia": conductor.fecha_caducidad_licencia,
            "activo": conductor.activo,
            "usuario_id": conductor.usuario_id,
            "creado_en": conductor.creado_en,
            "dias_restantes_licencia": dias_restantes,
            "licencia_proxima_caducar": True
        }
        resultados.append(ConductorResponse(**conductor_data))
    
    return resultados

@router.get("/{conductor_id}", response_model=ConductorResponse)
async def obtener_conductor(
    conductor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    dias_restantes = calcular_dias_restantes(conductor.fecha_caducidad_licencia)
    proxima_caducar = licencia_proxima_caducar(conductor.fecha_caducidad_licencia)
    conductor_data = {
        "id": conductor.id,
        "nombre": conductor.nombre,
        "apellidos": conductor.apellidos,
        "dni": conductor.dni,
        "telefono": conductor.telefono,
        "email": conductor.email,
        "licencia": conductor.licencia,
        "fecha_caducidad_licencia": conductor.fecha_caducidad_licencia,
        "activo": conductor.activo,
        "usuario_id": conductor.usuario_id,
        "creado_en": conductor.creado_en,
        "dias_restantes_licencia": dias_restantes,
        "licencia_proxima_caducar": proxima_caducar
    }
    
    return ConductorResponse(**conductor_data)

@router.post("/", response_model=ConductorResponse, status_code=status.HTTP_201_CREATED)
async def crear_conductor(
    conductor_data: ConductorCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar permisos
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear conductores"
        )
    
    # Verificar si la licencia ya existe
    existing_licencia = db.query(Conductor).filter(Conductor.licencia == conductor_data.licencia).first()
    if existing_licencia:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un conductor con esta licencia"
        )
    
    # Verificar si el DNI ya existe (si se proporciona)
    if conductor_data.dni:
        existing_dni = db.query(Conductor).filter(Conductor.dni == conductor_data.dni).first()
        if existing_dni:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un conductor con este DNI"
            )
    
    # Verificar si el email ya existe (si se proporciona)
    if conductor_data.email:
        existing_email = db.query(Conductor).filter(Conductor.email == conductor_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un conductor con este email"
            )
        
        # Si se proporciona password, verificar que el email no exista como usuario
        if conductor_data.password:
            usuario_existente = db.query(Usuario).filter(Usuario.email == conductor_data.email).first()
            if usuario_existente:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ya existe un usuario con ese email. No se puede crear un conductor con acceso."
                )
    
    usuario_id = None
    
    # Si se proporciona password y email, crear usuario automáticamente
    if conductor_data.password and conductor_data.email:
        nombre_completo = f"{conductor_data.nombre} {conductor_data.apellidos or ''}".strip()
        nuevo_usuario = Usuario(
            nombre=nombre_completo,
            email=conductor_data.email,
            hash_password=get_password_hash(conductor_data.password),
            rol="conductor",
            activo=conductor_data.activo
        )
        db.add(nuevo_usuario)
        db.flush()  # Para obtener el ID
        usuario_id = nuevo_usuario.id
    
    # Crear conductor (excluyendo password del dump)
    conductor_dict = conductor_data.model_dump(exclude={'password'})
    nuevo_conductor = Conductor(**conductor_dict, usuario_id=usuario_id)
    db.add(nuevo_conductor)
    db.commit()
    db.refresh(nuevo_conductor)
    
    dias_restantes = calcular_dias_restantes(nuevo_conductor.fecha_caducidad_licencia)
    proxima_caducar = licencia_proxima_caducar(nuevo_conductor.fecha_caducidad_licencia)
    conductor_data = {
        "id": nuevo_conductor.id,
        "nombre": nuevo_conductor.nombre,
        "apellidos": nuevo_conductor.apellidos,
        "dni": nuevo_conductor.dni,
        "telefono": nuevo_conductor.telefono,
        "email": nuevo_conductor.email,
        "licencia": nuevo_conductor.licencia,
        "fecha_caducidad_licencia": nuevo_conductor.fecha_caducidad_licencia,
        "activo": nuevo_conductor.activo,
        "usuario_id": nuevo_conductor.usuario_id,
        "creado_en": nuevo_conductor.creado_en,
        "dias_restantes_licencia": dias_restantes,
        "licencia_proxima_caducar": proxima_caducar
    }
    
    return ConductorResponse(**conductor_data)

@router.put("/{conductor_id}", response_model=ConductorResponse)
async def actualizar_conductor(
    conductor_id: int,
    conductor_data: ConductorUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para actualizar conductores"
        )
    
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    update_data = conductor_data.model_dump(exclude_unset=True)
    
    # Verificar duplicados si se actualiza la licencia
    if "licencia" in update_data and update_data["licencia"] != conductor.licencia:
        existing = db.query(Conductor).filter(
            Conductor.licencia == update_data["licencia"],
            Conductor.id != conductor_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un conductor con esta licencia"
            )
    
    # Verificar duplicados si se actualiza el DNI
    if "dni" in update_data and update_data["dni"] and update_data["dni"] != conductor.dni:
        existing = db.query(Conductor).filter(
            Conductor.dni == update_data["dni"],
            Conductor.id != conductor_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un conductor con este DNI"
            )
    
    # Verificar duplicados si se actualiza el email
    if "email" in update_data and update_data["email"] and update_data["email"] != conductor.email:
        existing = db.query(Conductor).filter(
            Conductor.email == update_data["email"],
            Conductor.id != conductor_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un conductor con este email"
            )
        # Si el email cambia y hay un usuario asociado, actualizar el email del usuario
        if conductor.usuario_id:
            usuario_asociado = db.query(Usuario).filter(Usuario.id == conductor.usuario_id).first()
            if usuario_asociado:
                usuario_asociado.email = update_data["email"]
    
    # Manejar creación/actualización de usuario si se proporciona password
    password = update_data.pop("password", None)
    if password:
        if not conductor.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El conductor debe tener un email para crear un usuario"
            )
        
        if conductor.usuario_id:
            # Actualizar contraseña del usuario existente
            usuario_asociado = db.query(Usuario).filter(Usuario.id == conductor.usuario_id).first()
            if usuario_asociado:
                usuario_asociado.hash_password = get_password_hash(password)
        else:
            # Crear nuevo usuario
            nombre_completo = f"{conductor.nombre} {conductor.apellidos or ''}".strip()
            nuevo_usuario = Usuario(
                nombre=nombre_completo,
                email=conductor.email,
                hash_password=get_password_hash(password),
                rol="conductor",
                activo=conductor.activo
            )
            db.add(nuevo_usuario)
            db.flush()
            conductor.usuario_id = nuevo_usuario.id
    
    # Actualizar campos del conductor (excluyendo password que ya se procesó)
    for field, value in update_data.items():
        setattr(conductor, field, value)
    
    # Actualizar nombre del usuario si cambia el nombre del conductor
    if conductor.usuario_id and ("nombre" in update_data or "apellidos" in update_data):
        usuario_asociado = db.query(Usuario).filter(Usuario.id == conductor.usuario_id).first()
        if usuario_asociado:
            nombre_completo = f"{conductor.nombre} {conductor.apellidos or ''}".strip()
            usuario_asociado.nombre = nombre_completo
    
    # Actualizar estado activo del usuario si cambia
    if conductor.usuario_id and "activo" in update_data:
        usuario_asociado = db.query(Usuario).filter(Usuario.id == conductor.usuario_id).first()
        if usuario_asociado:
            usuario_asociado.activo = update_data["activo"]
    
    db.commit()
    db.refresh(conductor)
    
    dias_restantes = calcular_dias_restantes(conductor.fecha_caducidad_licencia)
    proxima_caducar = licencia_proxima_caducar(conductor.fecha_caducidad_licencia)
    conductor_data = {
        "id": conductor.id,
        "nombre": conductor.nombre,
        "apellidos": conductor.apellidos,
        "dni": conductor.dni,
        "telefono": conductor.telefono,
        "email": conductor.email,
        "licencia": conductor.licencia,
        "fecha_caducidad_licencia": conductor.fecha_caducidad_licencia,
        "activo": conductor.activo,
        "usuario_id": conductor.usuario_id,
        "creado_en": conductor.creado_en,
        "dias_restantes_licencia": dias_restantes,
        "licencia_proxima_caducar": proxima_caducar
    }
    
    return ConductorResponse(**conductor_data)

@router.delete("/{conductor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_conductor(
    conductor_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para eliminar conductores"
        )
    
    conductor = db.query(Conductor).filter(Conductor.id == conductor_id).first()
    if not conductor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conductor no encontrado"
        )
    
    db.delete(conductor)
    db.commit()
    return None

