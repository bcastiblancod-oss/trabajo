"""
Router de Check-in / Check-out - Hotel Boutique
Procesos de entrada y salida de huéspedes (RF-06, RF-07, RF-08)
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone, date
from typing import Optional, List
import uuid

from models import (
    CheckInRequest, CheckInResponse, CheckInInDB,
    CheckOutRequest, CheckOutResponse, CheckOutInDB,
    ConsumoCreate, ConsumoResponse, ConsumoInDB,
    HabitacionResponse, TipoHabitacionResponse, ReservaResponse,
    ItemFactura, FacturaInDB
)
from utils import (
    get_current_user, require_roles, TokenPayload,
    generate_invoice_number
)


router = APIRouter(tags=["Check-in / Check-out"])


# ============== CHECK-IN ==============
@router.post("/checkin", response_model=CheckInResponse)
async def process_checkin(
    request: CheckInRequest,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """
    RF-06: Proceso de check-in.
    Busca reserva y actualiza estado a 'checked_in'.
    """
    from server import db
    
    # Find reservation
    reservation = None
    
    if request.reserva_id:
        reservation = await db.reservas.find_one({"id": request.reserva_id}, {"_id": 0})
    elif request.codigo_reserva:
        reservation = await db.reservas.find_one({"codigo": request.codigo_reserva.upper()}, {"_id": 0})
    elif request.documento_huesped:
        reservation = await db.reservas.find_one({
            "huesped.documento": request.documento_huesped,
            "estado": {"$in": ["pendiente", "confirmada"]}
        }, {"_id": 0})
    elif request.nombre_huesped:
        reservation = await db.reservas.find_one({
            "huesped.nombre_completo": {"$regex": request.nombre_huesped, "$options": "i"},
            "estado": {"$in": ["pendiente", "confirmada"]}
        }, {"_id": 0})
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Check reservation state
    if reservation["estado"] not in ["pendiente", "confirmada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede hacer check-in a una reserva en estado '{reservation['estado']}'"
        )
    
    # Check date
    checkin_date = date.fromisoformat(reservation["fecha_checkin"]) if isinstance(reservation["fecha_checkin"], str) else reservation["fecha_checkin"]
    today = date.today()
    
    if checkin_date > today:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El check-in está programado para {checkin_date}, no puede hacerse antes"
        )
    
    # Determine room to assign
    habitacion_id = request.habitacion_asignada or reservation["habitacion_id"]
    
    # Verify room is available
    room = await db.habitaciones.find_one({"id": habitacion_id}, {"_id": 0})
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habitación no encontrada"
        )
    
    if room["estado"] == "ocupada":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La habitación está ocupada"
        )
    
    # Create check-in record
    now = datetime.now(timezone.utc)
    checkin_id = str(uuid.uuid4())
    
    checkin_doc = {
        "id": checkin_id,
        "reserva_id": reservation["id"],
        "habitacion_id": habitacion_id,
        "fecha_hora_checkin": now.isoformat(),
        "realizado_por": current_user.user_id,
        "notas": None
    }
    
    await db.checkins.insert_one(checkin_doc)
    
    # Update reservation
    await db.reservas.update_one(
        {"id": reservation["id"]},
        {"$set": {
            "estado": "checked_in",
            "habitacion_id": habitacion_id,
            "updated_at": now.isoformat()
        }}
    )
    
    # Update room state
    await db.habitaciones.update_one(
        {"id": habitacion_id},
        {"$set": {"estado": "ocupada", "updated_at": now.isoformat()}}
    )
    
    # If room changed, free old room
    if habitacion_id != reservation["habitacion_id"]:
        await db.habitaciones.update_one(
            {"id": reservation["habitacion_id"]},
            {"$set": {"estado": "disponible", "updated_at": now.isoformat()}}
        )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "checkin",
        "entidad": "reservas",
        "entidad_id": reservation["id"],
        "detalles": {
            "codigo": reservation["codigo"],
            "habitacion": room["numero"]
        },
        "fecha": now.isoformat()
    })
    
    # Build response
    # Get room with type
    tipo = await db.tipos_habitacion.find_one({"id": room["tipo_habitacion_id"]}, {"_id": 0})
    room["estado"] = "ocupada"
    
    habitacion_response = HabitacionResponse(
        id=room["id"],
        numero=room["numero"],
        piso=room["piso"],
        tipo_habitacion_id=room["tipo_habitacion_id"],
        tipo_habitacion=TipoHabitacionResponse(**tipo) if tipo else None,
        descripcion=room.get("descripcion"),
        fotos=room.get("fotos", []),
        estado=room["estado"],
        precio_temporada_alta=room.get("precio_temporada_alta"),
        precio_temporada_baja=room.get("precio_temporada_baja"),
        created_at=datetime.fromisoformat(room["created_at"]) if isinstance(room["created_at"], str) else room["created_at"]
    )
    
    # Get updated reservation
    reservation = await db.reservas.find_one({"id": reservation["id"]}, {"_id": 0})
    reserva_response = ReservaResponse(
        id=reservation["id"],
        codigo=reservation["codigo"],
        usuario_id=reservation["usuario_id"],
        habitacion_id=reservation["habitacion_id"],
        habitacion=habitacion_response,
        fecha_checkin=date.fromisoformat(reservation["fecha_checkin"]) if isinstance(reservation["fecha_checkin"], str) else reservation["fecha_checkin"],
        fecha_checkout=date.fromisoformat(reservation["fecha_checkout"]) if isinstance(reservation["fecha_checkout"], str) else reservation["fecha_checkout"],
        num_huespedes=reservation["num_huespedes"],
        huesped=reservation["huesped"],
        acompanantes=reservation.get("acompanantes", []),
        servicios_adicionales=reservation.get("servicios_adicionales", []),
        estado=reservation["estado"],
        precio_habitacion=reservation["precio_habitacion"],
        precio_servicios=reservation["precio_servicios"],
        precio_total=reservation["precio_total"],
        notas=reservation.get("notas"),
        metodo_pago=reservation["metodo_pago"],
        created_at=datetime.fromisoformat(reservation["created_at"]) if isinstance(reservation["created_at"], str) else reservation["created_at"]
    )
    
    return CheckInResponse(
        id=checkin_id,
        reserva_id=reservation["id"],
        reserva=reserva_response,
        habitacion_id=habitacion_id,
        habitacion=habitacion_response,
        fecha_hora_checkin=now,
        realizado_por=current_user.user_id
    )


# ============== CONSUMOS ==============
@router.post("/consumos", response_model=ConsumoResponse, status_code=status.HTTP_201_CREATED)
async def add_consumption(
    request: ConsumoCreate,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """Registrar consumo (minibar, lavandería, etc.) a una reserva"""
    from server import db
    
    # Verify reservation exists and is checked in
    reservation = await db.reservas.find_one({"id": request.reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if reservation["estado"] != "checked_in":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden registrar consumos a reservas con check-in"
        )
    
    # Create consumption
    now = datetime.now(timezone.utc)
    consumo_id = str(uuid.uuid4())
    subtotal = request.cantidad * request.precio_unitario
    
    consumo_doc = {
        "id": consumo_id,
        "reserva_id": request.reserva_id,
        "descripcion": request.descripcion,
        "cantidad": request.cantidad,
        "precio_unitario": request.precio_unitario,
        "subtotal": subtotal,
        "categoria": request.categoria,
        "fecha": now.isoformat(),
        "registrado_por": current_user.user_id
    }
    
    await db.consumos.insert_one(consumo_doc)
    
    return ConsumoResponse(
        id=consumo_id,
        reserva_id=request.reserva_id,
        descripcion=request.descripcion,
        cantidad=request.cantidad,
        precio_unitario=request.precio_unitario,
        subtotal=subtotal,
        categoria=request.categoria,
        fecha=now
    )


@router.get("/consumos/{reserva_id}", response_model=List[ConsumoResponse])
async def get_consumptions(
    reserva_id: str,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """Obtener consumos de una reserva"""
    from server import db
    
    consumos = await db.consumos.find({"reserva_id": reserva_id}, {"_id": 0}).to_list(100)
    
    return [
        ConsumoResponse(
            id=c["id"],
            reserva_id=c["reserva_id"],
            descripcion=c["descripcion"],
            cantidad=c["cantidad"],
            precio_unitario=c["precio_unitario"],
            subtotal=c["subtotal"],
            categoria=c["categoria"],
            fecha=datetime.fromisoformat(c["fecha"]) if isinstance(c["fecha"], str) else c["fecha"]
        )
        for c in consumos
    ]


# ============== CHECK-OUT ==============
@router.post("/checkout", response_model=CheckOutResponse)
async def process_checkout(
    request: CheckOutRequest,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """
    RF-07: Proceso de check-out.
    Genera resumen de consumos, factura y actualiza estados.
    """
    from server import db
    
    # Get reservation
    reservation = await db.reservas.find_one({"id": request.reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if reservation["estado"] != "checked_in":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede hacer check-out a una reserva en estado '{reservation['estado']}'"
        )
    
    # Get consumptions
    consumos = await db.consumos.find({"reserva_id": request.reserva_id}, {"_id": 0}).to_list(100)
    subtotal_consumos = sum(c["subtotal"] for c in consumos)
    
    # Calculate totals
    subtotal_habitacion = reservation["precio_habitacion"]
    subtotal_servicios = reservation["precio_servicios"]
    subtotal = subtotal_habitacion + subtotal_servicios + subtotal_consumos
    impuestos = subtotal * 0.19  # IVA 19%
    total = subtotal + impuestos
    
    now = datetime.now(timezone.utc)
    checkout_id = str(uuid.uuid4())
    
    # Create checkout record
    checkout_doc = {
        "id": checkout_id,
        "reserva_id": request.reserva_id,
        "subtotal_habitacion": subtotal_habitacion,
        "subtotal_servicios": subtotal_servicios,
        "subtotal_consumos": subtotal_consumos,
        "impuestos": impuestos,
        "total": total,
        "fecha_hora_checkout": now.isoformat(),
        "realizado_por": current_user.user_id,
        "notas": request.notas
    }
    
    await db.checkouts.insert_one(checkout_doc)
    
    # Create invoice
    factura_id = str(uuid.uuid4())
    factura_numero = generate_invoice_number()
    
    # Build invoice items
    items = [
        ItemFactura(
            descripcion=f"Alojamiento - Habitación {reservation['habitacion_id'][-4:]}",
            cantidad=1,
            precio_unitario=subtotal_habitacion,
            subtotal=subtotal_habitacion
        ).model_dump()
    ]
    
    if subtotal_servicios > 0:
        items.append(ItemFactura(
            descripcion="Servicios adicionales",
            cantidad=1,
            precio_unitario=subtotal_servicios,
            subtotal=subtotal_servicios
        ).model_dump())
    
    for consumo in consumos:
        items.append(ItemFactura(
            descripcion=f"{consumo['categoria']}: {consumo['descripcion']}",
            cantidad=consumo["cantidad"],
            precio_unitario=consumo["precio_unitario"],
            subtotal=consumo["subtotal"]
        ).model_dump())
    
    factura_doc = {
        "id": factura_id,
        "numero": factura_numero,
        "reserva_id": request.reserva_id,
        "checkout_id": checkout_id,
        "huesped": reservation["huesped"],
        "items": items,
        "subtotal": subtotal,
        "impuestos": impuestos,
        "descuentos": 0,
        "total": total,
        "fecha_emision": now.isoformat(),
        "estado": "emitida"
    }
    
    await db.facturas.insert_one(factura_doc)
    
    # Update reservation
    await db.reservas.update_one(
        {"id": request.reserva_id},
        {"$set": {
            "estado": "checked_out",
            "updated_at": now.isoformat()
        }}
    )
    
    # Update room state
    await db.habitaciones.update_one(
        {"id": reservation["habitacion_id"]},
        {"$set": {"estado": "para_limpieza", "updated_at": now.isoformat()}}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "checkout",
        "entidad": "reservas",
        "entidad_id": request.reserva_id,
        "detalles": {
            "codigo": reservation["codigo"],
            "factura": factura_numero,
            "total": total
        },
        "fecha": now.isoformat()
    })
    
    # Build response
    room = await db.habitaciones.find_one({"id": reservation["habitacion_id"]}, {"_id": 0})
    tipo = await db.tipos_habitacion.find_one({"id": room["tipo_habitacion_id"]}, {"_id": 0})
    
    habitacion_response = HabitacionResponse(
        id=room["id"],
        numero=room["numero"],
        piso=room["piso"],
        tipo_habitacion_id=room["tipo_habitacion_id"],
        tipo_habitacion=TipoHabitacionResponse(**tipo) if tipo else None,
        descripcion=room.get("descripcion"),
        fotos=room.get("fotos", []),
        estado="para_limpieza",
        precio_temporada_alta=room.get("precio_temporada_alta"),
        precio_temporada_baja=room.get("precio_temporada_baja"),
        created_at=datetime.fromisoformat(room["created_at"]) if isinstance(room["created_at"], str) else room["created_at"]
    )
    
    # Get updated reservation
    reservation = await db.reservas.find_one({"id": request.reserva_id}, {"_id": 0})
    reserva_response = ReservaResponse(
        id=reservation["id"],
        codigo=reservation["codigo"],
        usuario_id=reservation["usuario_id"],
        habitacion_id=reservation["habitacion_id"],
        habitacion=habitacion_response,
        fecha_checkin=date.fromisoformat(reservation["fecha_checkin"]) if isinstance(reservation["fecha_checkin"], str) else reservation["fecha_checkin"],
        fecha_checkout=date.fromisoformat(reservation["fecha_checkout"]) if isinstance(reservation["fecha_checkout"], str) else reservation["fecha_checkout"],
        num_huespedes=reservation["num_huespedes"],
        huesped=reservation["huesped"],
        acompanantes=reservation.get("acompanantes", []),
        servicios_adicionales=reservation.get("servicios_adicionales", []),
        estado=reservation["estado"],
        precio_habitacion=reservation["precio_habitacion"],
        precio_servicios=reservation["precio_servicios"],
        precio_total=reservation["precio_total"],
        notas=reservation.get("notas"),
        metodo_pago=reservation["metodo_pago"],
        created_at=datetime.fromisoformat(reservation["created_at"]) if isinstance(reservation["created_at"], str) else reservation["created_at"]
    )
    
    consumos_response = [
        ConsumoResponse(
            id=c["id"],
            reserva_id=c["reserva_id"],
            descripcion=c["descripcion"],
            cantidad=c["cantidad"],
            precio_unitario=c["precio_unitario"],
            subtotal=c["subtotal"],
            categoria=c["categoria"],
            fecha=datetime.fromisoformat(c["fecha"]) if isinstance(c["fecha"], str) else c["fecha"]
        )
        for c in consumos
    ]
    
    return CheckOutResponse(
        id=checkout_id,
        reserva_id=request.reserva_id,
        reserva=reserva_response,
        consumos=consumos_response,
        subtotal_habitacion=subtotal_habitacion,
        subtotal_servicios=subtotal_servicios,
        subtotal_consumos=subtotal_consumos,
        impuestos=impuestos,
        total=total,
        fecha_hora_checkout=now,
        realizado_por=current_user.user_id,
        factura_id=factura_id
    )


# ============== PRE CHECK-IN ==============
@router.get("/precheckin/{codigo_reserva}")
async def get_precheckin_info(codigo_reserva: str):
    """
    RF-08: Obtener información para pre check-in online.
    No requiere autenticación (acceso público con código).
    """
    from server import db
    
    reservation = await db.reservas.find_one(
        {"codigo": codigo_reserva.upper()},
        {"_id": 0, "usuario_id": 0}
    )
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if reservation["estado"] not in ["pendiente", "confirmada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta reserva no está disponible para pre check-in"
        )
    
    # Get room info
    room = await db.habitaciones.find_one({"id": reservation["habitacion_id"]}, {"_id": 0})
    tipo = await db.tipos_habitacion.find_one({"id": room["tipo_habitacion_id"]}, {"_id": 0})
    
    return {
        "codigo": reservation["codigo"],
        "huesped": reservation["huesped"],
        "acompanantes": reservation.get("acompanantes", []),
        "fecha_checkin": reservation["fecha_checkin"],
        "fecha_checkout": reservation["fecha_checkout"],
        "habitacion": {
            "numero": room["numero"],
            "tipo": tipo["nombre"],
            "piso": room["piso"]
        },
        "servicios_adicionales": reservation.get("servicios_adicionales", []),
        "precio_total": reservation["precio_total"],
        "estado": reservation["estado"]
    }


@router.put("/precheckin/{codigo_reserva}")
async def update_precheckin(
    codigo_reserva: str,
    hora_llegada: Optional[str] = None,
    notas: Optional[str] = None
):
    """
    RF-08: Actualizar información de pre check-in.
    Permite al huésped indicar hora estimada de llegada.
    """
    from server import db
    
    reservation = await db.reservas.find_one(
        {"codigo": codigo_reserva.upper()},
        {"_id": 0}
    )
    
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    if reservation["estado"] not in ["pendiente", "confirmada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta reserva no está disponible para pre check-in"
        )
    
    # Update
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if hora_llegada:
        update_data["hora_llegada_estimada"] = hora_llegada
    if notas:
        update_data["notas_precheckin"] = notas
    
    await db.reservas.update_one(
        {"codigo": codigo_reserva.upper()},
        {"$set": update_data}
    )
    
    return {"message": "Pre check-in actualizado exitosamente"}
