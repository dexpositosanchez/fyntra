from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UsuarioBase(BaseModel):
    nombre: str
    email: EmailStr
    rol: str

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    rol: Optional[str] = None
    activo: Optional[bool] = None

class UsuarioResponse(BaseModel):
    """Respuesta de usuario. email es str para aceptar cuentas anonimizadas (eliminado_*@cuenta-eliminada.local)."""
    id: int
    nombre: str
    email: str  # str en lugar de EmailStr para aceptar anonimizados (RGPD)
    rol: str
    activo: bool
    creado_en: Optional[datetime] = None

    class Config:
        from_attributes = True

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    usuario: UsuarioResponse

class CambiarPassword(BaseModel):
    password: str


class EliminarCuentaConfirmacion(BaseModel):
    """Confirmación opcional para ejercer el derecho de supresión (Art. 17 RGPD)."""
    password: Optional[str] = None


class DatosPersonalesExport(BaseModel):
    """Exportación de datos personales del interesado (Art. 15 y 20 RGPD)."""
    exportado_en: datetime
    usuario: dict
    perfil_asociado: Optional[dict] = None  # conductor, propietario o proveedor si aplica
    resumen_actividad: Optional[dict] = None  # conteos o listados básicos según rol

