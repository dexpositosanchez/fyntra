### Desarrollo de requisitos funcionales

| Nº y nombre de requisito | Explicación | Desarrollado | Revisado | Observaciones |
| --- | --- | --- | --- | --- |
| **TRANSPORTES** |  |  |  |  |
| RF1. Gestión de Flota | Registro de vehículos con información técnica y de estado, con consulta del historial completo de cada vehículo. | ✅ | ❌ | Falta el historial |
| RF2. Gestión de Conductores | Registro de conductores con datos personales, licencia, fecha de caducidad y estado, con alertas de licencias próximas a caducar. | ✅ | ✅ |  |
| RF3. Gestión de Pedidos | Creación de pedidos con datos de origen, destino, cliente, volumen, peso, tipo de mercancía, fecha deseada y gestión de sus estados. | ✅ | ✅ |  |
| RF4. Planificación de Rutas | Creación de rutas asignando conductor y vehículo, con múltiples pedidos y orden de entrega, validando capacidades y disponibilidad. | ✅ | ✅ |  |
| RF5. Seguimiento de Entregas | Confirmación de entregas desde la app móvil, con firma del cliente, foto de la entrega y actualización de estado en tiempo real. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF6. Gestión de Mantenimientos | Programación y registro de mantenimientos preventivos y correctivos, con alertas de mantenimientos próximos o vencidos. | ✅ | ✅ |  |
| RF7. Reporte de Incidencias en Ruta | Registro desde la app móvil de incidencias en ruta (averías, retrasos, cliente ausente) con descripción y fotos. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF8. Informes de Operaciones | Informes de entregas, tiempos de ruta, eficiencia de conductores, costes de mantenimiento y rendimiento de la flota. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF9. Historial de Rutas | Historial completo de rutas realizadas con fecha, conductor, vehículo, pedidos entregados y tiempos. | ⬜ | ⬜ / ✅ / ❌ |  |
| **FINCAS** |  |  |  |  |
| RF10. Gestión de Comunidades | El sistema debe permitir a los administradores crear, editar, eliminar y consultar comunidades de propietarios, con información básica y asociación a múltiples inmuebles. | ✅ | ✅ |  |
| RF11. Gestión de Inmuebles | Registro de inmuebles asociados a comunidades, con datos como referencia catastral, dirección, metros cuadrados, tipo y múltiples propietarios asociados. | ✅ | ✅ |  |
| RF12. Gestión de Propietarios | Registro de propietarios con datos de contacto, asociación a inmuebles y acceso para consultar sus propiedades y crear incidencias. | ✅ | ✅ |  |
| RF13. Gestión de Incidencias | Creación y gestión de incidencias asociadas a inmuebles, con título, descripción, prioridad, estados y trazabilidad completa del historial. | ✅ | ⬜ / ✅ / ❌ |  |
| RF14. Asignación de Proveedores | Asignación de proveedores a incidencias, permitiendo múltiples incidencias por proveedor y múltiples actuaciones por incidencia. | ✅ | ⬜ / ✅ / ❌ |  |
| RF15. Gestión de Actuaciones | Registro de actuaciones realizadas por proveedores, incluyendo descripción, fecha de realización y coste, y actualización del estado de la incidencia. | ✅ | ⬜ / ✅ / ❌ |  |
| RF16. Gestión de Documentos | Adjuntar documentos (fotos, facturas, presupuestos) a incidencias, con almacenamiento seguro y control de acceso por permisos. | ✅ | ⬜ / ✅ / ❌ |  |
| RF17. Sistema de Mensajería | Mensajería interna entre administradores, propietarios y proveedores, vinculada a incidencias específicas. | ✅ | ⬜ / ✅ / ❌ |  |
| RF18. Generación de Informes | Generación de informes de costes por comunidad, período, proveedor y análisis de incidencias (tiempos medios, tipos frecuentes, etc.). | ⬜ | ⬜ / ✅ / ❌ |  |
| RF19. Gestión de Proveedores | Gestión de catálogo de proveedores con información de contacto, especialidades y estado (activo/inactivo). | ✅ | ⬜ / ✅ / ❌ |  |
| **COMUNES** |  |  |  |  |
| RF20. Autenticación y Autorización | Sistema de autenticación segura mediante JWT, con diferentes roles y permisos granulares por módulo. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF21. Gestión de Usuarios | Gestión de usuarios por parte de super administradores: creación, edición, eliminación, desactivación y asignación de roles. | ✅ | ⬜ / ✅ / ❌ |  |
| RF22. Notificaciones | Envío de notificaciones automáticas (email, push) ante eventos relevantes como incidencias, cambios de estado o mantenimientos próximos. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF23. Búsqueda y Filtrado | Búsqueda y filtrado avanzado en incidencias, pedidos, rutas, vehículos y otras entidades por múltiples criterios. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF24. Exportación de Datos | Exportación de informes y listados a formatos estándar como PDF, Excel y CSV. | ⬜ | ⬜ / ✅ / ❌ |  |
| RF25. Aplicación Móvil Android | App móvil nativa Android en Kotlin con autenticación JWT, sincronización online/offline, integración con Google Maps y soporte desde Android 8.0. | ⬜ | ⬜ / ✅ / ❌ |  |

### Requisitos no funcionales

| Nº y nombre de requisito | Explicación | Desarrollado | Revisado | Observaciones |
| --- | --- | --- | --- | --- |
| RNF1. Tiempo de Respuesta | El sistema debe responder a las peticiones del usuario en menos de 2 segundos en el 95% de los casos, incluso con 100 usuarios concurrentes. | ✅ | ✅ |  |
| RNF2. Disponibilidad | El sistema debe tener una disponibilidad del 99.5% (máximo 43 horas de inactividad no planificada al año). | ✅ | ✅ | |
| RNF3. Escalabilidad | El sistema debe poder escalar horizontalmente para soportar el crecimiento de usuarios y datos sin requerir cambios arquitectónicos mayores. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF4. Autenticación Segura | Las contraseñas deben almacenarse mediante hash seguro (bcrypt o similar) y nunca en texto plano. Debe implementarse protección contra ataques de fuerza bruta. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF5. Autorización Granular | El sistema debe implementar control de acceso basado en roles (RBAC) que restrinja las funcionalidades según el perfil del usuario. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF6. Protección de Datos | El sistema debe cumplir con el Reglamento General de Protección de Datos (RGPD), implementando medidas técnicas y organizativas adecuadas. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF7. Comunicación Segura | Todas las comunicaciones entre cliente y servidor deben realizarse mediante HTTPS/TLS para garantizar la confidencialidad de los datos. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF8. Validación de Entrada | El sistema debe validar y sanitizar todas las entradas del usuario para prevenir inyecciones SQL, XSS y otros ataques comunes. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF9. Interfaz Intuitiva | La interfaz web debe ser intuitiva y fácil de usar, siguiendo principios de diseño UX/UI modernos y con tiempo de aprendizaje mínimo. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF10. Diseño Responsive | La interfaz web debe adaptarse correctamente a diferentes tamaños de pantalla (ordenadores, tablets, smartphones). | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF11. Accesibilidad | El sistema debe cumplir con las pautas de accesibilidad WCAG 2.1 nivel AA para garantizar el acceso a usuarios con discapacidades. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF12. Código Limpio y Documentado | El código fuente debe estar bien documentado, seguir estándares de codificación y ser fácilmente mantenible por otros desarrolladores. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF13. Arquitectura Modular | El sistema debe estar diseñado con arquitectura modular que permita modificar o añadir funcionalidades sin afectar otras partes del sistema. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF14. Versionado | El sistema debe utilizar control de versiones (Git) y mantener un historial completo de cambios. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF15. Navegadores Soportados | La aplicación web debe funcionar correctamente en los navegadores más utilizados (Chrome, Firefox, Safari, Edge) en sus versiones actuales y anteriores. | ✅ | ✅ |  |
| RNF16. Plataforma Móvil | La aplicación móvil Android debe funcionar en dispositivos Android con versión 8.0 (API 26) o superior, adaptándose a diferentes tamaños de pantalla y resoluciones y siguiendo Material Design. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF17. Rendimiento Móvil | La aplicación móvil debe cargar las pantallas principales en menos de 2 segundos y responder a las interacciones del usuario en menos de 100 ms. | ⬜ | ⬜ / ✅ / ❌ |  |
| RNF18. Optimización Móvil | La aplicación móvil debe optimizar el uso de batería y datos (GPS solo cuando sea necesario, compresión de imágenes, sincronización incremental, opción de solo WiFi). | ⬜ | ⬜ / ✅ / ❌ |  |


