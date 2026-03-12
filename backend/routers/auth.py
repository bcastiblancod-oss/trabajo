"""
Router de Autenticación - Hotel Boutique
Endpoints: login, registro, cambio de contraseña
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime, timezone

from models import (
    LoginRequest, TokenResponse, UsuarioCreate, UsuarioResponse,
    UsuarioInDB, ChangePasswordRequest, RolUsuario
)
from utils import (
    hash_password, verify_password, create_access_token,
    get_current_user, TokenPayload
)


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db=Depends(lambda: None)):
    """
    Iniciar sesión con email y contraseña.
    Retorna token JWT válido por 24 horas.
    """
    # Import db from server module
    from server import db
    
    # Find user by email
    user = await db.usuarios.find_one({"email": request.email}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Verify password
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )
    
    # Check if user is active
    if not user.get("activo", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    # Create access token
    token = create_access_token(user["id"], user["email"], user["rol"])
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(__import__("uuid").uuid4()),
        "usuario_id": user["id"],
        "accion": "login",
        "entidad": "usuarios",
        "entidad_id": user["id"],
        "detalles": {"email": user["email"]},
        "fecha": datetime.now(timezone.utc).isoformat()
    })
    
    return TokenResponse(
        access_token=token,
        usuario=UsuarioResponse(
            id=user["id"],
            email=user["email"],
            nombre_completo=user["nombre_completo"],
            documento=user["documento"],
            telefono=user.get("telefono"),
            rol=user["rol"],
            activo=user.get("activo", True),
            created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"]
        )
    )


@router.post("/registro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UsuarioCreate):
    """
    Registrar nuevo usuario (solo huéspedes pueden auto-registrarse).
    Administradores y recepcionistas se crean desde /usuarios.
    """
    from server import db
    
    # Force role to guest for self-registration
    if request.rol != RolUsuario.HUESPED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo se puede registrar como huésped. Contacte al administrador para otros roles."
        )
    
    # Check if email already exists
    existing = await db.usuarios.find_one({"email": request.email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )
    
    # Check if document already exists
    existing_doc = await db.usuarios.find_one({"documento": request.documento})
    if existing_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El documento ya está registrado"
        )
    
    # Create user
    user_id = str(__import__("uuid").uuid4())
    now = datetime.now(timezone.utc)
    
    user_doc = {
        "id": user_id,
        "email": request.email,
        "nombre_completo": request.nombre_completo,
        "documento": request.documento,
        "telefono": request.telefono,
        "rol": request.rol.value,
        "password_hash": hash_password(request.password),
        "activo": True,
        "created_at": now.isoformat(),
        "updated_at": None
    }
    
    await db.usuarios.insert_one(user_doc)
    
    return UsuarioResponse(
        id=user_id,
        email=request.email,
        nombre_completo=request.nombre_completo,
        documento=request.documento,
        telefono=request.telefono,
        rol=request.rol,
        activo=True,
        created_at=now
    )


@router.post("/cambiar-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenPayload = Depends(get_current_user)
):
    """Cambiar contraseña del usuario autenticado"""
    from server import db
    
    # Get user
    user = await db.usuarios.find_one({"id": current_user.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verify current password
    if not verify_password(request.current_password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña actual incorrecta"
        )
    
    # Update password
    new_hash = hash_password(request.new_password)
    await db.usuarios.update_one(
        {"id": current_user.user_id},
        {"$set": {
            "password_hash": new_hash,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(__import__("uuid").uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "cambio_password",
        "entidad": "usuarios",
        "entidad_id": current_user.user_id,
        "fecha": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Contraseña actualizada exitosamente"}


@router.get("/me", response_model=UsuarioResponse)
async def get_current_user_info(current_user: TokenPayload = Depends(get_current_user)):
    """Obtener información del usuario autenticado"""
    from server import db
    
    user = await db.usuarios.find_one({"id": current_user.user_id}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    return UsuarioResponse(
        id=user["id"],
        email=user["email"],
        nombre_completo=user["nombre_completo"],
        documento=user["documento"],
        telefono=user.get("telefono"),
        rol=user["rol"],
        activo=user.get("activo", True),
        created_at=datetime.fromisoformat(user["created_at"]) if isinstance(user["created_at"], str) else user["created_at"],
        updated_at=datetime.fromisoformat(user["updated_at"]) if user.get("updated_at") and isinstance(user["updated_at"], str) else user.get("updated_at")
    )
