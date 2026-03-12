# API Hotel Boutique - Colección Postman

## Descripción
Colección de endpoints para el Sistema de Gestión de Reservas del Hotel Boutique.

## Base URL
```
https://boutique-reserve-hub.preview.emergentagent.com/api
```

## Autenticación
La API usa JWT (Bearer Token). Incluir en headers:
```
Authorization: Bearer <token>
```

---

## 1. AUTENTICACIÓN (/auth)

### 1.1 Login
```
POST /api/auth/login
Content-Type: application/json

Body:
{
    "email": "admin@hotelimperium.com",
    "password": "Admin123!"
}

Response:
{
    "access_token": "eyJ...",
    "token_type": "bearer",
    "usuario": {
        "id": "...",
        "email": "admin@hotelimperium.com",
        "nombre_completo": "Administrador Hotel",
        "rol": "administrador"
    }
}
```

### 1.2 Registro (solo huéspedes)
```
POST /api/auth/registro
Content-Type: application/json

Body:
{
    "email": "nuevo@email.com",
    "password": "Password123",
    "nombre_completo": "Nombre Completo",
    "documento": "1234567890",
    "telefono": "+57 300 123 4567",
    "rol": "huesped"
}
```

### 1.3 Obtener Usuario Actual
```
GET /api/auth/me
Authorization: Bearer <token>
```

### 1.4 Cambiar Contraseña
```
POST /api/auth/cambiar-password
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
    "current_password": "Admin123!",
    "new_password": "NuevaPass123!"
}
```

---

## 2. USUARIOS (/usuarios) - Solo Admin

### 2.1 Listar Usuarios
```
GET /api/usuarios?rol=recepcionista&activo=true&skip=0&limit=50
Authorization: Bearer <admin_token>
```

### 2.2 Crear Usuario
```
POST /api/usuarios
Authorization: Bearer <admin_token>
Content-Type: application/json

Body:
{
    "email": "nuevo.recep@hotel.com",
    "password": "Password123",
    "nombre_completo": "Nuevo Recepcionista",
    "documento": "9876543210",
    "telefono": "+57 300 987 6543",
    "rol": "recepcionista"
}
```

### 2.3 Actualizar Usuario
```
PUT /api/usuarios/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

Body:
{
    "nombre_completo": "Nombre Actualizado",
    "telefono": "+57 300 111 2222",
    "activo": true
}
```

### 2.4 Desactivar Usuario
```
DELETE /api/usuarios/{user_id}
Authorization: Bearer <admin_token>
```

### 2.5 Restablecer Contraseña
```
POST /api/usuarios/{user_id}/restablecer-password
Authorization: Bearer <admin_token>
```

---

## 3. HABITACIONES (/habitaciones)

### 3.1 Listar Habitaciones
```
GET /api/habitaciones?piso=1&estado=disponible&skip=0&limit=50
Authorization: Bearer <token>
```

### 3.2 Consultar Disponibilidad (RF-01)
```
GET /api/habitaciones/disponibilidad?fecha_checkin=2026-03-15&fecha_checkout=2026-03-18&num_huespedes=2&precio_min=100000&precio_max=500000
Authorization: Bearer <token>

Response:
{
    "habitaciones_disponibles": [...],
    "total": 20,
    "filtros_aplicados": {...}
}
```

### 3.3 Listar Tipos de Habitación
```
GET /api/habitaciones/tipos
Authorization: Bearer <token>

Response:
[
    {
        "id": "...",
        "codigo": "EST",
        "nombre": "Estándar",
        "capacidad_maxima": 2,
        "precio_base": 150000,
        "amenidades": ["WiFi", "TV", ...]
    }
]
```

### 3.4 Obtener Habitación
```
GET /api/habitaciones/{habitacion_id}
Authorization: Bearer <token>
```

### 3.5 Crear Habitación (Admin)
```
POST /api/habitaciones
Authorization: Bearer <admin_token>
Content-Type: application/json

Body:
{
    "numero": "401",
    "piso": 4,
    "tipo_habitacion_id": "<tipo_id>",
    "descripcion": "Nueva habitación",
    "fotos": [],
    "precio_temporada_alta": 200000
}
```

### 3.6 Actualizar Habitación
```
PUT /api/habitaciones/{habitacion_id}
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
    "descripcion": "Habitación renovada",
    "estado": "mantenimiento"
}
```

### 3.7 Eliminar Habitación (Admin)
```
DELETE /api/habitaciones/{habitacion_id}
Authorization: Bearer <admin_token>

// No permite eliminar si hay reservas activas
```

---

## 4. RESERVAS (/reservas)

### 4.1 Listar Reservas
```
GET /api/reservas?estado=confirmada&fecha_desde=2026-03-01&fecha_hasta=2026-03-31
Authorization: Bearer <token>

// Huéspedes solo ven sus propias reservas
```

### 4.2 Buscar Reserva
```
GET /api/reservas/buscar?codigo=RES-20260312-XXXX
GET /api/reservas/buscar?documento=1234567890
GET /api/reservas/buscar?nombre=Juan
Authorization: Bearer <recep/admin_token>
```

### 4.3 Crear Reserva (RF-02)
```
POST /api/reservas
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
    "habitacion_id": "<habitacion_id>",
    "fecha_checkin": "2026-03-15",
    "fecha_checkout": "2026-03-18",
    "num_huespedes": 2,
    "huesped": {
        "nombre_completo": "Juan Pérez García",
        "documento": "1122334455",
        "email": "juan@email.com",
        "telefono": "+57 300 123 4567",
        "ciudad": "Bogotá",
        "pais": "Colombia"
    },
    "acompanantes": [
        {
            "nombre_completo": "María López",
            "documento": "9988776655",
            "es_menor": false
        }
    ],
    "servicios_adicionales": ["<servicio_id>"],
    "notas": "Llegada tardía",
    "metodo_pago": "tarjeta_credito"
}

Response:
{
    "id": "...",
    "codigo": "RES-20260312-XXXX",
    "estado": "confirmada",
    "precio_habitacion": 450000,
    "precio_servicios": 70000,
    "precio_total": 520000,
    ...
}
```

### 4.4 Modificar Reserva (RF-03)
```
PUT /api/reservas/{reserva_id}
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
    "fecha_checkin": "2026-03-16",
    "fecha_checkout": "2026-03-19",
    "servicios_adicionales": ["<nuevo_servicio_id>"],
    "notas": "Actualizado"
}

// Solo permitido con >24h de anticipación
```

### 4.5 Cancelar Reserva (RF-04)
```
POST /api/reservas/{reserva_id}/cancelar
Authorization: Bearer <token>
Content-Type: application/json

Body:
{
    "motivo": "Cambio de planes"
}

Response:
{
    "codigo": "RES-20260312-XXXX",
    "politica_aplicada": "Más de 48 horas: reembolso completo",
    "monto_original": 520000,
    "monto_reembolso": 520000,
    "porcentaje_reembolso": 100.0
}

// Políticas:
// - >48h: 100% reembolso
// - 24-48h: 50% reembolso
// - <24h: 0% reembolso
```

---

## 5. CHECK-IN / CHECK-OUT

### 5.1 Proceso de Check-in (RF-06)
```
POST /api/checkin
Authorization: Bearer <recep/admin_token>
Content-Type: application/json

Body:
{
    "reserva_id": "<reserva_id>"
    // O alternativamente:
    // "codigo_reserva": "RES-20260312-XXXX"
    // "documento_huesped": "1122334455"
}

Response:
{
    "id": "...",
    "reserva": {...},
    "habitacion": {
        "numero": "101",
        "estado": "ocupada"
    },
    "fecha_hora_checkin": "2026-03-12T15:30:00Z"
}
```

### 5.2 Registrar Consumo
```
POST /api/consumos
Authorization: Bearer <recep/admin_token>
Content-Type: application/json

Body:
{
    "reserva_id": "<reserva_id>",
    "descripcion": "Agua mineral",
    "cantidad": 2,
    "precio_unitario": 5000,
    "categoria": "minibar"
}
```

### 5.3 Ver Consumos de Reserva
```
GET /api/consumos/{reserva_id}
Authorization: Bearer <recep/admin_token>
```

### 5.4 Proceso de Check-out (RF-07)
```
POST /api/checkout
Authorization: Bearer <recep/admin_token>
Content-Type: application/json

Body:
{
    "reserva_id": "<reserva_id>",
    "notas": "Sin novedades"
}

Response:
{
    "id": "...",
    "reserva": {...},
    "consumos": [...],
    "subtotal_habitacion": 300000,
    "subtotal_servicios": 70000,
    "subtotal_consumos": 25000,
    "impuestos": 75050,
    "total": 470050,
    "factura_id": "<factura_id>"
}
```

### 5.5 Pre Check-in Online (RF-08)
```
// Público - No requiere autenticación
GET /api/precheckin/{codigo_reserva}

PUT /api/precheckin/{codigo_reserva}?hora_llegada=15:00&notas=Llegamos con equipaje extra
```

---

## 6. PAGOS (/pagos)

### 6.1 Listar Pagos
```
GET /api/pagos?reserva_id=<id>&metodo_pago=efectivo
Authorization: Bearer <recep/admin_token>
```

### 6.2 Registrar Pago (RF-10)
```
POST /api/pagos
Authorization: Bearer <recep/admin_token>
Content-Type: application/json

Body:
{
    "reserva_id": "<reserva_id>",
    "monto": 500000,
    "metodo_pago": "tarjeta_credito",
    "referencia": "REF-12345",
    "notas": "Pago inicial"
}

// Métodos: tarjeta_credito, tarjeta_debito, efectivo, transferencia
```

### 6.3 Pagos por Reserva
```
GET /api/pagos/reserva/{reserva_id}
Authorization: Bearer <token>
```

---

## 7. FACTURAS (/facturas)

### 7.1 Listar Facturas
```
GET /api/facturas?estado=emitida&fecha_desde=2026-03-01
Authorization: Bearer <recep/admin_token>
```

### 7.2 Obtener Factura por ID
```
GET /api/facturas/{factura_id}
Authorization: Bearer <token>
```

### 7.3 Obtener Factura por Número
```
GET /api/facturas/numero/{numero_factura}
Authorization: Bearer <token>

// Ejemplo: FAC-202603-1234
```

### 7.4 Actualizar Estado Factura
```
PUT /api/facturas/{factura_id}/estado?estado=pagada
Authorization: Bearer <admin_token>

// Estados: emitida, pagada, anulada
```

---

## 8. REPORTES (/reportes)

### 8.1 Dashboard
```
GET /api/reportes/dashboard
Authorization: Bearer <recep/admin_token>

Response:
{
    "fecha": "2026-03-12",
    "habitaciones": {
        "total": 24,
        "ocupadas": 5,
        "disponibles": 18,
        "tasa_ocupacion": 20.8
    },
    "movimientos_hoy": {
        "checkins_pendientes": 3,
        "checkouts_pendientes": 2
    },
    "ingresos": {
        "hoy": 850000,
        "mes": 12500000
    }
}
```

### 8.2 Reporte de Ocupación (RF-13)
```
GET /api/reportes/ocupacion?fecha_inicio=2026-03-01&fecha_fin=2026-03-31
Authorization: Bearer <admin_token>

Response:
{
    "fecha_inicio": "2026-03-01",
    "fecha_fin": "2026-03-31",
    "total_habitaciones": 24,
    "habitaciones_ocupadas": 450,
    "tasa_ocupacion": 60.48,
    "ingresos_totales": 45000000,
    "reservas_realizadas": 85,
    "reservas_canceladas": 12,
    "promedio_estancia": 2.5
}
```

### 8.3 Top Clientes
```
GET /api/reportes/top-clientes?limite=10&fecha_inicio=2026-01-01
Authorization: Bearer <admin_token>
```

### 8.4 Ingresos por Tipo de Habitación
```
GET /api/reportes/ingresos-por-tipo?fecha_inicio=2026-03-01&fecha_fin=2026-03-31
Authorization: Bearer <admin_token>
```

---

## 9. OTROS

### 9.1 Servicios Adicionales
```
GET /api/servicios-adicionales

Response:
[
    {"id": "...", "codigo": "DESAYUNO", "nombre": "Desayuno Buffet", "precio": 35000},
    {"id": "...", "codigo": "PARKING", "nombre": "Parqueadero", "precio": 25000},
    ...
]
```

### 9.2 Health Check
```
GET /api/health

Response:
{
    "status": "healthy",
    "database": "connected",
    "stats": {
        "usuarios": 3,
        "habitaciones": 24,
        "reservas": 15
    }
}
```

---

## CREDENCIALES DE PRUEBA

| Rol | Email | Contraseña |
|-----|-------|------------|
| Administrador | admin@hotelimperium.com | Admin123! |
| Recepcionista | recepcion@hotelimperium.com | Recep123! |
| Huésped | huesped@test.com | Huesped123! |

---

## CASOS DE PRUEBA SUGERIDOS

### Caso 1: Flujo Completo de Reserva
1. Login como huésped
2. Consultar disponibilidad
3. Crear reserva
4. Login como recepcionista
5. Hacer check-in
6. Registrar consumos
7. Hacer check-out
8. Verificar factura

### Caso 2: Modificación de Reserva (>24h)
1. Crear reserva para fecha futura (>24h)
2. Modificar fechas y servicios
3. Verificar recálculo de precio

### Caso 3: Cancelación con Políticas
1. Crear reserva para dentro de 3 días
2. Cancelar → Verificar 100% reembolso
3. Crear reserva para mañana
4. Intentar cancelar → Verificar 50% reembolso

### Caso 4: Control de Acceso (RBAC)
1. Login como huésped
2. Intentar acceder a /usuarios → 403 Forbidden
3. Intentar acceder a /reportes/ocupacion → 403 Forbidden
