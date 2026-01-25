# Fyntra Mobile App

Aplicación Android desarrollada en Kotlin con Jetpack Compose para el sistema de gestión Fyntra.

## Estructura del Proyecto

```
app/src/main/java/com/tomoko/fyntra/
├── data/
│   ├── api/              # Servicios API con Retrofit
│   ├── models/           # Modelos de datos
│   ├── repository/       # Repositorios
│   └── local/            # Almacenamiento local (DataStore)
├── ui/
│   ├── screens/          # Pantallas de la aplicación
│   │   ├── login/        # Pantalla de login
│   │   ├── conductor/    # Pantallas para conductores
│   │   ├── propietario/  # Pantallas para propietarios
│   │   └── proveedor/    # Pantallas para proveedores
│   ├── components/       # Componentes reutilizables
│   ├── navigation/       # Navegación de la app
│   └── theme/            # Tema y estilos
└── util/                 # Utilidades

```

## Funcionalidades por Rol

### Conductor
- Ver rutas asignadas
- Iniciar/finalizar rutas
- Confirmar entregas (con firma y foto)
- Reportar incidencias en ruta

### Propietario
- Ver incidencias de sus inmuebles
- Crear nuevas incidencias
- Subir documentos a incidencias
- Chatear sobre incidencias

### Proveedor
- Ver incidencias asignadas
- Actualizar estado de incidencias
- Añadir actuaciones
- Subir documentos
- Chatear sobre incidencias

## Dependencias Principales

- **Retrofit**: Cliente HTTP para llamadas API
- **Jetpack Compose**: UI declarativa
- **Navigation Compose**: Navegación entre pantallas
- **DataStore**: Almacenamiento local de preferencias
- **Coil**: Carga de imágenes
- **CameraX**: Captura de fotos
- **ViewModel**: Gestión de estado

## Configuración

La URL base del API está configurada en `RetrofitModule.kt`:
- Emulador: `http://10.0.2.2:8000/api/`
- Dispositivo físico: `http://[IP_LOCAL]:8000/api/`

## Estado Actual

✅ Estructura básica creada
✅ Pantalla de login implementada
✅ Pantallas principales por rol creadas
⏳ Pantallas de detalle en desarrollo
⏳ Funcionalidad de firma y foto pendiente
⏳ Chat y documentos pendientes

