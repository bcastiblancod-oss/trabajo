"""
Router de Usuarios - Hotel Boutique
CRUD de usuarios (solo administradores)
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from models import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, RolUsuario
)
from utils import (
    hash_password, get_current_user, require_roles, TokenPayload
)


router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("", response_model=List[UsuarioResponse])
async def list_users(
    rol: Optional[RolUsuario] = None,
    activo: Optional[bool] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """
    Listar todos los usuarios (solo administradores).
    Filtros opcionales: rol, estado activo.
    """
    from server import db
    
    # Build query
    query = {}
    if rol:
        query["rol"] = rol.value
    if activo is not None:
        query["activo"] = activo
    
    # Execute query
    cursor = db.usuarios.find(query, {"_id": 0, "password_hash": 0}).skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    
    return [
        UsuarioResponse(
            id=u["id"],
            email=u["email"],
            nombre_completo=u["nombre_completo"],
            documento=u["documento"],
            telefono=u.get("telefono"),
            rol=u["rol"],
            activo=u.get("activo", True),
            created_at=datetime.fromisoformat(u["created_at"]) if isinstance(u["created_at"], str) else u["created_at"],
            updated_at=datetime.fromisoformat(u["updated_at"]) if u.get("updated_at") and isinstance(u["updated_at"], str) else u.get("updated_at")
        )
        for u in users
    ]


@router.get("/{user_id}", response_model=UsuarioResponse)
async def get_user(
    user_id: str,
    current_user: TokenPayload = Depends(require_roles("administrador", "recepcionista"))
):
    """Obtener usuario por ID"""
    from server import db
    
    user = await db.usuarios.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
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


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UsuarioCreate,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """
    Crear nuevo usuario (solo administradores).
    Permite crear usuarios con cualquier rol.
    """
    from server import db
    
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
    user_id = str(uuid.uuid4())
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
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "crear_usuario",
        "entidad": "usuarios",
        "entidad_id": user_id,
        "detalles": {"email": request.email, "rol": request.rol.value},
        "fecha": now.isoformat()
    })
    
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


@router.put("/{user_id}", response_model=UsuarioResponse)
async def update_user(
    user_id: str,
    request: UsuarioUpdate,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """Actualizar usuario (solo administradores)"""
    from server import db
    
    # Get user
    user = await db.usuarios.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Build update
    update_data = {}
    if request.nombre_completo is not None:
        update_data["nombre_completo"] = request.nombre_completo
    if request.telefono is not None:
        update_data["telefono"] = request.telefono
    if request.activo is not None:
        update_data["activo"] = request.activo
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.usuarios.update_one({"id": user_id}, {"$set": update_data})
        
        # Log audit
        await db.logs_auditoria.insert_one({
            "id": str(uuid.uuid4()),
            "usuario_id": current_user.user_id,
            "accion": "actualizar_usuario",
            "entidad": "usuarios",
            "entidad_id": user_id,
            "detalles": update_data,
            "fecha": datetime.now(timezone.utc).isoformat()
        })
    
    # Get updated user
    user = await db.usuarios.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    
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


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """
    Desactivar usuario (solo administradores).
    No elimina, solo desactiva para mantener historial.
    """
    from server import db
    
    # Cannot delete yourself
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puede desactivar su propia cuenta"
        )
    
    # Get user
    user = await db.usuarios.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Deactivate user
    await db.usuarios.update_one(
        {"id": user_id},
        {"$set": {
            "activo": False,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "desactivar_usuario",
        "entidad": "usuarios",
        "entidad_id": user_id,
        "fecha": datetime.now(timezone.utc).isoformat()
    })
    
    return {"message": "Usuario desactivado exitosamente"}


@router.post("/{user_id}/restablecer-password")
async def reset_user_password(
    user_id: str,
    current_user: TokenPayload = Depends(require_roles("administrador"))
):
    """
    Restablecer contraseña de usuario (solo administradores).
    Genera una contraseña temporal.
    """
    from server import db
    import string
    import random
    
    # Get user
    user = await db.usuarios.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Generate temporary password
    temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    
    # Update password
    await db.usuarios.update_one(
        {"id": user_id},
        {"$set": {
            "password_hash": hash_password(temp_password),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Log audit
    await db.logs_auditoria.insert_one({
        "id": str(uuid.uuid4()),
        "usuario_id": current_user.user_id,
        "accion": "restablecer_password",
        "entidad": "usuarios",
        "entidad_id": user_id,
        "fecha": datetime.now(timezone.utc).isoformat()
    })
    
    return {
        "message": "Contraseña restablecida",
        "email": user["email"],
        "password_temporal": temp_password
    }
