# Checklist de Pruebas - Fyntra (Presentación TFG)

Este documento contiene las credenciales de usuarios de prueba y el checklist completo para verificar todas las funcionalidades antes de la presentación.

---

## Tabla de Usuarios de Prueba

*Ejecutar `POST /api/admin/init-data` antes de las pruebas para crear los datos iniciales.*

| Rol | Email | Contraseña |
|-----|-------|------------|
| Super Admin | admin@fyntra.com | admin123 |
| Admin Transportes | admint@fyntra.com | transportes123 |
| Admin Fincas | adminf@fyntra.com | fincas123 |
| Propietario | propietario@test.com | 123456 |
| Proveedor (Fontanería) | fontaneria@test.com | 123456 |
| Proveedor (Electricidad) | electricidad@test.com | 123456 |
| Conductor (Juan) | juan.garcia@fyntra.com | 123456 |
| Conductor (María) | maria.martinez@fyntra.com | 123456 |

---

## Checklist de Pruebas

Leyenda columnas:
- **✓**: Marcar cuando la prueba ha sido revisada
- **Descripción**: Qué se debe verificar
- **Observaciones**: Resultado, fallos detectados, notas (ej: "OK", "Falla en...", "No probado")

---

### 1. Infraestructura y API

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Health check: GET `/health` devuelve status "healthy" y DB/Redis OK | |
| | API Docs: Swagger carga correctamente en `/docs` | |
| | Init data: POST `/api/admin/init-data` crea usuarios y datos de prueba | |
| | Frontend accesible en http://localhost:4200 | |

---

### 2. Autenticación

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Login correcto con usuario activo | |
| | Login incorrecto (email/contraseña): mensaje genérico, no revelar si existe el usuario | |
| | Login con usuario inactivo: 403 "Usuario inactivo" | |
| | Token expirado/inválido: 401 | |
| | Protección fuerza bruta: varios intentos fallidos → 429 y mensaje de bloqueo temporal | |

---

### 3. Roles y Permisos (Frontend Web)

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Super Admin: ve selector de módulos (Fincas, Transportes, Usuarios) | |
| | Super Admin: acceso a todos los módulos y gestión de usuarios | |
| | Admin Fincas: acceso a incidencias, comunidades, inmuebles, propietarios, proveedores | |
| | Admin Transportes: acceso a vehículos, conductores, pedidos, rutas, mantenimientos, historial | |
| | Propietario: solo incidencias y mis inmuebles; no ve comunidades, propietarios, proveedores | |
| | Proveedor: solo incidencias asignadas | |
| | Admin Transportes/Admin Fincas: pueden cambiar entre módulos | |
| | Propietario intenta acceder a /comunidades: redirige o bloquea | |
| | Admin Fincas intenta acceder a /usuarios: redirige a /modulos | |

---

### 4. Módulo Fincas

#### Comunidades

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar comunidades | |
| | Crear comunidad | |
| | Editar comunidad | |
| | Eliminar comunidad (sin inmuebles con incidencias) | |
| | **Bloqueo**: No permitir eliminar comunidad si algún inmueble tiene incidencias | |

#### Inmuebles

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Admin: listar todos los inmuebles | |
| | Propietario: listar solo sus inmuebles | |
| | Admin: crear inmueble | |
| | Admin: editar inmueble | |
| | Admin: eliminar inmueble (sin incidencias) | |
| | **Bloqueo**: No permitir eliminar inmueble si tiene incidencias asociadas | |

#### Propietarios

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar propietarios | |
| | Crear propietario (con usuario) | |
| | Editar propietario | |
| | Eliminar propietario | |

#### Proveedores

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar proveedores | |
| | Crear proveedor (con usuario) | |
| | Editar proveedor | |
| | Activar/Desactivar proveedor | |

#### Incidencias

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Admin: ver todas las incidencias | |
| | Propietario: ver solo incidencias de sus inmuebles | |
| | Proveedor: ver solo incidencias asignadas | |
| | Crear incidencia (propietario o admin) | |
| | Asignar proveedor a incidencia | |
| | Cambiar estado de incidencia | |
| | Ver historial de cambios | |
| | Subir documento a incidencia | |
| | Enviar mensaje en incidencia | |
| | Proveedor: añadir actuación | |
| | Eliminar incidencia (admin o propietario creador) | |
| | Filtros: estado, prioridad, búsqueda | |

---

### 5. Módulo Transportes

#### Vehículos

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar vehículos | |
| | Crear vehículo | |
| | Editar vehículo | |
| | Cambiar estado (activo/mantenimiento/baja) | |

#### Conductores

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar conductores | |
| | Crear conductor (con usuario) | |
| | Editar conductor | |
| | Ver alertas de licencias próximas a caducar | |

#### Pedidos

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar pedidos | |
| | Crear pedido | |
| | Editar pedido | |
| | Cambiar estado del pedido | |
| | Eliminar pedido | |

#### Rutas

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar rutas | |
| | Crear ruta (conductor, vehículo, paradas, pedidos) | |
| | Editar ruta | |
| | Ver paradas de cada ruta | |
| | Validar capacidad y disponibilidad al asignar | |
| | Eliminar ruta | |

#### Mantenimientos

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar mantenimientos | |
| | Crear mantenimiento (preventivo/correctivo) | |
| | Completar mantenimiento | |
| | Ver alertas de mantenimientos próximos/vencidos | |

#### Historial de Rutas

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar historial de rutas completadas | |
| | Filtros por fecha, conductor, vehículo | |

---

### 6. Informes

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Acceso a Informes (solo admins) | |
| | Informes Fincas: costes por comunidad, período, proveedor | |
| | Informes Transportes: entregas, tiempos, eficiencia | |
| | Exportar a PDF/Excel/CSV | |

---

### 7. Gestión de Usuarios (solo Super Admin)

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Listar usuarios | |
| | Crear usuario con rol válido | |
| | Editar usuario (rol, activo) | |
| | Cambiar contraseña de usuario | |
| | Eliminar usuario | |
| | No eliminar último super_admin activo | |

---

### 8. RGPD

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Exportar mis datos: descarga JSON con datos personales y actividad | |
| | Eliminar mi cuenta: anonimización y desactivación | |
| | No eliminar último super_admin activo | |

---

### 9. Flujo Completo: Pedido → Ruta → Finalizar

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Crear 2+ pedidos en estado pendiente | |
| | Crear ruta asignando conductor, vehículo y pedidos | |
| | Verificar ruta aparece como "planificada" | |
| | En app móvil como conductor: iniciar ruta | |
| | Marcar paradas como entregadas (firma, foto) | |
| | Finalizar ruta | |
| | Verificar pedidos pasan a "entregado" y ruta a "completada" | |

---

### 10. Flujo Completo: Incidencia → Asignación → Actuaciones → Cierre

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Crear incidencia (propietario o admin) | |
| | Asignar proveedor a la incidencia | |
| | Proveedor añade actuación | |
| | Subir documento a la incidencia | |
| | Cambiar estado (abierta → en_proceso → cerrada) | |
| | Verificar historial de cambios correcto | |
| | Verificar incidencia queda cerrada con fecha de cierre | |

---

### 11. App Móvil Android

#### Conductor

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Login como conductor | |
| | Ver listado de rutas asignadas | |
| | Ver detalle de ruta | |
| | Iniciar ruta | |
| | Marcar paradas como entregadas | |
| | Finalizar ruta | |
| | Reportar incidencia en ruta | |

#### Propietario

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Login como propietario | |
| | Ver incidencias de sus inmuebles | |
| | Crear incidencia | |
| | Ver detalle: historial, documentos, chat, actuaciones | |
| | Subir documento | |
| | Enviar mensaje | |

#### Proveedor

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Login como proveedor | |
| | Ver incidencias asignadas | |
| | Ver detalle de incidencia | |
| | Añadir actuación | |
| | Subir documento | |
| | Enviar mensaje | |
| | Actualizar estado de incidencia | |

---

### 12. UX/UI

| ✓ | Descripción | Observaciones |
|---|-------------|---------------|
| | Diseño responsive (ordenador, tablet, móvil) | |
| | Menú hamburguesa en móvil | |
| | Mensajes de error claros | |
| | Loading en operaciones asíncronas | |
