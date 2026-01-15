from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://fyntra_user:fyntra_password@postgres:5432/fyntra")

# Configuración del pool de conexiones para optimizar rendimiento y concurrencia
# pool_size: número de conexiones mantenidas en el pool
# max_overflow: conexiones adicionales permitidas más allá del pool_size
# pool_pre_ping: verifica que las conexiones estén vivas antes de usarlas
# pool_recycle: recicla conexiones después de este tiempo (segundos) para evitar conexiones obsoletas
engine = create_engine(
    DATABASE_URL,
    pool_size=20,              # 20 conexiones en el pool base
    max_overflow=10,            # Permite hasta 10 conexiones adicionales (total: 30)
    pool_pre_ping=True,        # Verifica conexiones antes de usar
    pool_recycle=3600,         # Recicla conexiones cada hora
    echo=False                 # Cambiar a True para debug de SQL
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

