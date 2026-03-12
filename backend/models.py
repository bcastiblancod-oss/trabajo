"""
Modelos Pydantic para el sistema de gestión de reservas - Hotel Boutique
"""
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date, timezone
from enum import Enum
import uuid


# ============== ENUMS ==============
class RolUsuario(str, Enum):
    HUESPED = "huesped"
    RECEPCIONISTA = "recepcionista"
    ADMINISTRADOR = "administrador"


class EstadoHabitacion(str, Enum):
    DISPONIBLE = "disponible"
    RESERVADA = "reservada"
    OCUPADA = "ocupada"
    MANTENIMIENTO = "mantenimiento"
    FUERA_DE_SERVICIO = "fuera_de_servicio"
    PARA_LIMPIEZA = "para_limpieza"


class EstadoReserva(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELADA = "cancelada"
    NO_SHOW = "no_show"


class MetodoPago(str, Enum):
    TARJETA_CREDITO = "tarjeta_credito"
    TARJETA_DEBITO = "tarjeta_debito"
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"


# ============== USUARIO ==============
class UsuarioBase(BaseModel):
    email: EmailStr
    nombre_completo: str = Field(..., min_length=2, max_length=100)
    documento: str = Field(..., min_length=5, max_length=20)
    telefono: Optional[str] = Field(None, max_length=20)
    rol: RolUsuario = RolUsuario.HUESPED


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)


class UsuarioUpdate(BaseModel):
    nombre_completo: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, max_length=20)
    activo: Optional[bool] = None


class UsuarioResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    email: EmailStr
    nombre_completo: str
    documento: str
    telefono: Optional[str] = None
    rol: RolUsuario
    activo: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None


class UsuarioInDB(UsuarioBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    password_hash: str
    activo: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


# ============== AUTENTICACIÓN ==============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioResponse


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=6)


# ============== TIPO HABITACIÓN ==============
class TipoHabitacionBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=10)
    nombre: str = Field(..., min_length=2, max_length=50)
    descripcion: Optional[str] = None
    capacidad_maxima: int = Field(..., ge=1, le=10)
    precio_base: float = Field(..., ge=0)
    amenidades: List[str] = []


class TipoHabitacionResponse(TipoHabitacionBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str


class TipoHabitacionInDB(TipoHabitacionBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


# ============== HABITACIÓN ==============
class HabitacionBase(BaseModel):
    numero: str = Field(..., min_length=1, max_length=10)
    piso: int = Field(..., ge=1, le=10)
    tipo_habitacion_id: str
    descripcion: Optional[str] = None
    fotos: List[str] = []
    precio_temporada_alta: Optional[float] = None
    precio_temporada_baja: Optional[float] = None


class HabitacionCreate(HabitacionBase):
    pass


class HabitacionUpdate(BaseModel):
    descripcion: Optional[str] = None
    fotos: Optional[List[str]] = None
    precio_temporada_alta: Optional[float] = None
    precio_temporada_baja: Optional[float] = None
    estado: Optional[EstadoHabitacion] = None


class HabitacionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    numero: str
    piso: int
    tipo_habitacion_id: str
    tipo_habitacion: Optional[TipoHabitacionResponse] = None
    descripcion: Optional[str] = None
    fotos: List[str] = []
    estado: EstadoHabitacion
    precio_temporada_alta: Optional[float] = None
    precio_temporada_baja: Optional[float] = None
    created_at: datetime


class HabitacionInDB(HabitacionBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    estado: EstadoHabitacion = EstadoHabitacion.DISPONIBLE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None


# ============== HUÉSPED (para reservas) ==============
class HuespedInfo(BaseModel):
    nombre_completo: str = Field(..., min_length=2)
    documento: str = Field(..., min_length=5)
    email: EmailStr
    telefono: str
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    pais: str = "Colombia"


class Acompanante(BaseModel):
    nombre_completo: str = Field(..., min_length=2)
    documento: str = Field(..., min_length=5)
    es_menor: bool = False


# ============== SERVICIO ADICIONAL ==============
class ServicioAdicionalBase(BaseModel):
    codigo: str = Field(..., min_length=2, max_length=20)
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None
    precio: float = Field(..., ge=0)


class ServicioAdicionalResponse(ServicioAdicionalBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str


class ServicioAdicionalInDB(ServicioAdicionalBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


# ============== RESERVA ==============
class ServicioReserva(BaseModel):
    servicio_id: str
    cantidad: int = 1
    precio_unitario: float
    subtotal: float


class ReservaBase(BaseModel):
    habitacion_id: str
    fecha_checkin: date
    fecha_checkout: date
    num_huespedes: int = Field(..., ge=1)
    huesped: HuespedInfo
    acompanantes: List[Acompanante] = []
    servicios_adicionales: List[str] = []  # Lista de IDs de servicios
    notas: Optional[str] = None
    
    @field_validator('fecha_checkout')
    @classmethod
    def checkout_after_checkin(cls, v, info):
        if 'fecha_checkin' in info.data and v <= info.data['fecha_checkin']:
            raise ValueError('La fecha de checkout debe ser posterior al checkin')
        return v


class ReservaCreate(ReservaBase):
    metodo_pago: MetodoPago = MetodoPago.TARJETA_CREDITO


class ReservaUpdate(BaseModel):
    fecha_checkin: Optional[date] = None
    fecha_checkout: Optional[date] = None
    habitacion_id: Optional[str] = None
    servicios_adicionales: Optional[List[str]] = None
    notas: Optional[str] = None


class ReservaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    codigo: str
    usuario_id: str
    habitacion_id: str
    habitacion: Optional[HabitacionResponse] = None
    fecha_checkin: date
    fecha_checkout: date
    num_huespedes: int
    huesped: HuespedInfo
    acompanantes: List[Acompanante] = []
    servicios_adicionales: List[ServicioReserva] = []
    estado: EstadoReserva
    precio_habitacion: float
    precio_servicios: float
    precio_total: float
    notas: Optional[str] = None
    metodo_pago: MetodoPago
    created_at: datetime
    updated_at: Optional[datetime] = None


class ReservaInDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    codigo: str
    usuario_id: str
    habitacion_id: str
    fecha_checkin: date
    fecha_checkout: date
    num_huespedes: int
    huesped: HuespedInfo
    acompanantes: List[Acompanante] = []
    servicios_adicionales: List[ServicioReserva] = []
    estado: EstadoReserva = EstadoReserva.PENDIENTE
    precio_habitacion: float
    precio_servicios: float
    precio_total: float
    notas: Optional[str] = None
    metodo_pago: MetodoPago
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    cancelada_at: Optional[datetime] = None
    motivo_cancelacion: Optional[str] = None
    monto_reembolso: Optional[float] = None


# ============== CHECK-IN ==============
class CheckInRequest(BaseModel):
    reserva_id: Optional[str] = None
    codigo_reserva: Optional[str] = None
    documento_huesped: Optional[str] = None
    nombre_huesped: Optional[str] = None
    habitacion_asignada: Optional[str] = None  # Puede cambiar la habitación


class CheckInResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    reserva_id: str
    reserva: ReservaResponse
    habitacion_id: str
    habitacion: HabitacionResponse
    fecha_hora_checkin: datetime
    realizado_por: str
    notas: Optional[str] = None


class CheckInInDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reserva_id: str
    habitacion_id: str
    fecha_hora_checkin: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    realizado_por: str
    notas: Optional[str] = None


# ============== CONSUMO ==============
class ConsumoBase(BaseModel):
    reserva_id: str
    descripcion: str = Field(..., min_length=2)
    cantidad: int = Field(..., ge=1)
    precio_unitario: float = Field(..., ge=0)
    categoria: str = Field(..., min_length=2)  # minibar, lavanderia, telefono, etc.


class ConsumoCreate(ConsumoBase):
    pass


class ConsumoResponse(ConsumoBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    subtotal: float
    fecha: datetime


class ConsumoInDB(ConsumoBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subtotal: float
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registrado_por: str


# ============== CHECK-OUT ==============
class CheckOutRequest(BaseModel):
    reserva_id: str
    metodo_pago_adicional: Optional[MetodoPago] = None
    notas: Optional[str] = None


class CheckOutResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    reserva_id: str
    reserva: ReservaResponse
    consumos: List[ConsumoResponse] = []
    subtotal_habitacion: float
    subtotal_servicios: float
    subtotal_consumos: float
    impuestos: float
    total: float
    fecha_hora_checkout: datetime
    realizado_por: str
    factura_id: Optional[str] = None


class CheckOutInDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    reserva_id: str
    subtotal_habitacion: float
    subtotal_servicios: float
    subtotal_consumos: float
    impuestos: float
    total: float
    fecha_hora_checkout: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    realizado_por: str
    notas: Optional[str] = None


# ============== PAGO ==============
class PagoBase(BaseModel):
    reserva_id: str
    monto: float = Field(..., gt=0)
    metodo_pago: MetodoPago
    referencia: Optional[str] = None
    notas: Optional[str] = None


class PagoCreate(PagoBase):
    pass


class PagoResponse(PagoBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    fecha: datetime
    registrado_por: str
    comprobante: str


class PagoInDB(PagoBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    registrado_por: str
    comprobante: str


# ============== FACTURA ==============
class ItemFactura(BaseModel):
    descripcion: str
    cantidad: int
    precio_unitario: float
    subtotal: float


class FacturaResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str
    numero: str
    reserva_id: str
    checkout_id: str
    huesped: HuespedInfo
    items: List[ItemFactura]
    subtotal: float
    impuestos: float
    descuentos: float
    total: float
    fecha_emision: datetime
    estado: str  # emitida, pagada, anulada


class FacturaInDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    numero: str
    reserva_id: str
    checkout_id: str
    huesped: HuespedInfo
    items: List[ItemFactura]
    subtotal: float
    impuestos: float
    descuentos: float
    total: float
    fecha_emision: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    estado: str = "emitida"


# ============== DISPONIBILIDAD ==============
class DisponibilidadQuery(BaseModel):
    fecha_checkin: date
    fecha_checkout: date
    tipo_habitacion_id: Optional[str] = None
    num_huespedes: Optional[int] = None
    precio_min: Optional[float] = None
    precio_max: Optional[float] = None


class DisponibilidadResponse(BaseModel):
    habitaciones_disponibles: List[HabitacionResponse]
    total: int
    filtros_aplicados: dict


# ============== REPORTES ==============
class ReporteOcupacion(BaseModel):
    fecha_inicio: date
    fecha_fin: date
    total_habitaciones: int
    habitaciones_ocupadas: int
    tasa_ocupacion: float
    ingresos_totales: float
    reservas_realizadas: int
    reservas_canceladas: int
    promedio_estancia: float


# ============== LOG AUDITORÍA ==============
class LogAuditoriaInDB(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    usuario_id: str
    accion: str
    entidad: str
    entidad_id: str
    detalles: Optional[dict] = None
    ip_address: Optional[str] = None
    fecha: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ============== CANCELACIÓN ==============
class CancelacionRequest(BaseModel):
    motivo: Optional[str] = None


class CancelacionResponse(BaseModel):
    reserva_id: str
    codigo: str
    estado_anterior: str
    estado_nuevo: str
    politica_aplicada: str
    monto_original: float
    monto_reembolso: float
    porcentaje_reembolso: float
    mensaje: str
