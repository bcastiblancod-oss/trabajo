"""
Paquete de routers - Hotel Boutique
"""
from .auth import router as auth_router
from .usuarios import router as usuarios_router
from .habitaciones import router as habitaciones_router
from .reservas import router as reservas_router
from .checkin_checkout import router as checkin_checkout_router
from .pagos import router as pagos_router
from .facturas import router as facturas_router
from .reportes import router as reportes_router

__all__ = [
    "auth_router",
    "usuarios_router",
    "habitaciones_router",
    "reservas_router",
    "checkin_checkout_router",
    "pagos_router",
    "facturas_router",
    "reportes_router"
]
