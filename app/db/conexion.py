from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, registry
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#--- LÍNEA A AÑADIR ---
# Esta línea le dice a SQLAlchemy: "Ahora que todos los modelos que heredan
# de 'Base' han sido cargados, por favor, resuelve todas las relaciones pendientes".
registry().configure()