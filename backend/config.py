"""
Configuración del sistema de gestión de reservas - Hotel Boutique
"""
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'hotel_boutique')

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'hotel_boutique_secret_key_2024_secure')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# CORS
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')

# Business Rules
CANCELLATION_POLICIES = {
    "full_refund_hours": 48,      # >48h = 100% reembolso
    "partial_refund_hours": 24,   # 24-48h = 50% reembolso
    "no_refund_hours": 24         # <24h = 0% reembolso
}

MODIFICATION_MIN_HOURS = 24  # Mínimo 24h para modificar reserva

# Room States
ROOM_STATES = [
    "disponible",
    "reservada",
    "ocupada",
    "mantenimiento",
    "fuera_de_servicio",
    "para_limpieza"
]

# Reservation States
RESERVATION_STATES = [
    "pendiente",
    "confirmada",
    "checked_in",
    "checked_out",
    "cancelada",
    "no_show"
]

# User Roles
USER_ROLES = [
    "huesped",
    "recepcionista",
    "administrador"
]

# Room Types Configuration
ROOM_TYPES_CONFIG = [
    {
        "codigo": "EST",
        "nombre": "Estándar",
        "descripcion": "Habitación estándar con cama doble o dos camas sencillas",
        "capacidad_maxima": 2,
        "precio_base": 150000,
        "amenidades": ["WiFi", "TV", "Aire acondicionado", "Baño privado"]
    },
    {
        "codigo": "SUI",
        "nombre": "Suite",
        "descripcion": "Suite con sala de estar, cama king y jacuzzi",
        "capacidad_maxima": 2,
        "precio_base": 350000,
        "amenidades": ["WiFi", "TV 55\"", "Aire acondicionado", "Jacuzzi", "Minibar", "Sala de estar"]
    },
    {
        "codigo": "FAM",
        "nombre": "Familiar",
        "descripcion": "Habitación familiar con cama king y dos camas sencillas",
        "capacidad_maxima": 4,
        "precio_base": 280000,
        "amenidades": ["WiFi", "TV", "Aire acondicionado", "Baño privado", "Sofá cama"]
    }
]

# 24 Rooms Configuration
ROOMS_CONFIG = [
    # Piso 1 - Habitaciones Estándar (101-108)
    {"numero": "101", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "102", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "103", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "104", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "105", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "106", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "107", "piso": 1, "tipo_codigo": "EST"},
    {"numero": "108", "piso": 1, "tipo_codigo": "EST"},
    # Piso 2 - Habitaciones Estándar y Familiares (201-208)
    {"numero": "201", "piso": 2, "tipo_codigo": "EST"},
    {"numero": "202", "piso": 2, "tipo_codigo": "EST"},
    {"numero": "203", "piso": 2, "tipo_codigo": "FAM"},
    {"numero": "204", "piso": 2, "tipo_codigo": "FAM"},
    {"numero": "205", "piso": 2, "tipo_codigo": "FAM"},
    {"numero": "206", "piso": 2, "tipo_codigo": "FAM"},
    {"numero": "207", "piso": 2, "tipo_codigo": "EST"},
    {"numero": "208", "piso": 2, "tipo_codigo": "EST"},
    # Piso 3 - Suites (301-308)
    {"numero": "301", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "302", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "303", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "304", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "305", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "306", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "307", "piso": 3, "tipo_codigo": "SUI"},
    {"numero": "308", "piso": 3, "tipo_codigo": "SUI"},
]

# Additional Services
ADDITIONAL_SERVICES = [
    {"codigo": "DESAYUNO", "nombre": "Desayuno Buffet", "precio": 35000, "descripcion": "Desayuno buffet completo"},
    {"codigo": "PARKING", "nombre": "Parqueadero", "precio": 25000, "descripcion": "Parqueadero por noche"},
    {"codigo": "SPA", "nombre": "Acceso Spa", "precio": 80000, "descripcion": "Acceso completo al spa"},
    {"codigo": "TRANSFER", "nombre": "Transfer Aeropuerto", "precio": 60000, "descripcion": "Traslado aeropuerto-hotel"},
    {"codigo": "MINIBAR", "nombre": "Minibar", "precio": 0, "descripcion": "Consumo de minibar (variable)"},
    {"codigo": "LAVANDERIA", "nombre": "Lavandería", "precio": 0, "descripcion": "Servicio de lavandería (variable)"},
]
