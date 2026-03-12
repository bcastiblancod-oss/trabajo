"""
Router de Reservas - Hotel Boutique
CRUD de reservas, disponibilidad, cancelación (RF-02, RF-03, RF-04)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone, date
from typing import Optional, List
import uuid

from models import (
    ReservaCreate, ReservaUpdate, ReservaResponse, ReservaInDB,
    HabitacionResponse, TipoHabitacionResponse, ServicioReserva,
    EstadoReserva, CancelacionRequest, CancelacionResponse
)
from utils import (
    get_current_user, require_roles, TokenPayload,
    generate_reservation_code, calculate_nights,
    calculate_cancellation_refund, can_modify_reservation,
    validate_dates
)


router = APIRouter(prefix="/reservas", tags=["Reservas"])


async def get_reserva_with_details(db, reserva: dict) -> ReservaResponse:
    """Helper to get reservation with room details"""
    habitacion = await db.habitaciones.find_one(
        {"id": reserva["habitacion_id"]}, 
        {"_id": 0}
    )
    habitacion_response = None
    if habitacion:
        tipo = await db.tipos_habitacion.find_one(
            {"id": habitacion["tipo_habitacion_id"]}, 
            {"_id": 0}
        )
        habitacion_response = HabitacionResponse(
            id=habitacion["id"],
            numero=habitacion["numero"],
            piso=habitacion["piso"],
            tipo_habitacion_id=habitacion["tipo_habitacion_id"],
            tipo_habitacion=TipoHabitacionResponse(**tipo) if tipo else None,
            descripcion=habitacion.get("descripcion"),
            fotos=habitacion.get("fotos", []),
            estado=habitacion["estado"],
            precio_temporada_alta=habitacion.get("precio_temporada_alta"),
            precio_temporada_baja=habitacion.get("precio_temporada_baja"),
            created_at=datetime.fromisoformat(habitacion["created_at"]) if isinstance(habitacion["created_at"], str) else habitacion["created_at"]
        )
    
    return ReservaResponse(
        id=reserva["id"],
        codigo=reserva["codigo"],
        usuario_id=reserva["usuario_id"],
        habitacion_id=reserva["habitacion_id"],
        habitacion=habitacion_response,
        fecha_checkin=date.fromisoformat(reserva["fecha_checkin"]) if isinstance(reserva["fecha_checkin"], str) else reserva["fecha_checkin"],
        fecha_checkout=date.fromisoformat(reserva["fecha_checkout"]) if isinstance(reserva["fecha_checkout"], str) else reserva["fecha_checkout"],
        num_huespedes=reserva["num_huespedes"],
        huesped=reserva["huesped"],
        acompanantes=reserva.get("acompanantes", []),
        servicios_adicionales=reserva.get("servicios_adicionales", []),
        estado=reserva["estado"],
        precio_habitacion=reserva["precio_habitacion"],
        precio_servicios=reserva["precio_servicios"],
        precio_total=reserva["precio_total"],
        notas=reserva.get("notas"),
        metodo_pago=reserva["metodo_pago"],
        created_at=datetime.fromisoformat(reserva["created_at"]) if isinstance(reserva["created_at"], str) else reserva["created_at"],
        updated_at=datetime.fromisoformat(reserva["updated_at"]) if reserva.get("updated_at") and isinstance(reserva["updated_at"], str) else reserva.get("updated_at")
    )


@router.get("", response_model=List[ReservaResponse])
async def list_reservations(
    estado: Optional[EstadoReserva] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    habitacion_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    Listar reservas.
    - Huéspedes: solo sus propias reservas
    - Recepcionistas/Administradores: todas las reservas
    """
    from server import db
    
    # Build query
    query = {}
    
    # Guests can only see their own reservations
    if current_user.rol == "huesped":
        query["usuario_id"] = current_user.user_id
    
    if estado:
        query["estado"] = estado.value
    if habitacion_id:
        query["habitacion_id"] = habitacion_id
    if fecha_desde:
        query["fecha_checkin"] = {"$gte": fecha_desde.isoformat()}
    if fecha_hasta:
        if "fecha_checkin" in query:
            query["fecha_checkin"]["$lte"] = fecha_hasta.isoformat()
        else:
            query["fecha_checkin"] = {"$lte": fecha_hasta.isoformat()}
    
    # Execute query
    cursor = db.reservas.find(query, {"_id": 0}).skip(skip).limit(limit).sort("created_at", -1)
    reservations = await cursor.to_list(length=limit)
    
    result = []
    for res in reservations:
        result.append(await get_reserva_with_details(db, res))
    
    return result


@router.get("/buscar")
async def search_reservation(
    codigo: Optional[str] = None,
    documento: Optional[str] = None,
    nombre: Optional[str] = None,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """
    Buscar reserva por código, documento o nombre del huésped.
    Usado principalmente para check-in.
    """
    from server import db
    
    if not codigo and not documento and not nombre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos un criterio de búsqueda"
        )
    
    query = {"estado": {"$in": ["pendiente", "confirmada"]}}
    
    if codigo:
        query["codigo"] = codigo.upper()
    if documento:
        query["huesped.documento"] = documento
    if nombre:
        query["huesped.nombre_completo"] = {"$regex": nombre, "$options": "i"}
    
    reservations = await db.reservas.find(query, {"_id": 0}).to_list(10)
    
    result = []
    for res in reservations:
        result.append(await get_reserva_with_details(db, res))
    
    return result


@router.get("/{reserva_id}", response_model=ReservaResponse)
async def get_reservation(
    reserva_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Obtener reserva por ID"""
    from server import db
    
    reservation = await db.reservas.find_one({"id": reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Guests can only see their own reservations
    if current_user.rol == "huesped" and reservation["usuario_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a esta reserva"
        )
    
    return await get_reserva_with_details(db, reservation)


@router.post("", response_model=ReservaResponse, status_code=status.HTTP_201_CREATED)
async def create_reservation(
    request: ReservaCreate,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    RF-02: Crear nueva reserva.
    Genera código único y calcula precio total.
    """
    from server import db
    
    # Validate dates
    valid, msg = validate_dates(request.fecha_checkin, request.fecha_checkout)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Verify room exists and is available
    room = await db.habitaciones.find_one({"id": request.habitacion_id}, {"_id": 0})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    if room["estado"] in ["mantenimiento", "fuera_de_servicio"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Habitación no disponible (estado: {room['estado']})"
        )
    
    # Check room type capacity
    tipo = await db.tipos_habitacion.find_one({"id": room["tipo_habitacion_id"]}, {"_id": 0})
    if not tipo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de habitación no encontrado"
        )
    
    total_guests = request.num_huespedes
    if total_guests > tipo["capacidad_maxima"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La habitación tiene capacidad máxima de {tipo['capacidad_maxima']} huéspedes"
        )
    
    # Check for overlapping reservations
    overlapping = await db.reservas.find_one({
        "habitacion_id": request.habitacion_id,
        "estado": {"$in": ["pendiente", "confirmada", "checked_in"]},
        "fecha_checkin": {"$lt": request.fecha_checkout.isoformat()},
        "fecha_checkout": {"$gt": request.fecha_checkin.isoformat()}
    })
    
    if overlapping:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La habitación ya está reservada para las fechas seleccionadas"
        )
    
    # Calculate prices
    nights = calculate_nights(request.fecha_checkin, request.fecha_checkout)
    precio_habitacion = tipo["precio_base"] * nights
    
    # Process additional services
    servicios_reserva = []
    precio_servicios = 0.0
    
    for servicio_id in request.servicios_adicionales:
        servicio = await db.servicios_adicionales.find_one({"id": servicio_id}, {"_id": 0})
        if servicio and servicio["precio"] > 0:
            subtotal = servicio["precio"] * nights
            servicios_reserva.append(ServicioReserva(
                servicio_id=servicio_id,
                cantidad=nights,
                precio_unitario=servicio["precio"],
                subtotal=subtotal
            ).model_dump())
            precio_servicios += subtotal
    
    precio_total = precio_habitacion + precio_servicios
    
    # Create reservation
    reserva_id = str(uuid.uuid4())
    codigo = generate_reservation_code()
    now = datetime.now(timezone.utc)
    
    reserva_doc = {
        "id": reserva_id,
        "codigo": codigo,
        "usuario_id": current_user.user_id,
        "habitacion_id": request.habitacion_id,
        "fecha_checkin": request.fecha_checkin.isoformat(),
        "fecha_checkout": request.fecha_checkout.isoformat(),
        "num_huespedes": request.num_huespedes,
        "huesped": request.huesped.model_dump(),
        "acompanantes": [a.model_dump() for a in request.acompanantes],
        "servicios_adicionales": servicios_reserva,
        "estado": "confirmada",
        "precio_habitacion": precio_habitacion,
        "precio_servicios": precio_servicios,
        "precio_total": precio_total,
        "notas": request.notas,
        "metodo_pago": request.metodo_pago.value,
        "created_at": now.isoformat(),
        "updated_at": None,
        "cancelada_at": None,
        "motivo_cancelacion": None,
        "monto_reembolso": None
    }
    
    await db.reservas.insert_one(reserva_doc)
    
    # Update room state to reserved
    await db.habitaciones.update_one(
        {"id": request.habitacion_id},
        {"$set": {"estado": "reservada", "updated_at": now.isoformat()}}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "crear_reserva",
        "entidad": "reservas",
        "entidad_id": reserva_id,
        "detalles": {
            "codigo": codigo,
            "habitacion": room["numero"],
            "fechas": f"{request.fecha_checkin} - {request.fecha_checkout}",
            "total": precio_total
        },
        "fecha": now.isoformat()
    })
    
    return await get_reserva_with_details(db, reserva_doc)


@router.put("/{reserva_id}", response_model=ReservaResponse)
async def update_reservation(
    reserva_id: str,
    request: ReservaUpdate,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    RF-03: Modificar reserva.
    Solo permitido con al menos 24h de anticipación al check-in.
    """
    from server import db
    
    # Get reservation
    reservation = await db.reservas.find_one({"id": reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Check permissions
    if current_user.rol == "huesped" and reservation["usuario_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a esta reserva"
        )
    
    # Check reservation state
    if reservation["estado"] not in ["pendiente", "confirmada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede modificar una reserva en estado '{reservation['estado']}'"
        )
    
    # Check modification time limit
    current_checkin = date.fromisoformat(reservation["fecha_checkin"]) if isinstance(reservation["fecha_checkin"], str) else reservation["fecha_checkin"]
    can_modify, msg = can_modify_reservation(current_checkin)
    if not can_modify:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )
    
    # Build update
    update_data = {}
    recalculate_price = False
    new_habitacion_id = reservation["habitacion_id"]
    new_checkin = current_checkin
    new_checkout = date.fromisoformat(reservation["fecha_checkout"]) if isinstance(reservation["fecha_checkout"], str) else reservation["fecha_checkout"]
    
    if request.fecha_checkin is not None or request.fecha_checkout is not None:
        new_checkin = request.fecha_checkin or current_checkin
        new_checkout = request.fecha_checkout or new_checkout
        
        valid, msg = validate_dates(new_checkin, new_checkout)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=msg
            )
        
        update_data["fecha_checkin"] = new_checkin.isoformat()
        update_data["fecha_checkout"] = new_checkout.isoformat()
        recalculate_price = True
    
    if request.habitacion_id is not None and request.habitacion_id != reservation["habitacion_id"]:
        # Verify new room
        new_room = await db.habitaciones.find_one({"id": request.habitacion_id}, {"_id": 0})
        if not new_room:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nueva habitación no encontrada"
            )
        
        # Check availability
        overlapping = await db.reservas.find_one({
            "habitacion_id": request.habitacion_id,
            "id": {"$ne": reserva_id},
            "estado": {"$in": ["pendiente", "confirmada", "checked_in"]},
            "fecha_checkin": {"$lt": new_checkout.isoformat()},
            "fecha_checkout": {"$gt": new_checkin.isoformat()}
        })
        
        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La nueva habitación no está disponible para las fechas"
            )
        
        update_data["habitacion_id"] = request.habitacion_id
        new_habitacion_id = request.habitacion_id
        recalculate_price = True
        
        # Update old room state
        await db.habitaciones.update_one(
            {"id": reservation["habitacion_id"]},
            {"$set": {"estado": "disponible", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        # Update new room state
        await db.habitaciones.update_one(
            {"id": request.habitacion_id},
            {"$set": {"estado": "reservada", "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    if request.servicios_adicionales is not None:
        recalculate_price = True
    
    if request.notas is not None:
        update_data["notas"] = request.notas
    
    # Recalculate price if needed
    if recalculate_price:
        room = await db.habitaciones.find_one({"id": new_habitacion_id}, {"_id": 0})
        tipo = await db.tipos_habitacion.find_one({"id": room["tipo_habitacion_id"]}, {"_id": 0})
        
        nights = calculate_nights(new_checkin, new_checkout)
        precio_habitacion = tipo["precio_base"] * nights
        
        servicios_ids = request.servicios_adicionales if request.servicios_adicionales is not None else [s["servicio_id"] for s in reservation.get("servicios_adicionales", [])]
        servicios_reserva = []
        precio_servicios = 0.0
        
        for servicio_id in servicios_ids:
            servicio = await db.servicios_adicionales.find_one({"id": servicio_id}, {"_id": 0})
            if servicio and servicio["precio"] > 0:
                subtotal = servicio["precio"] * nights
                servicios_reserva.append({
                    "servicio_id": servicio_id,
                    "cantidad": nights,
                    "precio_unitario": servicio["precio"],
                    "subtotal": subtotal
                })
                precio_servicios += subtotal
        
        update_data["precio_habitacion"] = precio_habitacion
        update_data["precio_servicios"] = precio_servicios
        update_data["precio_total"] = precio_habitacion + precio_servicios
        update_data["servicios_adicionales"] = servicios_reserva
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.reservas.update_one({"id": reserva_id}, {"$set": update_data})
        
        # Log audit
        await db.logs_auditoria.insert_one({
            "id": str(uuid.uuid4()),
            "usuario_id": current_user.user_id,
            "accion": "modificar_reserva",
            "entidad": "reservas",
            "entidad_id": reserva_id,
            "detalles": update_data,
            "fecha": datetime.now(timezone.utc).isoformat()
        })
    
    # Get updated reservation
    reservation = await db.reservas.find_one({"id": reserva_id}, {"_id": 0})
    return await get_reserva_with_details(db, reservation)


@router.post("/{reserva_id}/cancelar", response_model=CancelacionResponse)
async def cancel_reservation(
    reserva_id: str,
    request: CancelacionRequest,
    current_user: TokenPayload = Depends(get_current_user)
):
    """
    RF-04: Cancelar reserva con política de reembolsos.
    - >48h: 100% reembolso
    - 24-48h: 50% reembolso
    - <24h: 0% reembolso
    """
    from server import db
    
    # Get reservation
    reservation = await db.reservas.find_one({"id": reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Check permissions
    if current_user.rol == "huesped" and reservation["usuario_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a esta reserva"
        )
    
    # Check reservation state
    if reservation["estado"] not in ["pendiente", "confirmada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede cancelar una reserva en estado '{reservation['estado']}'"
        )
    
    # Calculate refund
    checkin_date = date.fromisoformat(reservation["fecha_checkin"]) if isinstance(reservation["fecha_checkin"], str) else reservation["fecha_checkin"]
    monto_reembolso, porcentaje, politica = calculate_cancellation_refund(
        checkin_date, 
        reservation["precio_total"]
    )
    
    # Update reservation
    now = datetime.now(timezone.utc)
    await db.reservas.update_one(
        {"id": reserva_id},
        {"$set": {
            "estado": "cancelada",
            "cancelada_at": now.isoformat(),
            "motivo_cancelacion": request.motivo,
            "monto_reembolso": monto_reembolso,
            "updated_at": now.isoformat()
        }}
    )
    
    # Update room state
    await db.habitaciones.update_one(
        {"id": reservation["habitacion_id"]},
        {"$set": {"estado": "disponible", "updated_at": now.isoformat()}}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "cancelar_reserva",
        "entidad": "reservas",
        "entidad_id": reserva_id,
        "detalles": {
            "codigo": reservation["codigo"],
            "motivo": request.motivo,
            "reembolso": monto_reembolso,
            "porcentaje": porcentaje
        },
        "fecha": now.isoformat()
    })
    
    return CancelacionResponse(
        reserva_id=reserva_id,
        codigo=reservation["codigo"],
        estado_anterior=reservation["estado"],
        estado_nuevo="cancelada",
        politica_aplicada=politica,
        monto_original=reservation["precio_total"],
        monto_reembolso=monto_reembolso,
        porcentaje_reembolso=porcentaje,
        mensaje=f"Reserva cancelada. Reembolso: ${monto_reembolso:,.0f} ({porcentaje}%)"
    )
