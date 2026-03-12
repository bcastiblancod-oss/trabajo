"""
Router de Habitaciones - Hotel Boutique
CRUD de habitaciones y consulta de disponibilidad (RF-01, RF-05)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone, date
from typing import Optional, List
import uuid

from models import (
    HabitacionCreate, HabitacionUpdate, HabitacionResponse,
    TipoHabitacionResponse, EstadoHabitacion, DisponibilidadQuery,
    DisponibilidadResponse
)
from utils import (
    get_current_user, require_roles, TokenPayload,
    date_to_str, str_to_date
)


router = APIRouter(prefix="/habitaciones", tags=["Habitaciones"])


async def get_habitacion_with_tipo(db, habitacion: dict) -> HabitacionResponse:
    """Helper to get room with type info"""
    tipo = await db.tipos_habitacion.find_one(
        {"id": habitacion["tipo_habitacion_id"]}, 
        {"_id": 0}
    )
    tipo_response = TipoHabitacionResponse(**tipo) if tipo else None
    
    return HabitacionResponse(
        id=habitacion["id"],
        numero=habitacion["numero"],
        piso=habitacion["piso"],
        tipo_habitacion_id=habitacion["tipo_habitacion_id"],
        tipo_habitacion=tipo_response,
        descripcion=habitacion.get("descripcion"),
        fotos=habitacion.get("fotos", []),
        estado=habitacion["estado"],
        precio_temporada_alta=habitacion.get("precio_temporada_alta"),
        precio_temporada_baja=habitacion.get("precio_temporada_baja"),
        created_at=datetime.fromisoformat(habitacion["created_at"]) if isinstance(habitacion["created_at"], str) else habitacion["created_at"]
    )


@router.get("", response_model=List[HabitacionResponse])
async def list_rooms(
    piso: Optional[int] = None,
    tipo_habitacion_id: Optional[str] = None,
    estado: Optional[EstadoHabitacion] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Listar habitaciones con filtros opcionales.
    Todos los usuarios autenticados pueden ver habitaciones.
    """
    from server import db
    
    # Build query
    query = {}
    if piso:
        query["piso"] = piso
    if tipo_habitacion_id:
        query["tipo_habitacion_id"] = tipo_habitacion_id
    if estado:
        query["estado"] = estado.value
    
    # Execute query
    cursor = db.habitaciones.find(query, {"_id": 0}).skip(skip).limit(limit).sort("numero", 1)
    rooms = await cursor.to_list(length=limit)
    
    result = []
    for room in rooms:
        result.append(await get_habitacion_with_tipo(db, room))
    
    return result


@router.get("/disponibilidad", response_model=DisponibilidadResponse)
async def check_availability(
    fecha_checkin: date,
    fecha_checkout: date,
    tipo_habitacion_id: Optional[str] = None,
    num_huespedes: Optional[int] = Query(None, ge=1),
    precio_min: Optional[float] = Query(None, ge=0),
    precio_max: Optional[float] = Query(None, ge=0),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    RF-01: Consulta de disponibilidad de habitaciones.
    Filtra por fechas, tipo, capacidad y precio.
    Retorna habitaciones disponibles para el rango de fechas.
    """
    from server import db
    
    # Validate dates
    if fecha_checkout <= fecha_checkin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de checkout debe ser posterior al checkin"
        )
    
    if fecha_checkin < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de checkin no puede ser anterior a hoy"
        )
    
    # Get all rooms that are not in maintenance or out of service
    room_query = {
        "estado": {"$nin": ["mantenimiento", "fuera_de_servicio"]}
    }
    if tipo_habitacion_id:
        room_query["tipo_habitacion_id"] = tipo_habitacion_id
    
    rooms = await db.habitaciones.find(room_query, {"_id": 0}).to_list(100)
    
    # Get reservations that overlap with the requested dates
    # A reservation overlaps if: existing_checkin < requested_checkout AND existing_checkout > requested_checkin
    reservations = await db.reservas.find({
        "estado": {"$in": ["pendiente", "confirmada", "checked_in"]},
        "fecha_checkin": {"$lt": fecha_checkout.isoformat()},
        "fecha_checkout": {"$gt": fecha_checkin.isoformat()}
    }, {"_id": 0, "habitacion_id": 1}).to_list(1000)
    
    reserved_room_ids = {r["habitacion_id"] for r in reservations}
    
    # Filter available rooms
    available_rooms = []
    for room in rooms:
        if room["id"] in reserved_room_ids:
            continue
        
        # Get room type for capacity and price check
        tipo = await db.tipos_habitacion.find_one(
            {"id": room["tipo_habitacion_id"]}, 
            {"_id": 0}
        )
        if not tipo:
            continue
        
        # Filter by capacity
        if num_huespedes and tipo["capacidad_maxima"] < num_huespedes:
            continue
        
        # Filter by price
        precio = tipo["precio_base"]
        if precio_min and precio < precio_min:
            continue
        if precio_max and precio > precio_max:
            continue
        
        available_rooms.append(await get_habitacion_with_tipo(db, room))
    
    return DisponibilidadResponse(
        habitaciones_disponibles=available_rooms,
        total=len(available_rooms),
        filtros_aplicados={
            "fecha_checkin": fecha_checkin.isoformat(),
            "fecha_checkout": fecha_checkout.isoformat(),
            "tipo_habitacion_id": tipo_habitacion_id,
            "num_huespedes": num_huespedes,
            "precio_min": precio_min,
            "precio_max": precio_max
        }
    )


@router.get("/tipos", response_model=List[TipoHabitacionResponse])
async def list_room_types(current_user: TokenPayload = Depends(get_current_user)):
    """Listar tipos de habitación disponibles"""
    from server import db
    
    tipos = await db.tipos_habitacion.find({}, {"_id": 0}).to_list(100)
    return [TipoHabitacionResponse(**t) for t in tipos]


@router.get("/{habitacion_id}", response_model=HabitacionResponse)
async def get_room(
    habitacion_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Obtener habitación por ID"""
    from server import db
    
    room = await db.habitaciones.find_one({"id": habitacion_id}, {"_id": 0})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    return await get_habitacion_with_tipo(db, room)


@router.post("", response_model=HabitacionResponse, status_code=status.HTTP_201_CREATED)
async def create_room(
    request: HabitacionCreate,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """RF-05: Crear nueva habitación (solo administradores)"""
    from server import db
    
    # Check if room number already exists
    existing = await db.habitaciones.find_one({"numero": request.numero})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una habitación con número {request.numero}"
        )
    
    # Verify room type exists
    tipo = await db.tipos_habitacion.find_one({"id": request.tipo_habitacion_id}, {"_id": 0})
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de habitación no encontrado"
        )
    
    # Create room
    room_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    room_doc = {
        "id": room_id,
        "numero": request.numero,
        "piso": request.piso,
        "tipo_habitacion_id": request.tipo_habitacion_id,
        "descripcion": request.descripcion,
        "fotos": request.fotos,
        "estado": "disponible",
        "precio_temporada_alta": request.precio_temporada_alta,
        "precio_temporada_baja": request.precio_temporada_baja,
        "created_at": now.isoformat(),
        "updated_at": None
    }
    
    await db.habitaciones.insert_one(room_doc)
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "crear_habitacion",
        "entidad": "habitaciones",
        "entidad_id": room_id,
        "detalles": {"numero": request.numero},
        "fecha": now.isoformat()
    })
    
    return await get_habitacion_with_tipo(db, room_doc)


@router.put("/{habitacion_id}", response_model=HabitacionResponse)
async def update_room(
    habitacion_id: str,
    request: HabitacionUpdate,
    current_user: TokenPayload = Depends(require_roles("administrador", "recepcionista"))
):
    """RF-05: Actualizar habitación"""
    from server import db
    
    # Get room
    room = await db.habitaciones.find_one({"id": habitacion_id}, {"_id": 0})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    # Build update
    update_data = {}
    if request.descripcion is not None:
        update_data["descripcion"] = request.descripcion
    if request.fotos is not None:
        update_data["fotos"] = request.fotos
    if request.precio_temporada_alta is not None:
        update_data["precio_temporada_alta"] = request.precio_temporada_alta
    if request.precio_temporada_baja is not None:
        update_data["precio_temporada_baja"] = request.precio_temporada_baja
    if request.estado is not None:
        update_data["estado"] = request.estado.value
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.habitaciones.update_one({"id": habitacion_id}, {"$set": update_data})
        
        # Log audit
        await db.logs_auditoria.insert_one({
            "id": str(uuid.uuid4()),
            "usuario_id": current_user.user_id,
            "accion": "actualizar_habitacion",
            "entidad": "habitaciones",
            "entidad_id": habitacion_id,
            "detalles": update_data,
            "fecha": datetime.now(timezone.utc).isoformat()
        })
    
    # Get updated room
    room = await db.habitaciones.find_one({"id": habitacion_id}, {"_id": 0})
    return await get_habitacion_with_tipo(db, room)


@router.delete("/{habitacion_id}")
async def delete_room(
    habitacion_id: str,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """
    RF-05: Eliminar habitación (solo administradores).
    No se permite si hay reservas activas.
    """
    from server import db
    
    # Get room
    room = await db.habitaciones.find_one({"id": habitacion_id}, {"_id": 0})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    # Check for active reservations
    active_reservations = await db.reservas.count_documents({
        "habitacion_id": habitacion_id,
        "estado": {"$in": ["pendiente", "confirmada", "checked_in"]}
    })
    
    if active_reservations > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar: hay {active_reservations} reserva(s) activa(s)"
        )
    
    # Delete room
    await db.habitaciones.delete_one({"id": habitacion_id})
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "eliminar_habitacion",
        "entidad": "habitaciones",
        "entidad_id": habitacion_id,
        "detalles": {"numero": room["numero"]},
        "fecha": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": f"Habitación {room['numero']} eliminada exitosamente"}
