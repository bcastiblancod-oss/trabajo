"""
Router de Facturas - Hotel Boutique
Generación y consulta de facturas (RF-09)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from models import FacturaResponse
from utils import (
    get_current_user, require_roles, TokenPayload
)


router = APIRouter(prefix="/facturas", tags=["Facturas"])


@router.get("", response_model=List[FacturaResponse])
async def list_invoices(
    reserva_id: Optional[str] = None,
    estado: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """Listar facturas con filtros opcionales"""
    from server import db
    
    query = {}
    if reserva_id:
        query["reserva_id"] = reserva_id
    if estado:
        query["estado"] = estado
    if fecha_desde:
        query["fecha_emision"] = {"$gte": fecha_desde}
    if fecha_hasta:
        if "fecha_emision" in query:
            query["fecha_emision"]["$lte"] = fecha_hasta
        else:
            query["fecha_emision"] = {"$lte": fecha_hasta}
    
    cursor = db.facturas.find(query, {"_id": 0}).skip(skip).limit(limit).sort("fecha_emision", -1)
    facturas = await cursor.to_list(length=limit)
    
    return [
        FacturaResponse(
            id=f["id"],
            numero=f["numero"],
            reserva_id=f["reserva_id"],
            checkout_id=f["checkout_id"],
            huesped=f["huesped"],
            items=f["items"],
            subtotal=f["subtotal"],
            impuestos=f["impuestos"],
            descuentos=f.get("descuentos", 0),
            total=f["total"],
            fecha_emision=datetime.fromisoformat(f["fecha_emision"]) if isinstance(f["fecha_emision"], str) else f["fecha_emision"],
            estado=f["estado"]
        )
        for f in facturas
    ]


@router.get("/{factura_id}", response_model=FacturaResponse)
async def get_invoice(
    factura_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Obtener factura por ID"""
    from server import db
    
    factura = await db.facturas.find_one({"id": factura_id}, {"_id": 0})
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )
    
    # For guests, verify they own the reservation
    if current_user.rol == "huesped":
        reservation = await db.reservas.find_one({"id": factura["reserva_id"]}, {"_id": 0})
        if not reservation or reservation["usuario_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a esta factura"
            )
    
    return FacturaResponse(
        id=factura["id"],
        numero=factura["numero"],
        reserva_id=factura["reserva_id"],
        checkout_id=factura["checkout_id"],
        huesped=factura["huesped"],
        items=factura["items"],
        subtotal=factura["subtotal"],
        impuestos=factura["impuestos"],
        descuentos=factura.get("descuentos", 0),
        total=factura["total"],
        fecha_emision=datetime.fromisoformat(factura["fecha_emision"]) if isinstance(factura["fecha_emision"], str) else factura["fecha_emision"],
        estado=factura["estado"]
    )


@router.get("/numero/{numero_factura}", response_model=FacturaResponse)
async def get_invoice_by_number(
    numero_factura: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Obtener factura por número"""
    from server import db
    
    factura = await db.facturas.find_one({"numero": numero_factura}, {"_id": 0})
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )
    
    # For guests, verify they own the reservation
    if current_user.rol == "huesped":
        reservation = await db.reservas.find_one({"id": factura["reserva_id"]}, {"_id": 0})
        if not reservation or reservation["usuario_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tiene acceso a esta factura"
            )
    
    return FacturaResponse(
        id=factura["id"],
        numero=factura["numero"],
        reserva_id=factura["reserva_id"],
        checkout_id=factura["checkout_id"],
        huesped=factura["huesped"],
        items=factura["items"],
        subtotal=factura["subtotal"],
        impuestos=factura["impuestos"],
        descuentos=factura.get("descuentos", 0),
        total=factura["total"],
        fecha_emision=datetime.fromisoformat(factura["fecha_emision"]) if isinstance(factura["fecha_emision"], str) else factura["fecha_emision"],
        estado=factura["estado"]
    )


@router.put("/{factura_id}/estado")
async def update_invoice_status(
    factura_id: str,
    estado: str,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """Actualizar estado de factura (solo administradores)"""
    from server import db
    
    if estado not in ["emitida", "pagada", "anulada"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Valores permitidos: emitida, pagada, anulada"
        )
    
    factura = await db.facturas.find_one({"id": factura_id}, {"_id": 0})
    if not factura:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Factura no encontrada"
        )
    
    await db.facturas.update_one(
        {"id": factura_id},
        {"$set": {"estado": estado}}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "actualizar_estado_factura",
        "entidad": "facturas",
        "entidad_id": factura_id,
        "detalles": {
            "numero": factura["numero"],
            "estado_anterior": factura["estado"],
            "estado_nuevo": estado
        },
        "fecha": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": f"Estado de factura actualizado a '{estado}'"}


@router.get("/reserva/{reserva_id}", response_model=List[FacturaResponse])
async def get_invoices_by_reservation(
    reserva_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Obtener todas las facturas de una reserva"""
    from server import db
    
    # Verify reservation exists
    reservation = await db.reservas.find_one({"id": reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Check permissions for guests
    if current_user.rol == "huesped" and reservation["usuario_id"] != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene acceso a esta reserva"
        )
    
    facturas = await db.facturas.find({"reserva_id": reserva_id}, {"_id": 0}).to_list(100)
    
    return [
        FacturaResponse(
            id=f["id"],
            numero=f["numero"],
            reserva_id=f["reserva_id"],
            checkout_id=f["checkout_id"],
            huesped=f["huesped"],
            items=f["items"],
            subtotal=f["subtotal"],
            impuestos=f["impuestos"],
            descuentos=f.get("descuentos", 0),
            total=f["total"],
            fecha_emision=datetime.fromisoformat(f["fecha_emision"]) if isinstance(f["fecha_emision"], str) else f["fecha_emision"],
            estado=f["estado"]
        )
        for f in facturas
    ]
