# PRD - Sistema de Gestión de Reservas Hotel Boutique

## Problema Original
Sistema web de gestión de reservas para un hotel boutique de 24 habitaciones (estándar, suite, familiar). Sprint 2 enfocado en Backend + Base de Datos con API RESTful.

## Arquitectura Implementada
- **Backend**: Python FastAPI
- **Base de Datos**: MongoDB
- **Autenticación**: JWT (24h expiration)
- **ORM**: Motor (async MongoDB driver)

## User Personas
1. **Huésped**: Crea/gestiona sus propias reservas
2. **Recepcionista**: Gestiona reservas, check-in/out, facturación
3. **Administrador**: Acceso total + usuarios + reportes

## Requisitos Funcionales Implementados
- [x] RF-01: Consulta de disponibilidad (fechas, tipo, capacidad, precio)
- [x] RF-02: Creación de reserva con código único
- [x] RF-03: Modificación de reserva (>24h anticipación)
- [x] RF-04: Cancelación con políticas (100%/>48h, 50%/24-48h, 0%/<24h)
- [x] RF-05: CRUD habitaciones (protección reservas activas)
- [x] RF-06: Check-in (búsqueda por código/documento/nombre)
- [x] RF-07: Check-out con factura y consumos
- [x] RF-08: Pre check-in online (endpoint público)
- [x] RF-09: Generación de facturas
- [x] RF-10: Registro de pagos
- [x] RF-11: Gestión de usuarios
- [x] RF-12: Control RBAC
- [x] RF-13: Reportes (dashboard, ocupación, top clientes)

## What's Been Implemented (2026-03-12)
- API REST completa con FastAPI
- 24 habitaciones pre-cargadas (8 EST piso 1, 4 EST + 4 FAM piso 2, 8 SUI piso 3)
- 3 tipos de habitación con precios y amenidades
- 6 servicios adicionales
- Sistema de autenticación JWT
- RBAC con 3 roles
- Documentación Postman completa
- Documentación de diseño de BD

## Credenciales de Prueba
- Admin: admin@hotelimperium.com / Admin123!
- Recepcionista: recepcion@hotelimperium.com / Recep123!
- Huésped: huesped@test.com / Huesped123!

## Backlog Priorizado
### P0 (Completado)
- [x] API REST funcional
- [x] Autenticación y RBAC
- [x] CRUD habitaciones y reservas
- [x] Check-in/Check-out
- [x] Facturación básica

### P1 (Siguiente Sprint)
- [ ] Integración pasarela de pagos real (Stripe/PayU)
- [ ] Envío de emails de confirmación (SendGrid)
- [ ] Generación PDF de facturas
- [ ] WebSockets para notificaciones en tiempo real

### P2 (Futuro)
- [ ] Frontend administrativo
- [ ] Pre check-in con firma digital
- [ ] Integración con OTAs
- [ ] App móvil nativa

## Endpoints Principales
- POST /api/auth/login
- POST /api/auth/registro
- GET /api/habitaciones
- GET /api/habitaciones/disponibilidad
- POST /api/reservas
- POST /api/reservas/{id}/cancelar
- POST /api/checkin
- POST /api/checkout
- GET /api/reportes/dashboard
