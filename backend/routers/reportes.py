"""
Router de Reportes - Hotel Boutique
Reportes de ocupación e ingresos (RF-13)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone, date, timedelta
from typing import Optional

from models import ReporteOcupacion
from utils import (
    get_current_user, require_roles, TokenPayload
)


router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/ocupacion", response_model=ReporteOcupacion)
async def get_occupancy_report(
    fecha_inicio: date,
    fecha_fin: date,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """
    RF-13: Reporte de ocupación e ingresos.
    Calcula tasa de ocupación, ingresos y estadísticas del período.
    """
    from server import db
    
    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de fin debe ser posterior a la fecha de inicio"
        )
    
    # Total rooms
    total_habitaciones = await db.habitaciones.count_documents({})
    
    # Get reservations in the period
    reservations = await db.reservas.find({
        "fecha_checkin": {"$lte": fecha_fin.isoformat()},
        "fecha_checkout": {"$gte": fecha_inicio.isoformat()},
        "estado": {"$in": ["confirmada", "checked_in", "checked_out"]}
    }, {"_id": 0}).to_list(10000)
    
    # Calculate occupied room-nights
    total_days = (fecha_fin - fecha_inicio).days + 1
    total_room_nights = total_habitaciones * total_days
    
    occupied_room_nights = 0
    total_revenue = 0
    total_stay_nights = 0
    
    for res in reservations:
        checkin = date.fromisoformat(res["fecha_checkin"]) if isinstance(res["fecha_checkin"], str) else res["fecha_checkin"]
        checkout = date.fromisoformat(res["fecha_checkout"]) if isinstance(res["fecha_checkout"], str) else res["fecha_checkout"]
        
        # Calculate overlap with report period
        overlap_start = max(checkin, fecha_inicio)
        overlap_end = min(checkout, fecha_fin)
        
        if overlap_start < overlap_end:
            nights = (overlap_end - overlap_start).days
            occupied_room_nights += nights
            
            # Prorate revenue
            total_nights = (checkout - checkin).days
            if total_nights > 0:
                daily_rate = res["precio_total"] / total_nights
                total_revenue += daily_rate * nights
            
            total_stay_nights += nights
    
    # Calculate occupancy rate
    tasa_ocupacion = (occupied_room_nights / total_room_nights * 100) if total_room_nights > 0 else 0
    
    # Count reservations and cancellations
    reservas_realizadas = len([r for r in reservations if r["estado"] in ["confirmada", "checked_in", "checked_out"]])
    
    cancelaciones = await db.reservas.count_documents({
        "estado": "cancelada",
        "cancelada_at": {
            "$gte": fecha_inicio.isoformat(),
            "$lte": fecha_fin.isoformat()
        }
    })
    
    # Average stay length
    promedio_estancia = (total_stay_nights / reservas_realizadas) if reservas_realizadas > 0 else 0
    
    return ReporteOcupacion(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        total_habitaciones=total_habitaciones,
        habitaciones_ocupadas=occupied_room_nights,
        tasa_ocupacion=round(tasa_ocupacion, 2),
        ingresos_totales=round(total_revenue, 2),
        reservas_realizadas=reservas_realizadas,
        reservas_canceladas=cancelaciones,
        promedio_estancia=round(promedio_estancia, 2)
    )


@router.get("/dashboard")
async def get_dashboard(
    current_user: TokenPayload = Depends(require_roles("administrador", "recepcionista"))
):
    """Dashboard con indicadores principales para hoy"""
    from server import db
    
    today = date.today()
    today_str = today.isoformat()
    
    # Room statistics
    total_rooms = await db.habitaciones.count_documents({})
    occupied = await db.habitaciones.count_documents({"estado": "ocupada"})
    available = await db.habitaciones.count_documents({"estado": "disponible"})
    maintenance = await db.habitaciones.count_documents({"estado": {"$in": ["mantenimiento", "fuera_de_servicio"]}})
    cleaning = await db.habitaciones.count_documents({"estado": "para_limpieza"})
    
    # Today's check-ins and check-outs
    checkins_hoy = await db.reservas.count_documents({
        "fecha_checkin": today_str,
        "estado": {"$in": ["pendiente", "confirmada"]}
    })
    
    checkouts_hoy = await db.reservas.count_documents({
        "fecha_checkout": today_str,
        "estado": "checked_in"
    })
    
    # Active reservations
    reservas_activas = await db.reservas.count_documents({
        "estado": {"$in": ["pendiente", "confirmada", "checked_in"]}
    })
    
    # Today's revenue (from checkouts)
    today_checkouts = await db.checkouts.find({
        "fecha_hora_checkout": {"$regex": f"^{today_str}"}
    }, {"_id": 0, "total": 1}).to_list(100)
    
    ingresos_hoy = sum(c["total"] for c in today_checkouts)
    
    # Monthly revenue
    first_day_month = today.replace(day=1)
    month_checkouts = await db.checkouts.find({
        "fecha_hora_checkout": {"$gte": first_day_month.isoformat()}
    }, {"_id": 0, "total": 1}).to_list(1000)
    
    ingresos_mes = sum(c["total"] for c in month_checkouts)
    
    return {
        "fecha": today_str,
        "habitaciones": {
            "total": total_rooms,
            "ocupadas": occupied,
            "disponibles": available,
            "mantenimiento": maintenance,
            "limpieza": cleaning,
            "tasa_ocupacion": round(occupied / total_rooms * 100, 1) if total_rooms > 0 else 0
        },
        "movimientos_hoy": {
            "checkins_pendientes": checkins_hoy,
            "checkouts_pendientes": checkouts_hoy
        },
        "reservas_activas": reservas_activas,
        "ingresos": {
            "hoy": ingresos_hoy,
            "mes": ingresos_mes
        }
    }


@router.get("/top-clientes")
async def get_top_clients(
    limite: int = Query(10, ge=1, le=50),
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """RF-13: Top 10 clientes por cantidad de reservas/ingresos"""
    from server import db
    
    # Build date filter
    match_stage = {"estado": {"$in": ["confirmada", "checked_in", "checked_out"]}}
    if fecha_inicio:
        match_stage["fecha_checkin"] = {"$gte": fecha_inicio.isoformat()}
    if fecha_fin:
        if "fecha_checkin" in match_stage:
            match_stage["fecha_checkin"]["$lte"] = fecha_fin.isoformat()
        else:
            match_stage["fecha_checkin"] = {"$lte": fecha_fin.isoformat()}
    
    # Aggregate by guest document
    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": "$huesped.documento",
            "nombre": {"$first": "$huesped.nombre_completo"},
            "email": {"$first": "$huesped.email"},
            "total_reservas": {"$sum": 1},
            "total_gastado": {"$sum": "$precio_total"}
        }},
        {"$sort": {"total_gastado": -1}},
        {"$limit": limite}
    ]
    
    results = await db.reservas.aggregate(pipeline).to_list(limite)
    
    return [
        {
            "documento": r["_id"],
            "nombre": r["nombre"],
            "email": r["email"],
            "total_reservas": r["total_reservas"],
            "total_gastado": r["total_gastado"]
        }
        for r in results
    ]


@router.get("/ingresos-por-tipo")
async def get_revenue_by_room_type(
    fecha_inicio: date,
    fecha_fin: date,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """Reporte de ingresos desglosado por tipo de habitación"""
    from server import db
    
    # Get room types
    tipos = await db.tipos_habitacion.find({}, {"_id": 0}).to_list(100)
    tipo_map = {t["id"]: t["nombre"] for t in tipos}
    
    # Get rooms
    rooms = await db.habitaciones.find({}, {"_id": 0, "id": 1, "tipo_habitacion_id": 1}).to_list(100)
    room_tipo_map = {r["id"]: r["tipo_habitacion_id"] for r in rooms}
    
    # Get reservations
    reservations = await db.reservas.find({
        "fecha_checkin": {"$lte": fecha_fin.isoformat()},
        "fecha_checkout": {"$gte": fecha_inicio.isoformat()},
        "estado": {"$in": ["confirmada", "checked_in", "checked_out"]}
    }, {"_id": 0}).to_list(10000)
    
    # Aggregate by room type
    revenue_by_type = {}
    for tipo_id, tipo_nombre in tipo_map.items():
        revenue_by_type[tipo_id] = {
            "nombre": tipo_nombre,
            "reservas": 0,
            "ingresos": 0
        }
    
    for res in reservations:
        tipo_id = room_tipo_map.get(res["habitacion_id"])
        if tipo_id and tipo_id in revenue_by_type:
            revenue_by_type[tipo_id]["reservas"] += 1
            revenue_by_type[tipo_id]["ingresos"] += res["precio_total"]
    
    return {
        "fecha_inicio": fecha_inicio.isoformat(),
        "fecha_fin": fecha_fin.isoformat(),
        "por_tipo": list(revenue_by_type.values())
    }
