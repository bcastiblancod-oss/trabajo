"""
Inicialización de datos del sistema - Hotel Boutique
Pre-carga las 24 habitaciones, tipos, servicios y usuario admin
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

from config import (
    MONGO_URL, 
    DB_NAME, 
    ROOM_TYPES_CONFIG, 
    ROOMS_CONFIG,
    ADDITIONAL_SERVICES
)
from utils import hash_password


async def init_database(db):
    """Initialize database with seed data"""
    
    # Check if already initialized
    existing_rooms = await db.habitaciones.count_documents({})
    if existing_rooms > 0:
        print("Base de datos ya inicializada")
        return False
    
    print("Inicializando base de datos...")
    
    # 1. Create Room Types
    tipos_habitacion = {}
    for tipo_config in ROOM_TYPES_CONFIG:
        tipo_id = str(uuid.uuid4())
        tipo_doc = {
            "id": tipo_id,
            **tipo_config
        }
        await db.tipos_habitacion.insert_one(tipo_doc)
        tipos_habitacion[tipo_config["codigo"]] = tipo_id
        print(f"  Tipo de habitación creado: {tipo_config['nombre']}")
    
    # 2. Create 24 Rooms
    for room_config in ROOMS_CONFIG:
        room_id = str(uuid.uuid4())
        tipo_id = tipos_habitacion[room_config["tipo_codigo"]]
        
        room_doc = {
            "id": room_id,
            "numero": room_config["numero"],
            "piso": room_config["piso"],
            "tipo_habitacion_id": tipo_id,
            "descripcion": f"Habitación {room_config['numero']} - Piso {room_config['piso']}",
            "fotos": [],
            "estado": "disponible",
            "precio_temporada_alta": None,
            "precio_temporada_baja": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None
        }
        await db.habitaciones.insert_one(room_doc)
    print(f"  24 habitaciones creadas")
    
    # 3. Create Additional Services
    for servicio_config in ADDITIONAL_SERVICES:
        servicio_id = str(uuid.uuid4())
        servicio_doc = {
            "id": servicio_id,
            **servicio_config
        }
        await db.servicios_adicionales.insert_one(servicio_doc)
    print(f"  Servicios adicionales creados")
    
    # 4. Create Admin User
    admin_id = str(uuid.uuid4())
    admin_doc = {
        "id": admin_id,
        "email": "admin@hotelimperium.com",
        "nombre_completo": "Administrador Hotel",
        "documento": "1234567890",
        "telefono": "+57 300 123 4567",
        "rol": "administrador",
        "password_hash": hash_password("Admin123!"),
        "activo": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    await db.usuarios.insert_one(admin_doc)
    print(f"  Usuario administrador creado: admin@hotelimperium.com / Admin123!")
    
    # 5. Create Receptionist User
    recep_id = str(uuid.uuid4())
    recep_doc = {
        "id": recep_id,
        "email": "recepcion@hotelimperium.com",
        "nombre_completo": "Recepcionista Hotel",
        "documento": "0987654321",
        "telefono": "+57 300 765 4321",
        "rol": "recepcionista",
        "password_hash": hash_password("Recep123!"),
        "activo": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    await db.usuarios.insert_one(recep_doc)
    print(f"  Usuario recepcionista creado: recepcion@hotelimperium.com / Recep123!")
    
    # 6. Create Test Guest User
    guest_id = str(uuid.uuid4())
    guest_doc = {
        "id": guest_id,
        "email": "huesped@test.com",
        "nombre_completo": "Huésped de Prueba",
        "documento": "1122334455",
        "telefono": "+57 300 111 2222",
        "rol": "huesped",
        "password_hash": hash_password("Huesped123!"),
        "activo": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": None
    }
    await db.usuarios.insert_one(guest_doc)
    print(f"  Usuario huésped creado: huesped@test.com / Huesped123!")
    
    # Create indexes
    await db.usuarios.create_index("email", unique=True)
    await db.usuarios.create_index("documento")
    await db.habitaciones.create_index("numero", unique=True)
    await db.habitaciones.create_index("estado")
    await db.reservas.create_index("codigo", unique=True)
    await db.reservas.create_index("usuario_id")
    await db.reservas.create_index("habitacion_id")
    await db.reservas.create_index("estado")
    await db.reservas.create_index([("fecha_checkin", 1), ("fecha_checkout", 1)])
    await db.facturas.create_index("numero", unique=True)
    await db.logs_auditoria.create_index("usuario_id")
    await db.logs_auditoria.create_index("fecha")
    print("  Índices creados")
    
    print("Inicialización completada exitosamente!")
    return True


async def get_database_stats(db):
    """Get database statistics"""
    stats = {
        "usuarios": await db.usuarios.count_documents({}),
        "tipos_habitacion": await db.tipos_habitacion.count_documents({}),
        "habitaciones": await db.habitaciones.count_documents({}),
        "servicios_adicionales": await db.servicios_adicionales.count_documents({}),
        "reservas": await db.reservas.count_documents({}),
        "facturas": await db.facturas.count_documents({}),
    }
    return stats


if __name__ == "__main__":
    # Run initialization directly
    async def main():
        client = AsyncIOMotorClient(MONGO_URL)
        db = client[DB_NAME]
        await init_database(db)
        stats = await get_database_stats(db)
        print(f"\nEstadísticas: {stats}")
        client.close()
    
    asyncio.run(main())
