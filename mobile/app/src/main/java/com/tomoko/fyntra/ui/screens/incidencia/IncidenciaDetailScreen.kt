package com.tomoko.fyntra.ui.screens.incidencia

import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import android.net.Uri
import android.content.Intent
import android.os.Environment
import android.app.DatePickerDialog
import androidx.core.content.FileProvider
import android.Manifest
import android.content.pm.PackageManager
import androidx.core.content.ContextCompat
import java.text.SimpleDateFormat
import java.util.Locale
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.ResponseBody
import java.io.File
import java.io.FileOutputStream
import java.util.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Build
import androidx.compose.material.icons.filled.Edit
import androidx.compose.foundation.clickable
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.TextButton
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.models.IncidenciaUpdate
import com.tomoko.fyntra.data.repository.AuthRepository
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IncidenciaDetailScreen(
    incidenciaId: Int,
    userRol: String,
    navController: NavController,
    authRepository: AuthRepository,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    userId: Int? = null,
    initialTab: Int = 0
) {
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var selectedTab by remember { mutableStateOf(initialTab) }
    var showDeleteDialog by remember { mutableStateOf(false) }
    var isDeleting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
    val incidencia by incidenciaRepository
        .observeIncidenciaById(incidenciaId)
        .collectAsState(initial = null)

    // Verificar si puede eliminar: admin o propietario que creó la incidencia
    val puedeEliminar = remember(incidencia, userRol, userId) {
        when {
            userRol in listOf("super_admin", "admin_fincas") -> true
            userRol == "propietario" && incidencia != null && userId != null -> {
                incidencia!!.creador_usuario_id == userId
            }
            else -> false
        }
    }
    
    // Verificar si puede editar: admin siempre, propietario solo si es el creador, proveedor NO puede editar
    val puedeEditar = remember(incidencia, userRol, userId) {
        when {
            userRol in listOf("super_admin", "admin_fincas") -> true
            userRol == "propietario" && incidencia != null && userId != null -> {
                incidencia!!.creador_usuario_id == userId
            }
            else -> false
        }
    }
    
    var mostrarEditarDialog by remember { mutableStateOf(false) }

    LaunchedEffect(incidenciaId) {
        isLoading = true
        try {
            // Upsert de detalle: asegura que Room tenga el registro aunque el listado no se haya cargado aún
            incidenciaRepository.getIncidenciaById(incidenciaId)
        } catch (e: Exception) {
            error = e.message
        } finally {
            isLoading = false
        }
    }

    // Manejar botón físico de "atrás": si estamos en una pestaña distinta de Detalles,
    // primero volvemos a Detalles; si ya estamos en Detalles, volvemos al listado.
    BackHandler {
        if (selectedTab != 0) {
            selectedTab = 0
        } else {
            navController.popBackStack()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(incidencia?.titulo ?: "Incidencia", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(
                        onClick = {
                            if (selectedTab != 0) {
                                selectedTab = 0
                            } else {
                                navController.popBackStack()
                            }
                        }
                    ) {
                        Icon(
                            imageVector = Icons.AutoMirrored.Filled.ArrowBack,
                            contentDescription = "Volver"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                actions = {
                    if (puedeEditar) {
                        IconButton(
                            onClick = { mostrarEditarDialog = true }
                        ) {
                            Icon(
                                imageVector = Icons.Default.Edit,
                                contentDescription = "Editar"
                            )
                        }
                    }
                    if (puedeEliminar) {
                        IconButton(
                            onClick = { showDeleteDialog = true },
                            enabled = !isDeleting
                        ) {
                            Icon(
                                imageVector = Icons.Default.Delete,
                                contentDescription = "Eliminar"
                            )
                        }
                    }
                }
            )
        }
    ) { paddingValues ->
        if (isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (error != null) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                Text(error!!, color = MaterialTheme.colorScheme.error)
            }
        } else if (incidencia != null) {
            Box(modifier = Modifier.padding(paddingValues)) {
                val context = androidx.compose.ui.platform.LocalContext.current
                when (selectedTab) {
                    0 -> DetallesTab(
                        incidencia = incidencia!!,
                        userRol = userRol,
                        authRepository = authRepository,
                        incidenciaRepository = incidenciaRepository,
                        selectedTab = { selectedTab = it },
                        onRefreshIncidencia = {
                            scope.launch {
                                isLoading = true
                                try {
                                    incidenciaRepository.refreshIncidenciasFromServer(userRol = userRol)
                                } catch (_: Exception) {
                                    // Ignorar, seguimos con caché local
                                } finally {
                                    isLoading = false
                                }
                            }
                        }
                    )
                    1 -> HistorialTab(incidencia!!)
                    2 -> DocumentosTab(incidencia!!, userRol, authRepository, incidenciaRepository, userId, context)
                    3 -> ChatTab(incidencia!!, incidenciaRepository, userId)
                    4 -> if (userRol == "proveedor") ActuacionesTab(
                        incidencia = incidencia!!,
                        incidenciaRepository = incidenciaRepository,
                        onActuacionCreada = {
                            // Refrescar la incidencia después de crear una actuación
                            scope.launch {
                                try {
                                    incidenciaRepository.refreshIncidenciasFromServer(userRol = userRol)
                                } catch (_: Exception) {
                                    // Ignorar errores de red aquí
                                }
                            }
                        }
                    )
                }
            }
        }
        
        // Dialog de confirmación de eliminación
        if (showDeleteDialog) {
            AlertDialog(
                onDismissRequest = { if (!isDeleting) showDeleteDialog = false },
                title = { Text("Eliminar Incidencia") },
                text = { Text("¿Está seguro de que desea eliminar esta incidencia? Esta acción no se puede deshacer.") },
                confirmButton = {
                    TextButton(
                        onClick = {
                            scope.launch {
                                isDeleting = true
                                try {
                                    val result = incidenciaRepository.deleteIncidencia(incidenciaId)
                                    result.onSuccess {
                                        navController.popBackStack()
                                    }.onFailure { e ->
                                        error = e.message ?: "Error al eliminar la incidencia"
                                        showDeleteDialog = false
                                    }
                                } finally {
                                    isDeleting = false
                                }
                            }
                        },
                        enabled = !isDeleting
                    ) {
                        if (isDeleting) {
                            CircularProgressIndicator(modifier = Modifier.size(16.dp))
                        } else {
                            Text("Eliminar")
                        }
                    }
                },
                dismissButton = {
                    TextButton(
                        onClick = { showDeleteDialog = false },
                        enabled = !isDeleting
                    ) {
                        Text("Cancelar")
                    }
                }
            )
        }
        
        // Dialog de edición
        if (mostrarEditarDialog && incidencia != null) {
            EditarIncidenciaDialog(
                incidencia = incidencia!!,
                userRol = userRol,
                incidenciaRepository = incidenciaRepository,
                authRepository = authRepository,
                onDismiss = { mostrarEditarDialog = false },
                onSuccess = {
                    mostrarEditarDialog = false
                    // Recargar la incidencia
                    scope.launch {
                        isLoading = true
                        try {
                            // Refrescar en Room (sin reasignar el estado local aquí)
                            incidenciaRepository.getIncidenciaById(incidenciaId)
                        } catch (e: Exception) {
                            error = e.message
                        } finally {
                            isLoading = false
                        }
                    }
                }
            )
        }
    }
}

@Composable
fun DetallesTab(
    incidencia: Incidencia,
    userRol: String,
    authRepository: AuthRepository,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    selectedTab: (Int) -> Unit = {},
    onRefreshIncidencia: () -> Unit = {}
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        Card(modifier = Modifier.fillMaxWidth()) {
            Column(
                modifier = Modifier.padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text("Título", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(incidencia.titulo, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text("Descripción", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(incidencia.descripcion ?: "Sin descripción", fontSize = 14.sp)
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Column {
                        Text("Estado", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(getEstadoLabel(incidencia.estado), fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                    Column {
                        Text("Prioridad", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(getPrioridadLabel(incidencia.prioridad), fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text("Inmueble", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text("${incidencia.inmueble?.referencia ?: "N/A"} - ${incidencia.inmueble?.direccion ?: ""}", fontSize = 14.sp)
                
                Spacer(modifier = Modifier.height(8.dp))
                
                // Proveedor si está asignado
                if (incidencia.proveedor != null) {
                    Text("Proveedor", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text("${incidencia.proveedor.nombre}${incidencia.proveedor.especialidad?.let { " - $it" } ?: ""}", fontSize = 14.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                }
                
                Text("Fecha de creación", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(formatearFechaSolo(incidencia.fecha_alta), fontSize = 14.sp)
                
                if (incidencia.estado == "resuelta" || incidencia.estado == "cerrada") {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Fecha de cierre", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Text(
                        if (!incidencia.fecha_cierre.isNullOrBlank()) formatearFechaSolo(incidencia.fecha_cierre) else "No hay fecha de cierre",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }

        // Botones de acción rápida
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                Text("Acciones", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Botón Historial
                    Button(
                        onClick = { selectedTab(1) },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("📋 Historial", fontSize = 12.sp)
                    }
                    
                    // Botón Documentos
                    Button(
                        onClick = { selectedTab(2) },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("📎 Adjuntos", fontSize = 12.sp)
                    }
                }
                
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Botón Chat
                    Button(
                        onClick = { selectedTab(3) },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("💬 Chat", fontSize = 12.sp)
                    }
                    
                    // Botón Actuaciones (solo para proveedores)
                    if (userRol == "proveedor") {
                        Button(
                            onClick = { selectedTab(4) },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("🔧 Actuaciones", fontSize = 12.sp)
                        }
                    }
                }
            }
        }
        
        if (userRol == "proveedor") {
            CambiarEstadoCard(
                incidencia = incidencia,
                incidenciaRepository = incidenciaRepository,
                onEstadoCambiado = onRefreshIncidencia
            )
        }
    }
}

@Composable
fun DocumentosTab(
    incidencia: Incidencia,
    userRol: String,
    authRepository: AuthRepository,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    userId: Int?,
    context: android.content.Context
) {
    val documentos by incidenciaRepository
        .getDocumentos(incidencia.id)
        .collectAsState(initial = emptyList())
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showUploadDialog by remember { mutableStateOf(false) }
    var nombreDocumento by remember { mutableStateOf("") }
    var archivoSeleccionado by remember { mutableStateOf<Uri?>(null) }
    var fotoCapturada by remember { mutableStateOf<Uri?>(null) }
    var archivoFoto by remember { mutableStateOf<File?>(null) }
    var isUploading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
    // Variable para mantener referencia al archivo de foto actual
    var archivoFotoActual by remember { mutableStateOf<File?>(null) }

    // Launcher para seleccionar archivos
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        archivoSeleccionado = uri
        fotoCapturada = null
        archivoFoto = null
        archivoFotoActual = null
    }

    // Launcher para tomar foto
    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success: Boolean ->
        if (success && archivoFotoActual != null && archivoFotoActual!!.exists()) {
            val photoUri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                archivoFotoActual!!
            )
            fotoCapturada = photoUri
            archivoFoto = archivoFotoActual
            archivoSeleccionado = null
        } else {
            error = "Error al capturar la foto"
            archivoFotoActual = null
        }
    }

    // Launcher para permisos de cámara
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted: Boolean ->
        if (isGranted) {
            // Crear nuevo archivo para la foto en cacheDir (configurado en FileProvider)
            val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val imageFileName = "JPEG_${timeStamp}_"
            val nuevoArchivo = File.createTempFile(
                imageFileName,
                ".jpg",
                context.cacheDir
            )
            archivoFotoActual = nuevoArchivo
            
            val photoUri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                nuevoArchivo
            )
            cameraLauncher.launch(photoUri)
        } else {
            error = "Se necesita permiso de cámara para tomar fotos"
        }
    }

    // Función para tomar foto
    fun tomarFoto() {
        when {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED -> {
                // Crear nuevo archivo para la foto en cacheDir (configurado en FileProvider)
                val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
                val imageFileName = "JPEG_${timeStamp}_"
                val nuevoArchivo = File.createTempFile(
                    imageFileName,
                    ".jpg",
                    context.cacheDir
                )
                archivoFotoActual = nuevoArchivo
                
                val photoUri = FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.fileprovider",
                    nuevoArchivo
                )
                cameraLauncher.launch(photoUri)
            }
            else -> {
                // Solicitar permiso
                permissionLauncher.launch(Manifest.permission.CAMERA)
            }
        }
    }

    fun cargarDocumentos() {
        scope.launch {
            isLoading = true
            try {
                incidenciaRepository.refreshDocumentosFromServer(incidencia.id)
            } catch (e: Exception) {
                error = e.message
            } finally {
                isLoading = false
            }
        }
    }

    fun eliminarDocumento(documentoId: Int) {
        scope.launch {
            try {
                val response = authRepository.getApiServiceInstance().eliminarDocumento(documentoId)
                if (response.isSuccessful) {
                    cargarDocumentos()
                } else {
                    error = "Error al eliminar documento"
                }
            } catch (e: Exception) {
                error = e.message
            }
        }
    }

    fun subirDocumento() {
        if (nombreDocumento.isBlank()) {
            error = "Por favor, ingrese un nombre para el documento"
            return
        }
        if (archivoSeleccionado == null && archivoFoto == null) {
            error = "Por favor, seleccione un archivo o tome una foto"
            return
        }

        scope.launch {
            isUploading = true
            var tempFile: File? = null
            var fileName: String = ""
            var mimeType: String = "application/octet-stream"
            try {
                if (archivoFoto != null) {
                    // Usar la foto capturada
                    tempFile = archivoFoto!!
                    fileName = "${nombreDocumento.replace(" ", "_")}_${SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())}.jpg"
                    mimeType = "image/jpeg"
                } else {
                    // Usar el archivo seleccionado
                    val uri = archivoSeleccionado!!
                    val inputStream = context?.contentResolver?.openInputStream(uri)
                    if (inputStream == null) {
                        error = "Error al leer el archivo"
                        isUploading = false
                        return@launch
                    }

                    // Crear archivo temporal
                    tempFile = File.createTempFile("upload_", null, context?.cacheDir)
                    tempFile!!.outputStream().use { output ->
                        inputStream.copyTo(output)
                    }

                    // Obtener el nombre del archivo original si es posible
                    fileName = try {
                        context?.contentResolver?.query(uri, null, null, null, null)?.use { cursor ->
                            val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                            if (cursor.moveToFirst() && nameIndex >= 0) {
                                cursor.getString(nameIndex)
                            } else {
                                tempFile!!.name
                            }
                        } ?: tempFile!!.name
                    } catch (e: Exception) {
                        tempFile!!.name
                    }

                    // Obtener el tipo MIME del archivo
                    mimeType = try {
                        context?.contentResolver?.getType(uri) ?: "application/octet-stream"
                    } catch (e: Exception) {
                        "application/octet-stream"
                    }
                }

                // Crear RequestBody para el archivo (el backend espera "archivo")
                val fileForUpload = tempFile ?: throw IllegalStateException("Archivo no disponible")
                val requestFile = fileForUpload.asRequestBody(mimeType.toMediaTypeOrNull())
                val filePart = MultipartBody.Part.createFormData("archivo", fileName, requestFile)

                // Crear RequestBody para el nombre y incidencia_id (usando Form para multipart)
                val nombrePart = nombreDocumento.toRequestBody("text/plain".toMediaTypeOrNull())
                val incidenciaIdPart = incidencia.id.toString().toRequestBody("text/plain".toMediaTypeOrNull())

                val result = incidenciaRepository.uploadDocumentoOfflineFirst(
                    incidenciaId = incidencia.id,
                    nombre = nombreDocumento,
                    filePath = fileForUpload.absolutePath,
                    mimeType = mimeType,
                    fileName = fileName
                )

                if (result.isSuccess) {
                    nombreDocumento = ""
                    archivoSeleccionado = null
                    fotoCapturada = null
                    archivoFoto = null
                    archivoFotoActual = null
                    showUploadDialog = false
                    cargarDocumentos()
                } else {
                    error = result.exceptionOrNull()?.message ?: "Error al subir documento"
                }

                // Eliminar archivo temporal solo si no es la foto (la foto se eliminará después si es necesario)
                if (archivoFoto == null || fileForUpload != archivoFoto) {
                    fileForUpload.delete()
                } else {
                    // Si es la foto, eliminarla después de subirla
                    try {
                        fileForUpload.delete()
                    } catch (e: Exception) {
                        // Ignorar error al eliminar
                    }
                }
            } catch (e: Exception) {
                // Sin conexión o Solo WiFi sin WiFi: guardar local y encolar
                val fileForQueue = tempFile ?: archivoFoto
                if (fileForQueue != null) {
                    incidenciaRepository.uploadDocumentoOfflineFirst(
                        incidenciaId = incidencia.id,
                        nombre = nombreDocumento,
                        filePath = fileForQueue.absolutePath,
                        mimeType = mimeType.ifBlank { "application/octet-stream" },
                        fileName = if (fileName.isNotBlank()) fileName else fileForQueue.name
                    )
                } else {
                    error = "Error al subir documento: ${e.message}"
                }
                nombreDocumento = ""
                archivoSeleccionado = null
                fotoCapturada = null
                archivoFoto = null
                archivoFotoActual = null
                showUploadDialog = false
            } finally {
                isUploading = false
            }
        }
    }

    LaunchedEffect(incidencia.id) {
        cargarDocumentos()
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Botón para subir documento (solo admin, propietario o proveedor asignado)
        if (userRol in listOf("super_admin", "admin_fincas", "propietario", "proveedor")) {
            Button(
                onClick = { showUploadDialog = true },
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Subir Documento")
            }
        }

        if (isLoading) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (error != null) {
            Text(error!!, color = MaterialTheme.colorScheme.error)
        } else if (documentos.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                Text("No hay documentos")
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                items(documentos) { doc ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(
                                text = doc.nombre,
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                            Text(
                                text = "Subido por: ${doc.subido_por ?: "N/A"}",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Text(
                                text = "Fecha: ${formatearFecha(doc.creado_en)}",
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            if (doc.tamano != null) {
                                Text(
                                    text = "Tamaño: ${doc.tamano / 1024} KB",
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Button(
                                    onClick = {
                                        scope.launch {
                                            try {
                                                val authDataStore = com.tomoko.fyntra.data.local.AuthDataStore(context)
                                                val token = authDataStore.getToken()
                                                if (token != null) {
                                                    val response = authRepository.getApiServiceInstance().downloadDocumento(doc.id, token)
                                                    if (response.isSuccessful) {
                                                        val responseBody = response.body()
                                                        if (responseBody != null) {
                                                            descargarYabrirDocumento(
                                                                context = context,
                                                                responseBody = responseBody,
                                                                nombreArchivo = doc.nombre_archivo ?: doc.nombre,
                                                                tipoArchivo = doc.tipo_archivo ?: "application/octet-stream"
                                                            )
                                                        } else {
                                                            error = "Error: respuesta vacía"
                                                        }
                                                    } else {
                                                        error = "Error al descargar documento: ${response.message()}"
                                                    }
                                                } else {
                                                    error = "No se pudo obtener el token de autenticación"
                                                }
                                            } catch (e: Exception) {
                                                error = e.message ?: "Error al descargar documento"
                                            }
                                        }
                                    }
                                ) {
                                    Text("Ver/Descargar")
                                }
                                // Solo el propietario del documento puede eliminarlo
                                if (userId != null && doc.usuario_id == userId) {
                                    TextButton(
                                        onClick = { eliminarDocumento(doc.id) }
                                    ) {
                                        Text("Eliminar", color = MaterialTheme.colorScheme.error)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // Dialog para subir documento
    if (showUploadDialog) {
        AlertDialog(
            onDismissRequest = { 
                if (!isUploading) {
                    showUploadDialog = false
                    nombreDocumento = ""
                    archivoSeleccionado = null
                    fotoCapturada = null
                    archivoFoto = null
                    archivoFotoActual = null
                    error = null
                }
            },
            title = { Text("Subir Documento") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = nombreDocumento,
                        onValueChange = { nombreDocumento = it },
                        label = { Text("Nombre del documento") },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isUploading
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Button(
                            onClick = { filePickerLauncher.launch("*/*") },
                            modifier = Modifier.weight(1f),
                            enabled = !isUploading
                        ) {
                            Text(if (archivoSeleccionado != null) "Archivo ✓" else "Seleccionar archivo", fontSize = 12.sp)
                        }
                        Button(
                            onClick = { tomarFoto() },
                            modifier = Modifier.weight(1f),
                            enabled = !isUploading
                        ) {
                            Text(if (fotoCapturada != null) "Foto ✓" else "📷 Tomar foto", fontSize = 12.sp)
                        }
                    }
                    if (archivoSeleccionado != null) {
                        Text(
                            text = "Archivo seleccionado",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                    if (fotoCapturada != null) {
                        Text(
                            text = "Foto capturada",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = { subirDocumento() },
                    enabled = !isUploading && nombreDocumento.isNotBlank() && (archivoSeleccionado != null || archivoFoto != null)
                ) {
                    if (isUploading) {
                        CircularProgressIndicator(modifier = Modifier.size(16.dp))
                    } else {
                        Text("Subir")
                    }
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { 
                        showUploadDialog = false
                        nombreDocumento = ""
                        archivoSeleccionado = null
                        fotoCapturada = null
                        archivoFoto = null
                        archivoFotoActual = null
                        error = null
                    },
                    enabled = !isUploading
                ) {
                    Text("Cancelar")
                }
            }
        )
    }
}

fun formatearFecha(fechaString: String?): String {
    if (fechaString == null) return "N/A"
    return try {
        // Intentar parsear diferentes formatos de fecha
        val formatos = listOf(
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
            "yyyy-MM-dd'T'HH:mm:ss",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd"
        )
        var fecha: Date? = null
        for (formato in formatos) {
            try {
                val sdf = SimpleDateFormat(formato, Locale("es", "ES"))
                sdf.timeZone = TimeZone.getTimeZone("UTC")
                fecha = sdf.parse(fechaString)
                if (fecha != null) break
            } catch (e: Exception) {
                continue
            }
        }
        if (fecha != null) {
            val formatoSalida = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale("es", "ES"))
            formatoSalida.format(fecha)
        } else {
            fechaString
        }
    } catch (e: Exception) {
        fechaString
    }
}

fun formatearFechaSolo(fechaString: String?): String {
    if (fechaString == null) return "N/A"
    return try {
        // Intentar parsear diferentes formatos de fecha
        val formatos = listOf(
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
            "yyyy-MM-dd'T'HH:mm:ss",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd"
        )
        var fecha: Date? = null
        for (formato in formatos) {
            try {
                val sdf = SimpleDateFormat(formato, Locale("es", "ES"))
                sdf.timeZone = TimeZone.getTimeZone("UTC")
                fecha = sdf.parse(fechaString)
                if (fecha != null) break
            } catch (e: Exception) {
                continue
            }
        }
        if (fecha != null) {
            val formatoSalida = SimpleDateFormat("dd/MM/yyyy", Locale("es", "ES"))
            formatoSalida.format(fecha)
        } else {
            fechaString
        }
    } catch (e: Exception) {
        fechaString
    }
}

@Composable
fun HistorialTab(
    incidencia: Incidencia
) {
    val historial = remember(incidencia.historial) {
        (incidencia.historial ?: emptyList()).sortedByDescending { item ->
            try {
                val formatos = listOf(
                    "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
                    "yyyy-MM-dd'T'HH:mm:ss",
                    "yyyy-MM-dd HH:mm:ss",
                    "yyyy-MM-dd"
                )
                var fecha: Date? = null
                for (formato in formatos) {
                    try {
                        val sdf = SimpleDateFormat(formato, Locale("es", "ES"))
                        sdf.timeZone = TimeZone.getTimeZone("UTC")
                        fecha = sdf.parse(item.fecha)
                        if (fecha != null) break
                    } catch (e: Exception) {
                        continue
                    }
                }
                fecha?.time ?: 0L
            } catch (e: Exception) {
                0L
            }
        }
    }
    
    if (historial.isEmpty()) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            contentAlignment = androidx.compose.ui.Alignment.Center
        ) {
            Text("No hay historial disponible")
        }
    } else {
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(historial) { item ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text(
                                text = if (item.estado_anterior != null) {
                                    "Estado: ${getEstadoLabel(item.estado_anterior)} → ${getEstadoLabel(item.estado_nuevo)}"
                                } else {
                                    // Primer estado registrado: solo mostrar el estado nuevo (ej. "Abierta")
                                    "Estado: ${getEstadoLabel(item.estado_nuevo)}"
                                },
                                fontWeight = FontWeight.Bold,
                                fontSize = 16.sp
                            )
                            Text(
                                text = formatearFecha(item.fecha),
                                fontSize = 12.sp,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        if (!item.comentario.isNullOrBlank()) {
                            Text(
                                text = item.comentario,
                                fontSize = 14.sp
                            )
                        }
                        Text(
                            text = "Usuario: ${item.usuario_nombre ?: "N/A"}",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun ChatTab(
    incidencia: Incidencia,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    userId: Int?
) {
    val mensajes by incidenciaRepository
        .getMensajes(incidencia.id)
        .collectAsState(initial = emptyList())
    var nuevoMensaje by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(incidencia.id) {
        isLoading = true
        try {
            incidenciaRepository.refreshMensajesFromServer(incidencia.id)
        } catch (_: Exception) {
            // Sin conexión o solo WiFi sin WiFi: usar local
        } finally {
            isLoading = false
        }
    }

    fun enviarMensaje() {
        if (nuevoMensaje.isBlank()) return
        
        scope.launch {
            try {
                val result = incidenciaRepository.enviarMensajeOfflineFirst(incidencia.id, nuevoMensaje)
                result.onSuccess { nuevoMensaje = "" }
                    .onFailure { e -> error = e.message ?: "Error al enviar mensaje" }
            } catch (e: Exception) {
                error = e.message
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        if (error != null) {
            Text(
                text = error!!,
                color = MaterialTheme.colorScheme.error,
                fontSize = 12.sp
            )
        }

        // Lista de mensajes
        if (isLoading) {
            Box(
                modifier = Modifier.weight(1f),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (mensajes.isEmpty()) {
            Box(
                modifier = Modifier.weight(1f),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                Text("No hay mensajes")
            }
        } else {
            LazyColumn(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(mensajes) { mensaje ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = if (mensaje.usuario_id == userId) {
                                MaterialTheme.colorScheme.primaryContainer
                            } else {
                                MaterialTheme.colorScheme.surface
                            }
                        )
                    ) {
                        Column(
                            modifier = Modifier.padding(12.dp),
                            verticalArrangement = Arrangement.spacedBy(4.dp)
                        ) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = mensaje.usuario_nombre + if (mensaje.id < 0) " (pendiente)" else "",
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 14.sp
                                )
                                Text(
                                    text = formatearFecha(mensaje.creado_en),
                                    fontSize = 10.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                            Text(
                                text = mensaje.contenido,
                                fontSize = 14.sp
                            )
                        }
                    }
                }
            }
        }

        // Campo para escribir y enviar mensaje
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedTextField(
                value = nuevoMensaje,
                onValueChange = { nuevoMensaje = it },
                modifier = Modifier.weight(1f),
                placeholder = { Text("Escribe un mensaje...") },
                maxLines = 3
            )
            Button(
                onClick = { enviarMensaje() },
                enabled = nuevoMensaje.isNotBlank()
            ) {
                Text("Enviar")
            }
        }
    }
}

@Composable
fun ActuacionesTab(
    incidencia: Incidencia,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    onActuacionCreada: () -> Unit = {}
) {
    val actuaciones by incidenciaRepository
        .getActuaciones(incidencia.id)
        .collectAsState(initial = emptyList())
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var mostrarFormulario by remember { mutableStateOf(false) }
    var descripcion by remember { mutableStateOf("") }
    var fecha by remember { mutableStateOf("") }
    var coste by remember { mutableStateOf("") }
    var isSubmitting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
    fun crearActuacion() {
        if (descripcion.isBlank() || fecha.isBlank()) {
            error = "Por favor completa todos los campos obligatorios"
            return
        }
        
        scope.launch {
            isSubmitting = true
            error = null
            try {
                val costeValue = if (coste.isNotBlank()) {
                    try {
                        coste.toDouble()
                    } catch (e: Exception) {
                        null
                    }
                } else null
                
                // Convertir fecha a formato ISO si no lo está
                val fechaISO = try {
                    // Si ya está en formato ISO, usarla directamente
                    if (fecha.matches(Regex("\\d{4}-\\d{2}-\\d{2}"))) {
                        "${fecha}T00:00:00"
                    } else {
                        fecha
                    }
                } catch (e: Exception) {
                    fecha
                }
                
                val actuacionData = com.tomoko.fyntra.data.models.ActuacionCreate(
                    incidencia_id = incidencia.id,
                    descripcion = descripcion,
                    fecha = fechaISO,
                    coste = costeValue
                )

                val result = incidenciaRepository.crearActuacionOfflineFirst(actuacionData)
                if (result.isSuccess) {
                    descripcion = ""
                    fecha = ""
                    coste = ""
                    mostrarFormulario = false
                    error = null
                    onActuacionCreada() // Notificar que se creó una actuación
                } else {
                    error = result.exceptionOrNull()?.message ?: "Error al crear actuación"
                }
            } catch (e: Exception) {
                error = e.message ?: "Error al crear actuación"
            } finally {
                isSubmitting = false
            }
        }
    }
    
    LaunchedEffect(incidencia.id) {
        isLoading = true
        try {
            incidenciaRepository.refreshActuacionesFromServer(incidencia.id)
        } catch (_: Exception) {
            // usar local
        } finally {
            isLoading = false
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Botón para crear actuación
        Button(
            onClick = { mostrarFormulario = true },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Nueva Actuación")
        }
        
        if (error != null) {
            Text(
                text = error!!,
                color = MaterialTheme.colorScheme.error,
                fontSize = 12.sp
            )
        }
        
        // Formulario de nueva actuación
        if (mostrarFormulario) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Text(
                        text = "Nueva Actuación",
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                    
                    OutlinedTextField(
                        value = descripcion,
                        onValueChange = { descripcion = it },
                        label = { Text("Descripción *") },
                        modifier = Modifier.fillMaxWidth(),
                        maxLines = 4,
                        enabled = !isSubmitting
                    )
                    
                    // Campo de fecha con DatePicker
                    val context = LocalContext.current
                    var fechaDisplay by remember { mutableStateOf("") }
                    var fechaSeleccionada by remember { mutableStateOf<Calendar?>(null) }
                    
                    // Inicializar con fecha de hoy
                    LaunchedEffect(Unit) {
                        val hoy = Calendar.getInstance()
                        fechaSeleccionada = hoy
                        val sdf = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
                        fechaDisplay = sdf.format(hoy.time)
                        val sdfISO = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                        fecha = sdfISO.format(hoy.time)
                    }
                    
                    // Actualizar fechaDisplay cuando cambia fechaSeleccionada
                    LaunchedEffect(fechaSeleccionada) {
                        fechaSeleccionada?.let { cal ->
                            val sdf = SimpleDateFormat("dd/MM/yyyy", Locale.getDefault())
                            fechaDisplay = sdf.format(cal.time)
                            val sdfISO = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
                            fecha = sdfISO.format(cal.time)
                        }
                    }
                    
                    OutlinedTextField(
                        value = fechaDisplay,
                        onValueChange = { },
                        label = { Text("Fecha * (dd/MM/yyyy)") },
                        modifier = Modifier
                            .fillMaxWidth()
                            .clickable {
                                val cal = fechaSeleccionada ?: Calendar.getInstance()
                                DatePickerDialog(
                                    context,
                                    { _, year, month, dayOfMonth ->
                                        val nuevaFecha = Calendar.getInstance().apply {
                                            set(year, month, dayOfMonth)
                                        }
                                        fechaSeleccionada = nuevaFecha
                                    },
                                    cal.get(Calendar.YEAR),
                                    cal.get(Calendar.MONTH),
                                    cal.get(Calendar.DAY_OF_MONTH)
                                ).show()
                            },
                        enabled = !isSubmitting,
                        readOnly = true,
                        placeholder = { Text("Seleccionar fecha") },
                        trailingIcon = {
                            IconButton(onClick = {
                                val cal = fechaSeleccionada ?: Calendar.getInstance()
                                DatePickerDialog(
                                    context,
                                    { _, year, month, dayOfMonth ->
                                        val nuevaFecha = Calendar.getInstance().apply {
                                            set(year, month, dayOfMonth)
                                        }
                                        fechaSeleccionada = nuevaFecha
                                    },
                                    cal.get(Calendar.YEAR),
                                    cal.get(Calendar.MONTH),
                                    cal.get(Calendar.DAY_OF_MONTH)
                                ).show()
                            }) {
                                Text("📅", fontSize = 20.sp)
                            }
                        }
                    )
                    
                    OutlinedTextField(
                        value = coste,
                        onValueChange = { coste = it },
                        label = { Text("Coste (opcional)") },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isSubmitting,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Decimal)
                    )
                    
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        TextButton(
                            onClick = {
                                mostrarFormulario = false
                                descripcion = ""
                                fecha = ""
                                coste = ""
                                error = null
                            },
                            enabled = !isSubmitting
                        ) {
                            Text("Cancelar")
                        }
                        Button(
                            onClick = { crearActuacion() },
                            enabled = !isSubmitting && descripcion.isNotBlank() && fecha.isNotBlank(),
                            modifier = Modifier.weight(1f)
                        ) {
                            if (isSubmitting) {
                                CircularProgressIndicator(modifier = Modifier.size(16.dp))
                            } else {
                                Text("Crear")
                            }
                        }
                    }
                }
            }
        }
        
        // Lista de actuaciones
        if (isLoading) {
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = androidx.compose.ui.Alignment.Center
    ) {
                CircularProgressIndicator()
            }
        } else if (actuaciones.isEmpty()) {
            Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = androidx.compose.ui.Alignment.Center
            ) {
                Text("No hay actuaciones registradas")
            }
        } else {
            LazyColumn(
                verticalArrangement = Arrangement.spacedBy(12.dp),
                modifier = Modifier.padding(bottom = 8.dp)
            ) {
                items(actuaciones) { actuacion ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Text(
                                text = actuacion.descripcion,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text(
                                    text = "Fecha: ${formatearFechaSolo(actuacion.fecha)}",
                                    fontSize = 12.sp,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                                if (actuacion.coste != null) {
                                    Text(
                                        text = "Coste: ${String.format("%.2f", actuacion.coste)} €",
                                        fontSize = 12.sp,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                        }
                    }
                }
                item {
                    val totalImporte = actuaciones.sumOf { it.coste ?: 0.0 }
                    Text(
                        text = "Total importe: ${String.format("%.2f", totalImporte)} €",
                        modifier = Modifier.padding(top = 8.dp),
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}


@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EditarIncidenciaDialog(
    incidencia: Incidencia,
    userRol: String,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    authRepository: AuthRepository,
    onDismiss: () -> Unit,
    onSuccess: () -> Unit
) {
    var titulo by remember { mutableStateOf(incidencia.titulo) }
    var descripcion by remember { mutableStateOf(incidencia.descripcion ?: "") }
    var prioridad by remember { mutableStateOf(incidencia.prioridad) }
    var estado by remember { mutableStateOf(incidencia.estado) }
    var proveedorId by remember { mutableStateOf<Int?>(incidencia.proveedor_id) }
    var comentarioCambio by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    
    var proveedores by remember { mutableStateOf<List<com.tomoko.fyntra.data.models.ProveedorSimple>>(emptyList()) }
    val scope = rememberCoroutineScope()
    val esAdmin = userRol in listOf("super_admin", "admin_fincas")
    val esProveedor = userRol == "proveedor"
    val puedeEditarEstado = esAdmin || esProveedor
    
    LaunchedEffect(Unit) {
        if (esAdmin) {
            // Cargar proveedores solo para admin
            scope.launch {
                try {
                    val response = authRepository.getApiServiceInstance().getProveedores(activo = true)
                    if (response.isSuccessful) {
                        proveedores = response.body() ?: emptyList()
                    }
                } catch (e: Exception) {
                    // Error al cargar proveedores, continuar sin ellos
                }
            }
        }
    }
    
    AlertDialog(
        onDismissRequest = { if (!isLoading) onDismiss() },
        title = { Text("Editar Incidencia") },
        text = {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                if (error != null) {
                    Text(
                        text = error!!,
                        color = MaterialTheme.colorScheme.error,
                        fontSize = 12.sp
                    )
                }
                
                OutlinedTextField(
                    value = titulo,
                    onValueChange = { titulo = it },
                    label = { Text("Título *") },
                    modifier = Modifier.fillMaxWidth(),
                    enabled = !isLoading
                )
                
                OutlinedTextField(
                    value = descripcion,
                    onValueChange = { descripcion = it },
                    label = { Text("Descripción *") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(100.dp),
                    maxLines = 4,
                    enabled = !isLoading
                )
                
                // Prioridad
                var expandedPrioridad by remember { mutableStateOf(false) }
                ExposedDropdownMenuBox(
                    expanded = expandedPrioridad,
                    onExpandedChange = { expandedPrioridad = !expandedPrioridad }
                ) {
                    OutlinedTextField(
                        value = prioridad,
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Prioridad *") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedPrioridad) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor(),
                        enabled = !isLoading
                    )
                    ExposedDropdownMenu(
                        expanded = expandedPrioridad,
                        onDismissRequest = { expandedPrioridad = false }
                    ) {
                        listOf("baja", "media", "alta", "urgente").forEach { prio ->
                            DropdownMenuItem(
                                text = { Text(prio.capitalize()) },
                                onClick = {
                                    prioridad = prio
                                    expandedPrioridad = false
                                }
                            )
                        }
                    }
                }
                
                // Estado para admin y proveedor
                if (puedeEditarEstado) {
                    var expandedEstado by remember { mutableStateOf(false) }
                    ExposedDropdownMenuBox(
                        expanded = expandedEstado,
                        onExpandedChange = { expandedEstado = !expandedEstado }
                    ) {
                        OutlinedTextField(
                            value = estado,
                            onValueChange = {},
                            readOnly = true,
                            label = { Text("Estado") },
                            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedEstado) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .menuAnchor(),
                            enabled = !isLoading
                        )
                        ExposedDropdownMenu(
                            expanded = expandedEstado,
                            onDismissRequest = { expandedEstado = false }
                        ) {
                            listOf("abierta", "asignada", "en_progreso", "resuelta", "cerrada").forEach { est ->
                                DropdownMenuItem(
                                    text = { Text(getEstadoLabel(est)) },
                                    onClick = {
                                        estado = est
                                        expandedEstado = false
                                    }
                                )
                            }
                        }
                    }
                    
                    // Selector de proveedor solo para admin
                    if (esAdmin && proveedores.isNotEmpty()) {
                        var expandedProveedor by remember { mutableStateOf(false) }
                        val proveedorSeleccionado = proveedores.find { it.id == proveedorId }
                        ExposedDropdownMenuBox(
                            expanded = expandedProveedor,
                            onExpandedChange = { expandedProveedor = !expandedProveedor }
                        ) {
                            OutlinedTextField(
                                value = proveedorSeleccionado?.nombre ?: "Sin asignar",
                                onValueChange = {},
                                readOnly = true,
                                label = { Text("Proveedor") },
                                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedProveedor) },
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .menuAnchor(),
                                enabled = !isLoading
                            )
                            ExposedDropdownMenu(
                                expanded = expandedProveedor,
                                onDismissRequest = { expandedProveedor = false }
                            ) {
                                DropdownMenuItem(
                                    text = { Text("Sin asignar") },
                                    onClick = {
                                        proveedorId = null
                                        expandedProveedor = false
                                    }
                                )
                                proveedores.forEach { prov ->
                                    DropdownMenuItem(
                                        text = { Text(prov.nombre) },
                                        onClick = {
                                            proveedorId = prov.id
                                            expandedProveedor = false
                                        }
                                    )
                                }
                            }
                        }
                    }
                    
                    // Comentario del cambio solo para admin
                    if (esAdmin) {
                        OutlinedTextField(
                            value = comentarioCambio,
                            onValueChange = { comentarioCambio = it },
                            label = { Text("Comentario del cambio (opcional)") },
                            modifier = Modifier.fillMaxWidth(),
                            enabled = !isLoading
                        )
                    }
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    scope.launch {
                        isLoading = true
                        error = null
                        try {
                            val updateData = IncidenciaUpdate(
                                titulo = titulo,
                                descripcion = descripcion,
                                prioridad = prioridad,
                                estado = if (puedeEditarEstado) estado else null,
                                proveedor_id = if (esAdmin) proveedorId else null,
                                comentario_cambio = if (esAdmin && comentarioCambio.isNotBlank()) comentarioCambio else null,
                                version = incidencia.version
                            )
                            val result = incidenciaRepository.updateIncidencia(incidencia.id, updateData)
                            result.onSuccess {
                                onSuccess()
                            }.onFailure { e ->
                                error = e.message ?: "Error al actualizar incidencia"
                            }
                        } catch (e: Exception) {
                            error = e.message ?: "Error al actualizar incidencia"
                        } finally {
                            isLoading = false
                        }
                    }
                },
                enabled = !isLoading && titulo.isNotBlank() && descripcion.isNotBlank()
            ) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(16.dp))
                } else {
                    Text("Guardar")
                }
            }
        },
        dismissButton = {
            TextButton(
                onClick = onDismiss,
                enabled = !isLoading
            ) {
                Text("Cancelar")
            }
        }
    )
}

fun getEstadoLabel(estado: String): String {
    return when (estado.lowercase()) {
        "abierta" -> "Abierta"
        "asignada" -> "Asignada"
        "en_progreso" -> "En Progreso"
        "resuelta" -> "Resuelta"
        "cerrada" -> "Cerrada"
        else -> estado
    }
}

fun getPrioridadLabel(prioridad: String): String {
    return when (prioridad.lowercase()) {
        "baja" -> "Baja"
        "media" -> "Media"
        "alta" -> "Alta"
        "urgente" -> "Urgente"
        else -> prioridad.capitalize()
    }
}

// Función para descargar y abrir documento
suspend fun descargarYabrirDocumento(
    context: android.content.Context,
    responseBody: ResponseBody,
    nombreArchivo: String,
    tipoArchivo: String
) {
    withContext(Dispatchers.IO) {
        try {
            // Crear directorio de descargas si no existe
            val downloadsDir = context.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
                ?: context.filesDir
            val file = File(downloadsDir, nombreArchivo)
            
            // Escribir el archivo
            file.outputStream().use { output ->
                responseBody.byteStream().use { input ->
                    input.copyTo(output)
                }
            }
            
            // Abrir el archivo con Intent
            withContext(Dispatchers.Main) {
                val uri = FileProvider.getUriForFile(
                    context,
                    "${context.packageName}.fileprovider",
                    file
                )
                
                val intent = Intent(Intent.ACTION_VIEW).apply {
                    setDataAndType(uri, tipoArchivo)
                    addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                }
                
                try {
                    context.startActivity(intent)
                } catch (e: Exception) {
                    // Si no hay app para abrir, intentar con ACTION_SEND
                    val shareIntent = Intent(Intent.ACTION_SEND).apply {
                        type = tipoArchivo
                        putExtra(Intent.EXTRA_STREAM, uri)
                        addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                    }
                    context.startActivity(Intent.createChooser(shareIntent, "Abrir con..."))
                }
            }
        } catch (e: Exception) {
            throw e
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CambiarEstadoCard(
    incidencia: Incidencia,
    incidenciaRepository: com.tomoko.fyntra.data.repository.IncidenciaRepository,
    onEstadoCambiado: () -> Unit
) {
    var estadoSeleccionado by remember { mutableStateOf(incidencia.estado) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var expandedEstado by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
    // Estados permitidos para proveedor
    val estadosPermitidos = listOf("asignada", "en_progreso", "resuelta", "cerrada")
    
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text("Cambiar Estado", fontSize = 16.sp, fontWeight = FontWeight.Bold)
            
            if (error != null) {
                Text(
                    text = error!!,
                    color = MaterialTheme.colorScheme.error,
                    fontSize = 12.sp
                )
            }
            
            ExposedDropdownMenuBox(
                expanded = expandedEstado,
                onExpandedChange = { expandedEstado = !expandedEstado }
            ) {
                OutlinedTextField(
                    value = getEstadoLabel(estadoSeleccionado),
                    onValueChange = {},
                    readOnly = true,
                    label = { Text("Estado") },
                    trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedEstado) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .menuAnchor(),
                    enabled = !isLoading
                )
                ExposedDropdownMenu(
                    expanded = expandedEstado,
                    onDismissRequest = { expandedEstado = false }
                ) {
                    estadosPermitidos.forEach { est ->
                        DropdownMenuItem(
                            text = { Text(getEstadoLabel(est)) },
                            onClick = {
                                estadoSeleccionado = est
                                expandedEstado = false
                            }
                        )
                    }
                }
            }
            
            Button(
                onClick = {
                    if (estadoSeleccionado != incidencia.estado) {
                        scope.launch {
                            isLoading = true
                            error = null
                            try {
                                val updateData = IncidenciaUpdate(
                                    titulo = null,
                                    descripcion = null,
                                    prioridad = null,
                                    estado = estadoSeleccionado,
                                    proveedor_id = null,
                                    comentario_cambio = null,
                                    version = incidencia.version
                                )
                                val result = incidenciaRepository.updateIncidencia(incidencia.id, updateData)
                                result.onSuccess {
                                    onEstadoCambiado()
                                }.onFailure { e ->
                                    error = e.message ?: "Error al cambiar estado"
                                }
                            } catch (e: Exception) {
                                error = e.message ?: "Error al cambiar estado"
                            } finally {
                                isLoading = false
                            }
                        }
                    }
                },
                enabled = !isLoading && estadoSeleccionado != incidencia.estado,
                modifier = Modifier.fillMaxWidth()
            ) {
                if (isLoading) {
                    CircularProgressIndicator(modifier = Modifier.size(16.dp))
                } else {
                    Text("Guardar Cambio de Estado")
                }
            }
        }
    }
}

