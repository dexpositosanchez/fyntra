from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from datetime import datetime
from app.database import get_db
from app.models.documento import Documento
from app.models.incidencia import Incidencia
from app.models.proveedor import Proveedor
from app.models.propietario import Propietario
from app.models.usuario import Usuario
from app.schemas.documento import DocumentoResponse
from app.api.dependencies import get_current_user
from app.core.security import decode_access_token
from app.core.cache import (
    get_from_cache, set_to_cache, generate_cache_key,
    invalidate_documentos_cache, delete_from_cache
)

router = APIRouter(prefix="/documentos", tags=["documentos"])

# Directorio para almacenar archivos
UPLOAD_DIR = "/app/uploads/documentos"

# Tipos de archivo permitidos
ALLOWED_EXTENSIONS = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf',
    'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def verificar_acceso_incidencia(db: Session, incidencia_id: int, usuario: Usuario) -> Incidencia:
    """Verifica que el usuario tiene acceso a la incidencia"""
    incidencia = db.query(Incidencia).filter(Incidencia.id == incidencia_id).first()
    if not incidencia:
        raise HTTPException(status_code=404, detail="Incidencia no encontrada")
    
    # Super admin y admin fincas tienen acceso total
    if usuario.rol in ["super_admin", "admin_fincas"]:
        return incidencia
    
    # Propietario: solo si el inmueble le pertenece
    if usuario.rol == "propietario":
        propietario = db.query(Propietario).filter(Propietario.usuario_id == usuario.id).first()
        if propietario:
            inmueble_ids = [i.id for i in propietario.inmuebles]
            if incidencia.inmueble_id in inmueble_ids:
                return incidencia
        raise HTTPException(status_code=403, detail="No tiene acceso a esta incidencia")
    
    # Proveedor: solo si está asignado
    if usuario.rol == "proveedor":
        proveedor = db.query(Proveedor).filter(Proveedor.usuario_id == usuario.id).first()
        if proveedor and incidencia.proveedor_id == proveedor.id:
            return incidencia
        raise HTTPException(status_code=403, detail="No tiene acceso a esta incidencia")
    
    raise HTTPException(status_code=403, detail="No tiene permisos")

def documento_to_response(doc: Documento, db: Session) -> dict:
    """Convierte documento a respuesta con nombre del usuario"""
    usuario = db.query(Usuario).filter(Usuario.id == doc.usuario_id).first()
    return {
        "id": doc.id,
        "incidencia_id": doc.incidencia_id,
        "usuario_id": doc.usuario_id,
        "nombre": doc.nombre,
        "nombre_archivo": doc.nombre_archivo,
        "tipo_archivo": doc.tipo_archivo,
        "tamano": doc.tamano,
        "creado_en": doc.creado_en,
        "subido_por": usuario.nombre if usuario else None
    }

@router.get("/incidencia/{incidencia_id}", response_model=List[DocumentoResponse])
async def listar_documentos(
    incidencia_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los documentos de una incidencia"""
    verificar_acceso_incidencia(db, incidencia_id, current_user)
    
    # Generar clave de caché
    cache_key = generate_cache_key("documentos:incidencia", incidencia_id=incidencia_id)
    
    # Intentar obtener de caché
    cached_result = get_from_cache(cache_key)
    if cached_result is not None:
        return cached_result
    
    documentos = db.query(Documento).filter(
        Documento.incidencia_id == incidencia_id
    ).order_by(Documento.creado_en.desc()).all()
    
    result = [documento_to_response(doc, db) for doc in documentos]
    
    # Almacenar en caché (5 minutos)
    set_to_cache(cache_key, result, expire=300)
    
    return result

@router.post("/", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
async def subir_documento(
    incidencia_id: int = Form(...),
    nombre: str = Form(...),
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Sube un documento a una incidencia"""
    # Verificar acceso
    verificar_acceso_incidencia(db, incidencia_id, current_user)
    
    # Validar tipo de archivo
    if archivo.content_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Tipo de archivo no permitido. Permitidos: imágenes, PDF, Word, Excel"
        )
    
    # Leer contenido para validar tamano
    contenido = await archivo.read()
    if len(contenido) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="El archivo excede el tamano máximo de 10MB")
    
    # Crear directorio si no existe
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generar nombre único para el archivo
    extension = os.path.splitext(archivo.filename)[1] if archivo.filename else ""
    nombre_unico = f"{uuid.uuid4()}{extension}"
    ruta_completa = os.path.join(UPLOAD_DIR, nombre_unico)
    
    # Guardar archivo
    with open(ruta_completa, "wb") as f:
        f.write(contenido)
    
    # Crear registro en BD
    nuevo_documento = Documento(
        incidencia_id=incidencia_id,
        usuario_id=current_user.id,
        nombre=nombre,
        nombre_archivo=archivo.filename or "archivo",
        tipo_archivo=archivo.content_type,
        ruta_archivo=ruta_completa,
        tamano=len(contenido)
    )
    db.add(nuevo_documento)
    db.commit()
    db.refresh(nuevo_documento)
    
    # Invalidar caché de documentos de esta incidencia
    invalidate_documentos_cache()
    delete_from_cache(generate_cache_key("documentos:incidencia", incidencia_id=incidencia_id))
    
    return documento_to_response(nuevo_documento, db)

@router.get("/{documento_id}/archivo")
async def descargar_documento(
    documento_id: int,
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Descarga/visualiza un documento"""
    # Obtener usuario desde token en query param
    if not token:
        raise HTTPException(status_code=401, detail="Token requerido")
    
    try:
        payload = decode_access_token(token)
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token inválido")
        current_user = db.query(Usuario).filter(Usuario.email == email).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Verificar acceso a la incidencia
    verificar_acceso_incidencia(db, documento.incidencia_id, current_user)
    
    # Verificar que el archivo existe
    if not os.path.exists(documento.ruta_archivo):
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor")
    
    # Determinar si mostrar inline o descargar
    # Imágenes y PDFs se pueden mostrar inline
    media_type = documento.tipo_archivo or "application/octet-stream"
    inline_types = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'}
    
    if media_type in inline_types:
        return FileResponse(
            documento.ruta_archivo,
            media_type=media_type,
            filename=documento.nombre_archivo,
            headers={"Content-Disposition": f"inline; filename={documento.nombre_archivo}"}
        )
    else:
        return FileResponse(
            documento.ruta_archivo,
            media_type=media_type,
            filename=documento.nombre_archivo
        )

@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_documento(
    documento_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Elimina un documento (solo el propietario del documento)"""
    documento = db.query(Documento).filter(Documento.id == documento_id).first()
    if not documento:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    # Solo el usuario que subió el documento puede eliminarlo
    if documento.usuario_id != current_user.id and current_user.rol != "super_admin":
        raise HTTPException(
            status_code=403, 
            detail="Solo puede eliminar documentos que usted haya subido"
        )
    
    # Eliminar archivo físico
    if os.path.exists(documento.ruta_archivo):
        os.remove(documento.ruta_archivo)
    
    # Eliminar registro
    incidencia_id = documento.incidencia_id
    db.delete(documento)
    db.commit()
    
    # Invalidar caché de documentos de esta incidencia
    invalidate_documentos_cache()
    delete_from_cache(generate_cache_key("documentos:incidencia", incidencia_id=incidencia_id))
    
    return None

