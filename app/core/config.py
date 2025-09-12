from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Mi Proyecto SAAS"
    DATABASE_URL: str = "postgresql://user:password@host:port/dbname"

    # Nuevas variables de seguridad
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    GOOGLE_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()

# --- AÑADE ESTA LÍNEA TEMPORALMENTE PARA DEPURAR ---
#print("--- DEBUG: GOOGLE_API_KEY cargada:", settings.GOOGLE_API_KEY)

# --- FIN DE LA LÍNEA TEMPORAL ---
