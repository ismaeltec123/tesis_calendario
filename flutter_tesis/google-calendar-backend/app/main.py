from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config.settings import settings
from app.routes.auth_routes import router as auth_router
from app.routes.calendar_routes import router as calendar_router
from app.routes.sync_routes import router as sync_router

# Crear la aplicación FastAPI
app = FastAPI(
    title="Google Calendar Integration API",
    description="API para sincronización entre Flutter/Firebase y Google Calendar",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas
app.include_router(auth_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(sync_router, prefix="/api")

@app.get("/")
async def root():
    """Endpoint raíz de la API"""
    return {
        "message": "Google Calendar Integration API",
        "version": "1.0.0",
        "endpoints": {
            "auth": "/api/auth",
            "calendar": "/api/calendar",
            "sync": "/api/sync",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de verificación de salud"""
    return {
        "status": "healthy",
        "message": "API funcionando correctamente"
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Manejador global de excepciones"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Error interno del servidor",
            "detail": str(exc) if settings.DEBUG else "Error interno"
        }
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
