package com.tomoko.fyntra.ui.screens.incidencia

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
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import android.net.Uri
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.text.SimpleDateFormat
import java.util.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Build
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.TextButton
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.repository.AuthRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun IncidenciaDetailScreen(
    incidenciaId: Int,
    userRol: String,
    navController: NavController,
    authRepository: AuthRepository,
    userId: Int? = null,
    initialTab: Int = 0
) {
    var incidencia by remember { mutableStateOf<Incidencia?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var selectedTab by remember { mutableStateOf(initialTab) }
    var showDeleteDialog by remember { mutableStateOf(false) }
    var isDeleting by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()
    
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

    LaunchedEffect(incidenciaId) {
        isLoading = true
        try {
            val response = authRepository.getApiServiceInstance().getIncidencia(incidenciaId)
            if (response.isSuccessful) {
                incidencia = response.body()
            } else {
                error = "Error al cargar la incidencia"
            }
        } catch (e: Exception) {
            error = e.message
        } finally {
            isLoading = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(incidencia?.titulo ?: "Incidencia", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = { navController.popBackStack() }) {
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
        },
        bottomBar = {
            TabRow(selectedTabIndex = selectedTab) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = { Text("Detalles") }
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = { Text("Historial") }
                )
                Tab(
                    selected = selectedTab == 2,
                    onClick = { selectedTab = 2 },
                    text = { Text("Documentos") }
                )
                Tab(
                    selected = selectedTab == 3,
                    onClick = { selectedTab = 3 },
                    text = { Text("Chat") }
                )
                if (userRol == "proveedor") {
                    Tab(
                        selected = selectedTab == 4,
                        onClick = { selectedTab = 4 },
                        text = { Text("Actuaciones") }
                    )
                }
            }
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
                    0 -> DetallesTab(incidencia!!, userRol, authRepository)
                    1 -> HistorialTab(incidencia!!)
                    2 -> DocumentosTab(incidencia!!, userRol, authRepository, userId, context)
                    3 -> ChatTab(incidencia!!, authRepository, userId)
                    4 -> if (userRol == "proveedor") ActuacionesTab(incidencia!!, authRepository)
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
                                    val response = authRepository.getApiServiceInstance().eliminarIncidencia(incidenciaId)
                                    if (response.isSuccessful) {
                                        navController.popBackStack()
                                    } else {
                                        error = "Error al eliminar la incidencia"
                                        showDeleteDialog = false
                                    }
                                } catch (e: Exception) {
                                    error = e.message ?: "Error al eliminar la incidencia"
                                    showDeleteDialog = false
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
    }
}

@Composable
fun DetallesTab(
    incidencia: Incidencia,
    userRol: String,
    authRepository: AuthRepository
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
                        Text(incidencia.estado, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                    Column {
                        Text("Prioridad", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text(incidencia.prioridad, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text("Inmueble", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text("${incidencia.inmueble?.referencia ?: "N/A"} - ${incidencia.inmueble?.direccion ?: ""}", fontSize = 14.sp)
                
                Spacer(modifier = Modifier.height(8.dp))
                
                Text("Fecha de creación", fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
                Text(formatearFecha(incidencia.fecha_alta), fontSize = 14.sp)
            }
        }

        if (userRol == "proveedor") {
            Card(modifier = Modifier.fillMaxWidth()) {
                Column(
                    modifier = Modifier.padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text("Cambiar Estado", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                    // TODO: Implementar selector de estado
                }
            }
        }
    }
}

@Composable
fun DocumentosTab(
    incidencia: Incidencia,
    userRol: String,
    authRepository: AuthRepository,
    userId: Int?,
    context: android.content.Context
) {
    var documentos by remember { mutableStateOf<List<com.tomoko.fyntra.data.models.Documento>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showUploadDialog by remember { mutableStateOf(false) }
    var nombreDocumento by remember { mutableStateOf("") }
    var archivoSeleccionado by remember { mutableStateOf<Uri?>(null) }
    var isUploading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    // Launcher para seleccionar archivos
    val filePickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        archivoSeleccionado = uri
    }

    fun cargarDocumentos() {
        scope.launch {
            isLoading = true
            try {
                val response = authRepository.getApiServiceInstance().getDocumentosIncidencia(incidencia.id)
                if (response.isSuccessful) {
                    documentos = response.body() ?: emptyList()
                } else {
                    error = "Error al cargar documentos"
                }
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
        if (archivoSeleccionado == null) {
            error = "Por favor, seleccione un archivo"
            return
        }

        scope.launch {
            isUploading = true
            try {
                val uri = archivoSeleccionado!!
                val inputStream = context?.contentResolver?.openInputStream(uri)
                if (inputStream == null) {
                    error = "Error al leer el archivo"
                    isUploading = false
                    return@launch
                }

                // Crear archivo temporal
                val tempFile = File.createTempFile("upload_", null, context?.cacheDir)
                tempFile.outputStream().use { output ->
                    inputStream.copyTo(output)
                }

                // Obtener el nombre del archivo original si es posible
                val fileName = try {
                    context?.contentResolver?.query(uri, null, null, null, null)?.use { cursor ->
                        val nameIndex = cursor.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME)
                        if (cursor.moveToFirst() && nameIndex >= 0) {
                            cursor.getString(nameIndex)
                        } else {
                            tempFile.name
                        }
                    } ?: tempFile.name
                } catch (e: Exception) {
                    tempFile.name
                }

                // Crear RequestBody para el archivo (el backend espera "archivo" no "file")
                val requestFile = tempFile.asRequestBody("application/octet-stream".toMediaTypeOrNull())
                val filePart = MultipartBody.Part.createFormData("archivo", fileName, requestFile)

                // Crear RequestBody para el nombre y incidencia_id
                val nombrePart = nombreDocumento.toRequestBody("text/plain".toMediaTypeOrNull())
                val incidenciaIdPart = incidencia.id.toString().toRequestBody("text/plain".toMediaTypeOrNull())

                val response = authRepository.getApiServiceInstance().uploadDocumento(
                    incidenciaIdPart,
                    nombrePart,
                    filePart
                )

                if (response.isSuccessful) {
                    nombreDocumento = ""
                    archivoSeleccionado = null
                    showUploadDialog = false
                    cargarDocumentos()
                } else {
                    error = "Error al subir documento: ${response.message()}"
                }

                // Eliminar archivo temporal
                tempFile.delete()
            } catch (e: Exception) {
                error = "Error al subir documento: ${e.message}"
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
                                        // Abrir documento en navegador o descargar
                                        scope.launch {
                                            try {
                                                // Obtener token para la descarga
                                                val authDataStore = com.tomoko.fyntra.data.local.AuthDataStore(context)
                                                val token = authDataStore.getToken()
                                                if (token != null) {
                                                    val response = authRepository.getApiServiceInstance().downloadDocumento(doc.id, token)
                                                    if (response.isSuccessful) {
                                                        // TODO: Abrir archivo o descargar
                                                        error = "Funcionalidad de descarga en desarrollo"
                                                    } else {
                                                        error = "Error al descargar documento: ${response.message()}"
                                                    }
                                                } else {
                                                    error = "No se pudo obtener el token de autenticación"
                                                }
                                            } catch (e: Exception) {
                                                error = e.message
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
            onDismissRequest = { if (!isUploading) showUploadDialog = false },
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
                    Button(
                        onClick = { filePickerLauncher.launch("*/*") },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isUploading
                    ) {
                        Text(if (archivoSeleccionado != null) "Archivo seleccionado" else "Seleccionar archivo")
                    }
                    if (archivoSeleccionado != null) {
                        Text(
                            text = "Archivo: ${archivoSeleccionado.toString().takeLast(30)}",
                            fontSize = 12.sp,
                            color = MaterialTheme.colorScheme.primary
                        )
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = { subirDocumento() },
                    enabled = !isUploading && nombreDocumento.isNotBlank() && archivoSeleccionado != null
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
                    onClick = { showUploadDialog = false },
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
                val sdf = SimpleDateFormat(formato, Locale.getDefault())
                sdf.timeZone = TimeZone.getTimeZone("UTC")
                fecha = sdf.parse(fechaString)
                if (fecha != null) break
            } catch (e: Exception) {
                continue
            }
        }
        if (fecha != null) {
            val formatoSalida = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
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
    val historial = incidencia.historial ?: emptyList()
    
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
                                text = "Estado: ${item.estado_anterior ?: "N/A"} → ${item.estado_nuevo}",
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
    authRepository: AuthRepository,
    userId: Int?
) {
    var mensajes by remember { mutableStateOf<List<com.tomoko.fyntra.data.models.Mensaje>>(emptyList()) }
    var nuevoMensaje by remember { mutableStateOf("") }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    fun cargarMensajes() {
        scope.launch {
            isLoading = true
            try {
                val response = authRepository.getApiServiceInstance().getMensajesIncidencia(incidencia.id)
                if (response.isSuccessful) {
                    mensajes = response.body() ?: emptyList()
                } else {
                    error = "Error al cargar mensajes"
                }
            } catch (e: Exception) {
                error = e.message
            } finally {
                isLoading = false
            }
        }
    }

    LaunchedEffect(incidencia.id) {
        cargarMensajes()
    }

    fun enviarMensaje() {
        if (nuevoMensaje.isBlank()) return
        
        scope.launch {
            try {
                val response = authRepository.getApiServiceInstance().enviarMensaje(
                    incidencia.id,
                    com.tomoko.fyntra.data.models.MensajeCreate(nuevoMensaje)
                )
                if (response.isSuccessful) {
                    nuevoMensaje = ""
                    cargarMensajes()
                } else {
                    error = "Error al enviar mensaje"
                }
            } catch (e: Exception) {
                error = e.message
            }
        }
    }

    fun eliminarMensaje(mensajeId: Int) {
        scope.launch {
            try {
                // TODO: Implementar endpoint de eliminación de mensajes
                error = "Funcionalidad de eliminación en desarrollo"
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
                                    text = mensaje.usuario_nombre,
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
                            // Solo el autor puede eliminar su mensaje si es el último
                            if (userId != null && mensaje.usuario_id == userId && mensajes.lastOrNull()?.id == mensaje.id) {
                                TextButton(
                                    onClick = { eliminarMensaje(mensaje.id) },
                                    modifier = Modifier.align(Alignment.End)
                                ) {
                                    Text("Eliminar", fontSize = 10.sp, color = MaterialTheme.colorScheme.error)
                                }
                            }
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
    authRepository: AuthRepository
) {
    // TODO: Implementar lista de actuaciones y formulario
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = androidx.compose.ui.Alignment.Center
    ) {
        Text("Actuaciones - En desarrollo")
    }
}

