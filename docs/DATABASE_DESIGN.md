# Diseño de Base de Datos - Hotel Boutique

## 1. DISEÑO CONCEPTUAL Y LÓGICO

### 1.1 Colecciones MongoDB

| Colección | Descripción |
|-----------|-------------|
| `usuarios` | Usuarios del sistema (huéspedes, recepcionistas, administradores) |
| `tipos_habitacion` | Tipos de habitación (estándar, suite, familiar) |
| `habitaciones` | Las 24 habitaciones del hotel |
| `servicios_adicionales` | Servicios opcionales (desayuno, parking, spa, etc.) |
| `reservas` | Reservas con toda la información del huésped |
| `checkins` | Registro de check-ins |
| `checkouts` | Registro de check-outs |
| `consumos` | Consumos adicionales durante la estancia |
| `pagos` | Registro de pagos |
| `facturas` | Facturas generadas |
| `logs_auditoria` | Historial de actividad del sistema |

---

### 1.2 Estructura de Cada Colección

#### usuarios
```javascript
{
    "id": "uuid",                    // PK
    "email": "string",               // UNIQUE, NOT NULL
    "nombre_completo": "string",     // NOT NULL
    "documento": "string",           // UNIQUE, NOT NULL
    "telefono": "string",
    "rol": "enum",                   // huesped | recepcionista | administrador
    "password_hash": "string",       // bcrypt hash
    "activo": "boolean",             // DEFAULT true
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

#### tipos_habitacion
```javascript
{
    "id": "uuid",                    // PK
    "codigo": "string",              // EST, SUI, FAM - UNIQUE
    "nombre": "string",
    "descripcion": "string",
    "capacidad_maxima": "integer",
    "precio_base": "float",
    "amenidades": ["string"]         // Array de amenidades
}
```

#### habitaciones
```javascript
{
    "id": "uuid",                    // PK
    "numero": "string",              // UNIQUE (101, 102, etc.)
    "piso": "integer",
    "tipo_habitacion_id": "uuid",    // FK -> tipos_habitacion
    "descripcion": "string",
    "fotos": ["string"],             // URLs de fotos
    "estado": "enum",                // disponible | reservada | ocupada | mantenimiento | fuera_de_servicio | para_limpieza
    "precio_temporada_alta": "float",
    "precio_temporada_baja": "float",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

#### reservas
```javascript
{
    "id": "uuid",                    // PK
    "codigo": "string",              // UNIQUE (RES-YYYYMMDD-XXXX)
    "usuario_id": "uuid",            // FK -> usuarios
    "habitacion_id": "uuid",         // FK -> habitaciones
    "fecha_checkin": "date",
    "fecha_checkout": "date",
    "num_huespedes": "integer",
    "huesped": {                     // Documento embebido
        "nombre_completo": "string",
        "documento": "string",
        "email": "string",
        "telefono": "string",
        "direccion": "string",
        "ciudad": "string",
        "pais": "string"
    },
    "acompanantes": [{               // Array de documentos
        "nombre_completo": "string",
        "documento": "string",
        "es_menor": "boolean"
    }],
    "servicios_adicionales": [{      // Array de servicios contratados
        "servicio_id": "uuid",
        "cantidad": "integer",
        "precio_unitario": "float",
        "subtotal": "float"
    }],
    "estado": "enum",                // pendiente | confirmada | checked_in | checked_out | cancelada | no_show
    "precio_habitacion": "float",
    "precio_servicios": "float",
    "precio_total": "float",
    "notas": "string",
    "metodo_pago": "enum",           // tarjeta_credito | tarjeta_debito | efectivo | transferencia
    "created_at": "datetime",
    "updated_at": "datetime",
    "cancelada_at": "datetime",
    "motivo_cancelacion": "string",
    "monto_reembolso": "float"
}
```

#### servicios_adicionales
```javascript
{
    "id": "uuid",                    // PK
    "codigo": "string",              // UNIQUE
    "nombre": "string",
    "descripcion": "string",
    "precio": "float"
}
```

#### consumos
```javascript
{
    "id": "uuid",                    // PK
    "reserva_id": "uuid",            // FK -> reservas
    "descripcion": "string",
    "cantidad": "integer",
    "precio_unitario": "float",
    "subtotal": "float",
    "categoria": "string",           // minibar, lavanderia, telefono, etc.
    "fecha": "datetime",
    "registrado_por": "uuid"         // FK -> usuarios
}
```

#### checkins
```javascript
{
    "id": "uuid",                    // PK
    "reserva_id": "uuid",            // FK -> reservas
    "habitacion_id": "uuid",         // FK -> habitaciones
    "fecha_hora_checkin": "datetime",
    "realizado_por": "uuid",         // FK -> usuarios
    "notas": "string"
}
```

#### checkouts
```javascript
{
    "id": "uuid",                    // PK
    "reserva_id": "uuid",            // FK -> reservas
    "subtotal_habitacion": "float",
    "subtotal_servicios": "float",
    "subtotal_consumos": "float",
    "impuestos": "float",
    "total": "float",
    "fecha_hora_checkout": "datetime",
    "realizado_por": "uuid",         // FK -> usuarios
    "notas": "string"
}
```

#### pagos
```javascript
{
    "id": "uuid",                    // PK
    "reserva_id": "uuid",            // FK -> reservas
    "monto": "float",
    "metodo_pago": "enum",
    "referencia": "string",
    "notas": "string",
    "fecha": "datetime",
    "registrado_por": "uuid",        // FK -> usuarios
    "comprobante": "string"          // PAG-YYYYMMDD-XXXX
}
```

#### facturas
```javascript
{
    "id": "uuid",                    // PK
    "numero": "string",              // UNIQUE (FAC-YYYYMM-XXXX)
    "reserva_id": "uuid",            // FK -> reservas
    "checkout_id": "uuid",           // FK -> checkouts
    "huesped": {                     // Copia de datos del huésped
        "nombre_completo": "string",
        "documento": "string",
        "email": "string",
        ...
    },
    "items": [{                      // Detalle de conceptos
        "descripcion": "string",
        "cantidad": "integer",
        "precio_unitario": "float",
        "subtotal": "float"
    }],
    "subtotal": "float",
    "impuestos": "float",
    "descuentos": "float",
    "total": "float",
    "fecha_emision": "datetime",
    "estado": "string"               // emitida | pagada | anulada
}
```

#### logs_auditoria
```javascript
{
    "id": "uuid",                    // PK
    "usuario_id": "uuid",            // FK -> usuarios
    "accion": "string",              // login, crear_reserva, checkin, etc.
    "entidad": "string",             // usuarios, reservas, habitaciones, etc.
    "entidad_id": "uuid",
    "detalles": "object",            // JSON con detalles adicionales
    "ip_address": "string",
    "fecha": "datetime"
}
```

---

### 1.3 Relaciones

```
usuarios (1) ─────< (N) reservas
usuarios (1) ─────< (N) logs_auditoria

tipos_habitacion (1) ─────< (N) habitaciones

habitaciones (1) ─────< (N) reservas
habitaciones (1) ─────< (N) checkins

reservas (1) ─────< (N) consumos
reservas (1) ─────< (N) pagos
reservas (1) ────── (1) checkin
reservas (1) ────── (1) checkout
reservas (1) ────── (1) factura
```

---

### 1.4 Índices

```javascript
// usuarios
db.usuarios.createIndex("email", { unique: true })
db.usuarios.createIndex("documento")

// habitaciones
db.habitaciones.createIndex("numero", { unique: true })
db.habitaciones.createIndex("estado")
db.habitaciones.createIndex("tipo_habitacion_id")

// reservas
db.reservas.createIndex("codigo", { unique: true })
db.reservas.createIndex("usuario_id")
db.reservas.createIndex("habitacion_id")
db.reservas.createIndex("estado")
db.reservas.createIndex({ "fecha_checkin": 1, "fecha_checkout": 1 })

// facturas
db.facturas.createIndex("numero", { unique: true })
db.facturas.createIndex("reserva_id")

// logs_auditoria
db.logs_auditoria.createIndex("usuario_id")
db.logs_auditoria.createIndex("fecha")
```

---

## 2. DATOS INICIALES (SEED)

### 2.1 Tipos de Habitación
| Código | Nombre | Capacidad | Precio Base | Amenidades |
|--------|--------|-----------|-------------|------------|
| EST | Estándar | 2 | $150,000 | WiFi, TV, A/C, Baño privado |
| SUI | Suite | 2 | $350,000 | WiFi, TV 55", A/C, Jacuzzi, Minibar, Sala |
| FAM | Familiar | 4 | $280,000 | WiFi, TV, A/C, Baño privado, Sofá cama |

### 2.2 24 Habitaciones Pre-cargadas
| Piso | Números | Tipo | Cantidad |
|------|---------|------|----------|
| 1 | 101-108 | Estándar | 8 |
| 2 | 201-202, 207-208 | Estándar | 4 |
| 2 | 203-206 | Familiar | 4 |
| 3 | 301-308 | Suite | 8 |

### 2.3 Servicios Adicionales
| Código | Nombre | Precio |
|--------|--------|--------|
| DESAYUNO | Desayuno Buffet | $35,000 |
| PARKING | Parqueadero | $25,000 |
| SPA | Acceso Spa | $80,000 |
| TRANSFER | Transfer Aeropuerto | $60,000 |
| MINIBAR | Minibar | Variable |
| LAVANDERIA | Lavandería | Variable |

### 2.4 Usuarios de Prueba
| Rol | Email | Contraseña |
|-----|-------|------------|
| administrador | admin@hotelimperium.com | Admin123! |
| recepcionista | recepcion@hotelimperium.com | Recep123! |
| huesped | huesped@test.com | Huesped123! |

---

## 3. CONSIDERACIONES DE NEGOCIO

### 3.1 Estados de Habitación
```
disponible ──> reservada ──> ocupada ──> para_limpieza ──> disponible
                  │
                  └──> disponible (cancelación)

disponible <──> mantenimiento
disponible <──> fuera_de_servicio
```

### 3.2 Estados de Reserva
```
pendiente ──> confirmada ──> checked_in ──> checked_out
     │              │              │
     └──────────────┴──────────────┴───> cancelada
     │
     └──────────────────────────────────> no_show
```

### 3.3 Políticas de Cancelación
| Tiempo Anticipación | Reembolso |
|---------------------|-----------|
| > 48 horas | 100% |
| 24-48 horas | 50% |
| < 24 horas | 0% |

### 3.4 Restricción de Modificación
- Solo permitida con **más de 24 horas** de anticipación al check-in

### 3.5 Control de Acceso (RBAC)
| Recurso | Huésped | Recepcionista | Admin |
|---------|---------|---------------|-------|
| Ver habitaciones | ✓ | ✓ | ✓ |
| Crear reserva propia | ✓ | ✓ | ✓ |
| Ver reservas propias | ✓ | ✓ | ✓ |
| Ver todas las reservas | ✗ | ✓ | ✓ |
| Check-in/out | ✗ | ✓ | ✓ |
| Registrar pagos | ✗ | ✓ | ✓ |
| Gestionar usuarios | ✗ | ✗ | ✓ |
| Ver reportes | ✗ | Dashboard | Todo |
| Gestionar habitaciones | ✗ | Actualizar | CRUD |
