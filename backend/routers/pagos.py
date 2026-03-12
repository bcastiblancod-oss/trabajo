"""
Router de Pagos - Hotel Boutique
Registro de pagos (RF-10)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from models import (
    PagoCreate, PagoResponse, PagoInDB, MetodoPago
)
from utils import (
    get_current_user, require_roles, TokenPayload,
    generate_payment_receipt
)


router = APIRouter(prefix="/pagos", tags=["Pagos"])


@router.get("", response_model=List[PagoResponse])
async def list_payments(
    reserva_id: Optional[str] = None,
    metodo_pago: Optional[MetodoPago] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """Listar pagos con filtros opcionales"""
    from server import db
    
    query = {}
    if reserva_id:
        query["reserva_id"] = reserva_id
    if metodo_pago:
        query["metodo_pago"] = metodo_pago.value
    if fecha_desde:
        query["fecha"] = {"$gte": fecha_desde}
    if fecha_hasta:
        if "fecha" in query:
            query["fecha"]["$lte"] = fecha_hasta
        else:
            query["fecha"] = {"$lte": fecha_hasta}
    
    cursor = db.pagos.find(query, {"_id": 0}).skip(skip).limit(limit).sort("fecha", -1)
    pagos = await cursor.to_list(length=limit)
    
    return [
        PagoResponse(
            id=p["id"],
            reserva_id=p["reserva_id"],
            monto=p["monto"],
            metodo_pago=p["metodo_pago"],
            referencia=p.get("referencia"),
            notas=p.get("notas"),
            fecha=datetime.fromisoformat(p["fecha"]) if isinstance(p["fecha"], str) else p["fecha"],
            registrado_por=p["registrado_por"],
            comprobante=p["comprobante"]
        )
        for p in pagos
    ]


@router.get("/{pago_id}", response_model=PagoResponse)
async def get_payment(
    pago_id: str,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """Obtener pago por ID"""
    from server import db
    
    pago = await db.pagos.find_one({"id": pago_id}, {"_id": 0})
    if not pago:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    return PagoResponse(
        id=pago["id"],
        reserva_id=pago["reserva_id"],
        monto=pago["monto"],
        metodo_pago=pago["metodo_pago"],
        referencia=pago.get("referencia"),
        notas=pago.get("notas"),
        fecha=datetime.fromisoformat(pago["fecha"]) if isinstance(pago["fecha"], str) else pago["fecha"],
        registrado_por=pago["registrado_por"],
        comprobante=pago["comprobante"]
    )


@router.post("", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: PagoCreate,
    current_user: TokenPayload = Depends(require_roles("recepcionista", "administrador"))
):
    """
    RF-10: Registrar pago.
    Soporta: tarjeta crédito/débito, efectivo, transferencia.
    """
    from server import db
    
    # Verify reservation exists
    reservation = await db.reservas.find_one({"id": request.reserva_id}, {"_id": 0})
    if not reservation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reserva no encontrada"
        )
    
    # Create payment
    now = datetime.now(timezone.utc)
    pago_id = str(uuid.uuid4())
    comprobante = generate_payment_receipt()
    
    pago_doc = {
        "id": pago_id,
        "reserva_id": request.reserva_id,
        "monto": request.monto,
        "metodo_pago": request.metodo_pago.value,
        "referencia": request.referencia,
        "notas": request.notas,
        "fecha": now.isoformat(),
        "registrado_por": current_user.user_id,
        "comprobante": comprobante
    }
    
    await db.pagos.insert_one(pago_doc)
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "registrar_pago",
        "entidad": "pagos",
        "entidad_id": pago_id,
        "detalles": {
            "reserva": reservation["codigo"],
            "monto": request.monto,
            "metodo": request.metodo_pago.value,
            "comprobante": comprobante
        },
        "fecha": now.isoformat()
    })
    
    return PagoResponse(
        id=pago_id,
        reserva_id=request.reserva_id,
        monto=request.monto,
        metodo_pago=request.metodo_pago,
        referencia=request.referencia,
        notas=request.notas,
        fecha=now,
        registrado_por=current_user.user_id,
        comprobante=comprobante
    )


@router.get("/reserva/{reserva_id}", response_model=List[PagoResponse])
async def get_payments_by_reservation(
    reserva_id: str,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Obtener todos los pagos de una reserva"""
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
    
    pagos = await db.pagos.find({"reserva_id": reserva_id}, {"_id": 0}).to_list(100)
    
    return [
        PagoResponse(
            id=p["id"],
            reserva_id=p["reserva_id"],
            monto=p["monto"],
            metodo_pago=p["metodo_pago"],
            referencia=p.get("referencia"),
            notas=p.get("notas"),
            fecha=datetime.fromisoformat(p["fecha"]) if isinstance(p["fecha"], str) else p["fecha"],
            registrado_por=p["registrado_por"],
            comprobante=p["comprobante"]
        )
        for p in pagos
    ]
