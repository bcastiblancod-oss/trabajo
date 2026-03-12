"""
Sistema de Gestión de Reservas - Hotel Boutique
API REST con FastAPI + MongoDB

Módulos:
- Autenticación (JWT)
- Usuarios (RBAC: huésped, recepcionista, administrador)
- Habitaciones (CRUD, disponibilidad)
- Reservas (CRUD, cancelación con políticas)
- Check-in / Check-out
- Pagos
- Facturas
- Reportes
"""
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configuration
from config import MONGO_URL, DB_NAME, CORS_ORIGINS

# Routers
from routers import (
    auth_router,
    usuarios_router,
    habitaciones_router,
    reservas_router,
    checkin_checkout_router,
    pagos_router,
    facturas_router,
    reportes_router
)

# Database initialization
from init_db import init_database, get_database_stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for startup and shutdown events"""
    # Startup
    logger.info("Iniciando Sistema de Gestión de Reservas - Hotel Boutique")
    logger.info(f"Conectando a MongoDB: {MONGO_URL}")
    
    # Initialize database with seed data
    initialized = await init_database(db)
    if initialized:
        logger.info("Base de datos inicializada con datos semilla")
    
    stats = await get_database_stats(db)
    logger.info(f"Estadísticas de BD: {stats}")
    
    yield
    
    # Shutdown
    logger.info("Cerrando conexión a MongoDB")
    client.close()


# Create FastAPI app
app = FastAPI(
    title="Hotel Boutique - Sistema de Gestión de Reservas",
    description="""
## Sistema de Gestión de Reservas para Hotel Boutique

API REST para gestionar reservas, habitaciones, huéspedes y operaciones hoteleras.

### Módulos disponibles:
- **Autenticación**: Login, registro, gestión de sesiones (JWT)
- **Usuarios**: CRUD de usuarios con roles (RBAC)
- **Habitaciones**: Gestión de 24 habitaciones (estándar, suite, familiar)
- **Reservas**: Consulta de disponibilidad, creación, modificación y cancelación
- **Check-in/Check-out**: Procesos de entrada y salida
- **Pagos**: Registro de pagos (tarjeta, efectivo, transferencia)
- **Facturas**: Generación de facturas electrónicas
- **Reportes**: Ocupación, ingresos, top clientes

### Roles de usuario:
- **Huésped**: Puede crear y gestionar sus propias reservas
- **Recepcionista**: Gestiona reservas, check-in/out, facturación
- **Administrador**: Acceso total + usuarios + reportes

### Credenciales de prueba:
- **Admin**: admin@hotelimperium.com / Admin123!
- **Recepcionista**: recepcion@hotelimperium.com / Recep123!
- **Huésped**: huesped@test.com / Huesped123!
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Router with /api prefix
api_router = APIRouter(prefix="/api")

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(usuarios_router)
api_router.include_router(habitaciones_router)
api_router.include_router(reservas_router)
api_router.include_router(checkin_checkout_router)
api_router.include_router(pagos_router)
api_router.include_router(facturas_router)
api_router.include_router(reportes_router)


# Root endpoint
@api_router.get("/")
async def root():
    """Endpoint raíz - Información del sistema"""
    return {
        "nombre": "Hotel Boutique - Sistema de Gestión de Reservas",
        "version": "1.0.0",
        "descripcion": "API REST para gestión hotelera",
        "documentacion": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "usuarios": "/api/usuarios",
            "habitaciones": "/api/habitaciones",
            "reservas": "/api/reservas",
            "checkin": "/api/checkin",
            "checkout": "/api/checkout",
            "pagos": "/api/pagos",
            "facturas": "/api/facturas",
            "reportes": "/api/reportes"
        }
    }


# Health check endpoint
@api_router.get("/health")
async def health_check():
    """Health check para monitoreo"""
    try:
        # Check MongoDB connection
        await db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    stats = await get_database_stats(db)
    
    return {
        "status": "healthy" if db_status == "connected" else "unhealthy",
        "database": db_status,
        "stats": stats
    }


# Servicios adicionales endpoint
@api_router.get("/servicios-adicionales")
async def list_additional_services():
    """Listar servicios adicionales disponibles"""
    servicios = await db.servicios_adicionales.find({}, {"_id": 0}).to_list(100)
    return servicios


# Include API router in main app
app.include_router(api_router)


# Export db for use in routers
__all__ = ["app", "db"]
