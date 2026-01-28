"""
Script para crear usuarios para todos los conductores que no tienen usuario asociado
Ejecutar desde el directorio raíz del backend: python scripts/migrate_conductores_sin_usuario.py
"""
import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.conductor import Conductor
from app.models.usuario import Usuario
from app.core.security import get_password_hash

def migrate_conductores_sin_usuario():
    """Crear usuarios para todos los conductores que tienen email pero no tienen usuario_id"""
    db: Session = SessionLocal()
    
    try:
        # Obtener todos los conductores sin usuario pero con email
        conductores_sin_usuario = db.query(Conductor).filter(
            Conductor.usuario_id.is_(None),
            Conductor.email.isnot(None)
        ).all()
        
        if not conductores_sin_usuario:
            print("✅ Todos los conductores ya tienen usuarios asociados.")
            return
        
        print(f"📋 Encontrados {len(conductores_sin_usuario)} conductores sin usuario.")
        
        creados = 0
        errores = 0
        
        for conductor in conductores_sin_usuario:
            try:
                # Verificar que no exista ya un usuario con ese email
                usuario_existente = db.query(Usuario).filter(Usuario.email == conductor.email).first()
                if usuario_existente:
                    print(f"⚠️  Ya existe un usuario con el email {conductor.email} para el conductor {conductor.nombre} {conductor.apellidos}")
                    # Vincular el conductor al usuario existente
                    conductor.usuario_id = usuario_existente.id
                    db.commit()
                    print(f"   ✅ Conductor vinculado al usuario existente (ID: {usuario_existente.id})")
                    continue
                
                # Construir nombre completo
                nombre_completo = f"{conductor.nombre} {conductor.apellidos or ''}".strip()
                
                # Generar password por defecto (parte antes del @ del email + "123")
                password_default = conductor.email.split("@")[0] + "123"
                
                # Crear usuario
                nuevo_usuario = Usuario(
                    nombre=nombre_completo,
                    email=conductor.email,
                    hash_password=get_password_hash(password_default),
                    rol="conductor",
                    activo=conductor.activo
                )
                db.add(nuevo_usuario)
                db.flush()  # Para obtener el ID
                
                # Vincular conductor al usuario
                conductor.usuario_id = nuevo_usuario.id
                db.commit()
                
                creados += 1
                print(f"✅ Usuario creado para {nombre_completo} (ID conductor: {conductor.id}, Email: {conductor.email}, Password: {password_default})")
                
            except Exception as e:
                db.rollback()
                errores += 1
                print(f"❌ Error al crear usuario para {conductor.nombre} {conductor.apellidos}: {str(e)}")
        
        print(f"\n📊 Resumen:")
        print(f"   ✅ Usuarios creados: {creados}")
        print(f"   ❌ Errores: {errores}")
        print(f"   📝 Total procesados: {len(conductores_sin_usuario)}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error general: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Iniciando migración de conductores sin usuario...")
    migrate_conductores_sin_usuario()
    print("✨ Migración completada.")
