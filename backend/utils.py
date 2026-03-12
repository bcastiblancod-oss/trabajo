"""
Utilidades para el sistema de gestión de reservas - Hotel Boutique
Incluye: JWT, hashing, generación de códigos, validaciones de negocio
"""
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone, date
from typing import Optional
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import random
import string

from config import (
    JWT_SECRET_KEY, 
    JWT_ALGORITHM, 
    JWT_EXPIRATION_HOURS,
    CANCELLATION_POLICIES,
    MODIFICATION_MIN_HOURS
)


# ============== PASSWORD HASHING ==============
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


# ============== JWT TOKENS ==============
def create_access_token(user_id: str, email: str, rol: str) -> str:
    """Create JWT access token"""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user_id,
        "email": email,
        "rol": rol,
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


# ============== AUTH DEPENDENCY ==============
security = HTTPBearer()


class TokenPayload:
    def __init__(self, user_id: str, email: str, rol: str):
        self.user_id = user_id
        self.email = email
        self.rol = rol


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenPayload:
    """Get current user from JWT token"""
    token = credentials.credentials
    payload = decode_access_token(token)
    return TokenPayload(
        user_id=payload["sub"],
        email=payload["email"],
        rol=payload["rol"]
    )


def require_roles(*allowed_roles: str):
    """Decorator factory for role-based access control"""
    async def role_checker(
        current_user: TokenPayload = Depends(get_current_user)
    ) -> TokenPayload:
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere rol: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


# ============== CODE GENERATION ==============
def generate_reservation_code() -> str:
    """Generate unique reservation code: RES-YYYYMMDD-XXXX"""
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"RES-{date_part}-{random_part}"


def generate_invoice_number() -> str:
    """Generate sequential invoice number: FAC-YYYYMM-XXXX"""
    date_part = datetime.now().strftime("%Y%m")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"FAC-{date_part}-{random_part}"


def generate_payment_receipt() -> str:
    """Generate payment receipt number: PAG-YYYYMMDD-XXXX"""
    date_part = datetime.now().strftime("%Y%m%d")
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"PAG-{date_part}-{random_part}"


# ============== BUSINESS RULES ==============
def calculate_nights(checkin: date, checkout: date) -> int:
    """Calculate number of nights between dates"""
    return (checkout - checkin).days


def calculate_cancellation_refund(
    reservation_checkin: date, 
    total_amount: float
) -> tuple[float, float, str]:
    """
    Calculate refund amount based on cancellation policy
    Returns: (refund_amount, refund_percentage, policy_applied)
    """
    now = datetime.now(timezone.utc)
    checkin_datetime = datetime.combine(reservation_checkin, datetime.min.time()).replace(tzinfo=timezone.utc)
    hours_until_checkin = (checkin_datetime - now).total_seconds() / 3600
    
    if hours_until_checkin > CANCELLATION_POLICIES["full_refund_hours"]:
        return total_amount, 100.0, "Más de 48 horas: reembolso completo"
    elif hours_until_checkin > CANCELLATION_POLICIES["partial_refund_hours"]:
        return total_amount * 0.5, 50.0, "Entre 24-48 horas: reembolso parcial"
    else:
        return 0.0, 0.0, "Menos de 24 horas: sin reembolso"


def can_modify_reservation(reservation_checkin: date) -> tuple[bool, str]:
    """
    Check if reservation can be modified (min 24h before checkin)
    Returns: (can_modify, message)
    """
    now = datetime.now(timezone.utc)
    checkin_datetime = datetime.combine(reservation_checkin, datetime.min.time()).replace(tzinfo=timezone.utc)
    hours_until_checkin = (checkin_datetime - now).total_seconds() / 3600
    
    if hours_until_checkin < MODIFICATION_MIN_HOURS:
        return False, f"No se puede modificar con menos de {MODIFICATION_MIN_HOURS} horas de anticipación"
    return True, "Modificación permitida"


def validate_dates(checkin: date, checkout: date) -> tuple[bool, str]:
    """Validate reservation dates"""
    today = date.today()
    
    if checkin < today:
        return False, "La fecha de check-in no puede ser anterior a hoy"
    if checkout <= checkin:
        return False, "La fecha de check-out debe ser posterior al check-in"
    if (checkout - checkin).days > 30:
        return False, "La estancia máxima es de 30 noches"
    
    return True, "Fechas válidas"


# ============== DATE HELPERS ==============
def date_to_datetime(d: date) -> datetime:
    """Convert date to datetime with UTC timezone"""
    return datetime.combine(d, datetime.min.time()).replace(tzinfo=timezone.utc)


def datetime_to_str(dt: datetime) -> str:
    """Convert datetime to ISO string"""
    return dt.isoformat()


def str_to_datetime(s: str) -> datetime:
    """Convert ISO string to datetime"""
    return datetime.fromisoformat(s)


def date_to_str(d: date) -> str:
    """Convert date to ISO string"""
    return d.isoformat()


def str_to_date(s: str) -> date:
    """Convert ISO string to date"""
    return date.fromisoformat(s)
