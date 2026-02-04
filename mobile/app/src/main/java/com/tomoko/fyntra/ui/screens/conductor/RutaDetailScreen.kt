package com.tomoko.fyntra.ui.screens.conductor

import android.Manifest
import android.content.pm.PackageManager
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.net.Uri
import android.util.Size
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.core.content.ContextCompat
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.core.content.FileProvider
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.Parada
import com.tomoko.fyntra.data.models.Ruta
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.util.ImageCompression
import kotlinx.coroutines.launch
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.io.FileOutputStream
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RutaDetailScreen(
    rutaId: Int,
    navController: NavController,
    authRepository: AuthRepository
) {
    var ruta by remember { mutableStateOf<Ruta?>(null) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showCompletarParadaDialog by remember { mutableStateOf<Parada?>(null) }
    var showIniciarDialog by remember { mutableStateOf(false) }
    var showFinalizarDialog by remember { mutableStateOf(false) }
    var showCrearIncidenciaDialog by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    fun cargarRuta() {
        scope.launch {
            isLoading = true
            try {
                val response = authRepository.getApiServiceInstance().getRuta(rutaId)
                if (response.isSuccessful) {
                    ruta = response.body()
                } else {
                    error = "Error al cargar la ruta: ${response.message()}"
                }
            } catch (e: Exception) {
                error = e.message
            } finally {
                isLoading = false
            }
        }
    }

    LaunchedEffect(rutaId) {
        cargarRuta()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Ruta #${rutaId}", fontWeight = FontWeight.Bold) },
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
                )
            )
        },
        floatingActionButton = {
            when (ruta?.estado) {
                "planificada" -> {
                    FloatingActionButton(
                        onClick = { showIniciarDialog = true }
                    ) {
                        Icon(
                            imageVector = Icons.Default.PlayArrow,
                            contentDescription = "Iniciar Ruta"
                        )
                    }
                }
                "en_curso" -> {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(16.dp),
                        modifier = Modifier.padding(end = 16.dp, bottom = 16.dp)
                    ) {
                        FloatingActionButton(
                            onClick = { showCrearIncidenciaDialog = true },
                            containerColor = MaterialTheme.colorScheme.errorContainer
                        ) {
                            Icon(
                                imageVector = Icons.Default.Warning,
                                contentDescription = "Reportar Incidencia"
                            )
                        }
                        val todasParadasCompletadas = ruta?.paradas?.all { it.estado == "entregado" } ?: false
                        if (todasParadasCompletadas) {
                            FloatingActionButton(
                                onClick = { showFinalizarDialog = true },
                                containerColor = MaterialTheme.colorScheme.primary
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Check,
                                    contentDescription = "Finalizar Ruta"
                                )
                            }
                        }
                    }
                }
            }
        }
    ) { paddingValues ->
        if (isLoading) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        } else if (error != null) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentAlignment = Alignment.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(error!!, color = MaterialTheme.colorScheme.error)
                    Spacer(modifier = Modifier.height(16.dp))
                    Button(onClick = { cargarRuta() }) {
                        Text("Reintentar")
                    }
                }
            }
        } else if (ruta != null) {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(paddingValues),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                item {
                    Card(modifier = Modifier.fillMaxWidth()) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            val vehiculo = ruta!!.vehiculo
                            if (vehiculo != null) {
                                Text("Vehículo: ${vehiculo.matricula}", fontSize = 16.sp)
                            }
                            if (ruta!!.fecha != null) {
                                Text("Fecha: ${ruta!!.fecha}", fontSize = 16.sp)
                            }
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text("Estado", fontSize = 16.sp, fontWeight = FontWeight.Bold)
                                Surface(
                                    color = when (ruta!!.estado) {
                                        "en_curso" -> Color(0xFFFF9800)
                                        "planificada" -> Color(0xFF2196F3)
                                        "completada" -> Color(0xFF4CAF50)
                                        else -> Color(0xFF9E9E9E)
                                    },
                                    shape = MaterialTheme.shapes.small
                                ) {
                                    Text(
                                        text = when (ruta!!.estado) {
                                            "en_curso" -> "En Progreso"
                                            "planificada" -> "Planificada"
                                            "completada" -> "Completada"
                                            else -> ruta!!.estado
                                        },
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                        fontSize = 12.sp,
                                        color = Color.White,
                                        fontWeight = FontWeight.Bold
                                    )
                                }
                            }
                            val paradasCompletadas = ruta!!.paradas?.count { it.estado == "entregado" } ?: 0
                            val totalParadas = ruta!!.paradas?.size ?: 0
                            if (totalParadas > 0) {
                                Text(
                                    text = "Progreso: $paradasCompletadas/$totalParadas paradas completadas",
                                    fontSize = 14.sp
                                )
                            }
                        }
                    }
                }

                item {
                    Text(
                        "Paradas (${ruta!!.paradas?.size ?: 0})",
                        fontSize = 20.sp,
                        fontWeight = FontWeight.Bold
                    )
                }

                items(ruta!!.paradas ?: emptyList()) { parada ->
                    ParadaCard(
                        parada = parada,
                        rutaEstado = ruta!!.estado,
                        onCompletarParada = {
                            if (ruta!!.estado == "en_curso") {
                                showCompletarParadaDialog = parada
                            }
                        }
                    )
                }
            }
        }

        // Dialog para iniciar ruta
        if (showIniciarDialog) {
            AlertDialog(
                onDismissRequest = { showIniciarDialog = false },
                title = { Text("Iniciar Ruta") },
                text = { Text("¿Estás seguro de que quieres iniciar esta ruta?") },
                confirmButton = {
                    Button(onClick = {
                        scope.launch {
                            try {
                                val response = authRepository.getApiServiceInstance().iniciarRuta(rutaId)
                                if (response.isSuccessful) {
                                    ruta = response.body()
                                    showIniciarDialog = false
                                } else {
                                    error = "Error al iniciar la ruta: ${response.message()}"
                                }
                            } catch (e: Exception) {
                                error = e.message
                            }
                        }
                    }) {
                        Text("Iniciar")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showIniciarDialog = false }) {
                        Text("Cancelar")
                    }
                }
            )
        }

        // Dialog para finalizar ruta
        if (showFinalizarDialog) {
            AlertDialog(
                onDismissRequest = { showFinalizarDialog = false },
                title = { Text("Finalizar Ruta") },
                text = { Text("¿Estás seguro de que quieres finalizar esta ruta?") },
                confirmButton = {
                    Button(onClick = {
                        scope.launch {
                            try {
                                val response = authRepository.getApiServiceInstance().finalizarRuta(rutaId)
                                if (response.isSuccessful) {
                                    ruta = response.body()
                                    showFinalizarDialog = false
                                } else {
                                    error = "Error al finalizar la ruta: ${response.message()}"
                                }
                            } catch (e: Exception) {
                                error = e.message
                            }
                        }
                    }) {
                        Text("Finalizar")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showFinalizarDialog = false }) {
                        Text("Cancelar")
                    }
                }
            )
        }

        // Dialog para completar parada
        showCompletarParadaDialog?.let { parada ->
            CompletarParadaDialog(
                parada = parada,
                rutaId = rutaId,
                onDismiss = { showCompletarParadaDialog = null },
                onSuccess = {
                    showCompletarParadaDialog = null
                    cargarRuta()
                },
                authRepository = authRepository
            )
        }

        // Dialog para crear incidencia
        if (showCrearIncidenciaDialog) {
            CrearIncidenciaRutaDialog(
                rutaId = rutaId,
                paradas = ruta?.paradas ?: emptyList(),
                onDismiss = { showCrearIncidenciaDialog = false },
                onSuccess = {
                    showCrearIncidenciaDialog = false
                    cargarRuta()
                },
                authRepository = authRepository
            )
        }
    }
}

@Composable
fun ParadaCard(
    parada: Parada,
    rutaEstado: String,
    onCompletarParada: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Parada ${parada.orden}",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                Surface(
                    color = when (parada.estado) {
                        "entregado" -> Color(0xFF4CAF50)
                        "en_camino" -> Color(0xFFFF9800)
                        "pendiente" -> Color(0xFF9E9E9E)
                        else -> Color(0xFF9E9E9E)
                    },
                    shape = MaterialTheme.shapes.small
                ) {
                    Text(
                        text = when (parada.estado) {
                            "entregado" -> "Completada"
                            "en_camino" -> "En Camino"
                            "pendiente" -> "Pendiente"
                            else -> parada.estado
                        },
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        fontSize = 12.sp,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            Text("Dirección: ${parada.direccion}")
            if (parada.pedido != null) {
                Text("Cliente: ${parada.pedido.cliente}")
            }
            if (parada.fecha_hora_completada != null) {
                Text("Completada: ${parada.fecha_hora_completada}", fontSize = 12.sp, color = Color(0xFF6F7785))
            }
            
            if (rutaEstado == "en_curso" && parada.estado != "entregado") {
                Button(
                    onClick = onCompletarParada,
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.CheckCircle, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Marcar como Completada")
                }
            }
        }
    }
}

@Composable
fun CompletarParadaDialog(
    parada: Parada,
    rutaId: Int,
    onDismiss: () -> Unit,
    onSuccess: () -> Unit,
    authRepository: AuthRepository
) {
    val context = LocalContext.current
    var fotoBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var archivoFotoActual by remember { mutableStateOf<File?>(null) }
    var firmaBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var showFirmaCanvas by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && archivoFotoActual != null && archivoFotoActual!!.exists()) {
            fotoBitmap = BitmapFactory.decodeFile(archivoFotoActual!!.absolutePath)
        }
    }

    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val nuevoArchivo = File.createTempFile(
                "foto_parada_${parada.id}_${timeStamp}_",
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
    }

    fun tomarFoto() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val nuevoArchivo = File.createTempFile(
                "foto_parada_${parada.id}_${timeStamp}_",
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
            permissionLauncher.launch(Manifest.permission.CAMERA)
        }
    }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = MaterialTheme.shapes.large
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "Completar Parada ${parada.orden}",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )

                Text(
                    text = "Foto y firma opcionales. Puedes completar la parada sin adjuntar nada.",
                    fontSize = 13.sp,
                    color = Color(0xFF6F7785)
                )

                // Botón para tomar foto (solicita permiso CAMERA si hace falta)
                OutlinedButton(
                    onClick = { tomarFoto() },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.Add, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Tomar Foto (opcional)",
                        modifier = Modifier.weight(1f),
                        textAlign = androidx.compose.ui.text.style.TextAlign.Start
                    )
                }

                // Mostrar foto si existe
                fotoBitmap?.let { bitmap ->
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Foto",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                    )
                }

                // Botón para firma
                OutlinedButton(
                    onClick = { showFirmaCanvas = true },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.Edit, contentDescription = null)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        text = "Añadir Firma (opcional)",
                        modifier = Modifier.weight(1f),
                        textAlign = TextAlign.Start
                    )
                }

                // Mostrar firma si existe
                firmaBitmap?.let { bitmap ->
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Firma",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(150.dp)
                    )
                }

                Column(
                    modifier = Modifier.fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Button(
                        onClick = {
                            scope.launch {
                                isLoading = true
                                try {
                                    // RNF18: compresión de imágenes antes de subir
                                    val fotoPart = archivoFotoActual?.takeIf { it.exists() }?.let { file ->
                                        val compressed = ImageCompression.compressPhotoForUpload(context, file)
                                        val fileToUpload = compressed ?: file
                                        MultipartBody.Part.createFormData(
                                            "foto",
                                            fileToUpload.name,
                                            fileToUpload.asRequestBody("image/jpeg".toMediaType())
                                        )
                                    }

                                    val firmaPart = firmaBitmap?.let { bitmap ->
                                        val firmaFile = ImageCompression.compressSignatureForUpload(context, bitmap)
                                            ?: run {
                                                val fallback = File(context.cacheDir, "firma_${parada.id}_${System.currentTimeMillis()}.png")
                                                FileOutputStream(fallback).use { out ->
                                                    bitmap.compress(Bitmap.CompressFormat.PNG, 90, out)
                                                }
                                                fallback
                                            }
                                        MultipartBody.Part.createFormData(
                                            "firma",
                                            firmaFile.name,
                                            firmaFile.asRequestBody("image/png".toMediaType())
                                        )
                                    }

                                    val response = authRepository.getApiServiceInstance().completarParada(
                                        rutaId = rutaId,
                                        paradaId = parada.id,
                                        accion = "completar".toRequestBody("text/plain".toMediaType()),
                                        foto = fotoPart,
                                        firma = firmaPart
                                    )

                                    if (response.isSuccessful) {
                                        onSuccess()
                                    } else {
                                        // Error
                                    }
                                } catch (e: Exception) {
                                    // Error
                                } finally {
                                    isLoading = false
                                }
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = !isLoading
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(16.dp),
                                color = Color.White
                            )
                        } else {
                            Text(
                                text = if (fotoBitmap == null && firmaBitmap == null) "Completar sin evidencias" else "Completar",
                                modifier = Modifier.fillMaxWidth(),
                                textAlign = androidx.compose.ui.text.style.TextAlign.Center
                            )
                        }
                    }
                    TextButton(
                        onClick = onDismiss,
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            text = "Cancelar",
                            modifier = Modifier.fillMaxWidth(),
                            textAlign = TextAlign.Center
                        )
                    }
                }
            }
        }
    }

    // Dialog para firma
    if (showFirmaCanvas) {
        FirmaCanvasDialog(
            onDismiss = { showFirmaCanvas = false },
            onFirmaCompletada = { bitmap ->
                firmaBitmap = bitmap
                showFirmaCanvas = false
            }
        )
    }
}

@Composable
fun FirmaCanvasDialog(
    onDismiss: () -> Unit,
    onFirmaCompletada: (Bitmap) -> Unit
) {
    // Usar listas de puntos para mantener la información de dibujo
    data class PathPoints(val points: List<Offset>)
    val paths = remember { mutableStateListOf<PathPoints>() }
    var currentPathPoints by remember { mutableStateOf<List<Offset>>(emptyList()) }
    var canvasSize by remember { mutableStateOf(android.util.Size(800, 200)) }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = MaterialTheme.shapes.large
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(24.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    text = "Firma",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )

                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(200.dp)
                        .background(Color.White)
                ) {
                    Canvas(
                        modifier = Modifier
                            .fillMaxSize()
                            .pointerInput(Unit) {
                                detectDragGestures(
                                    onDragStart = { offset ->
                                        currentPathPoints = mutableListOf(offset)
                                        canvasSize = android.util.Size(size.width.toInt(), size.height.toInt())
                                    },
                                    onDrag = { change, _ ->
                                        val newOffset = change.position
                                        currentPathPoints = currentPathPoints + newOffset
                                    },
                                    onDragEnd = {
                                        if (currentPathPoints.isNotEmpty()) {
                                            paths.add(PathPoints(currentPathPoints))
                                        }
                                        currentPathPoints = emptyList()
                                    }
                                )
                            }
                    ) {
                        val stroke = androidx.compose.ui.graphics.drawscope.Stroke(width = 3f)
                        
                        // Dibujar todos los paths guardados
                        paths.forEach { pathPoints ->
                            if (pathPoints.points.isNotEmpty()) {
                                val composePath = Path().apply {
                                    moveTo(pathPoints.points[0].x, pathPoints.points[0].y)
                                    pathPoints.points.drop(1).forEach { point ->
                                        lineTo(point.x, point.y)
                                    }
                                }
                                drawPath(path = composePath, color = Color.Black, style = stroke)
                            }
                        }
                        
                        // Dibujar el path actual
                        if (currentPathPoints.isNotEmpty()) {
                            val composePath = Path().apply {
                                moveTo(currentPathPoints[0].x, currentPathPoints[0].y)
                                currentPathPoints.drop(1).forEach { point ->
                                    lineTo(point.x, point.y)
                                }
                            }
                            drawPath(path = composePath, color = Color.Black, style = stroke)
                        }
                    }
                }

                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    TextButton(
                        onClick = {
                            paths.clear()
                            currentPathPoints = emptyList()
                        },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Limpiar")
                    }
                    TextButton(
                        onClick = onDismiss,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Cancelar")
                    }
                    Button(
                        onClick = {
                            // Crear bitmap desde los paths
                            val bitmap = Bitmap.createBitmap(canvasSize.width, canvasSize.height, Bitmap.Config.ARGB_8888)
                            val canvas = android.graphics.Canvas(bitmap)
                            canvas.drawColor(android.graphics.Color.WHITE)
                            
                            val paint = android.graphics.Paint().apply {
                                color = android.graphics.Color.BLACK
                                style = android.graphics.Paint.Style.STROKE
                                strokeWidth = 3f
                                isAntiAlias = true
                            }
                            
                            // Dibujar todos los paths usando los puntos
                            paths.forEach { pathPoints ->
                                if (pathPoints.points.isNotEmpty()) {
                                    val androidPath = android.graphics.Path()
                                    androidPath.moveTo(pathPoints.points[0].x, pathPoints.points[0].y)
                                    pathPoints.points.drop(1).forEach { point ->
                                        androidPath.lineTo(point.x, point.y)
                                    }
                                    canvas.drawPath(androidPath, paint)
                                }
                            }
                            
                            onFirmaCompletada(bitmap)
                        },
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Guardar")
                    }
                }
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CrearIncidenciaRutaDialog(
    rutaId: Int,
    paradas: List<Parada>,
    onDismiss: () -> Unit,
    onSuccess: () -> Unit,
    authRepository: AuthRepository
) {
    var tipoIncidencia by remember { mutableStateOf("averia") }
    var descripcion by remember { mutableStateOf("") }
    var paradaSeleccionada by remember { mutableStateOf<Int?>(null) }
    var fotoBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var archivoFotoActual by remember { mutableStateOf<File?>(null) }
    var cancelarRuta by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var mensajeExito by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()
    val context = LocalContext.current

    val cameraLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.TakePicture()
    ) { success ->
        if (success && archivoFotoActual != null && archivoFotoActual!!.exists()) {
            fotoBitmap = BitmapFactory.decodeFile(archivoFotoActual!!.absolutePath)
        }
    }

    val permissionLauncherIncidencia = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val nuevoArchivo = File.createTempFile(
                "incidencia_ruta_${rutaId}_${timeStamp}_",
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

    fun tomarFotoIncidencia() {
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            val timeStamp = SimpleDateFormat("yyyyMMdd_HHmmss", Locale.getDefault()).format(Date())
            val nuevoArchivo = File.createTempFile(
                "incidencia_ruta_${rutaId}_${timeStamp}_",
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
            permissionLauncherIncidencia.launch(Manifest.permission.CAMERA)
        }
    }

    Dialog(onDismissRequest = onDismiss) {
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            shape = MaterialTheme.shapes.large
        ) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(16.dp)
                    .verticalScroll(rememberScrollState()),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                Text(
                    "Reportar Incidencia",
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )

                if (error != null) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.errorContainer
                        )
                    ) {
                        Text(
                            text = error!!,
                            color = MaterialTheme.colorScheme.onErrorContainer,
                            modifier = Modifier.padding(16.dp)
                        )
                    }
                }
                
                if (mensajeExito != null) {
                    Card(
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.primaryContainer
                        )
                    ) {
                        Text(
                            text = mensajeExito!!,
                            color = MaterialTheme.colorScheme.onPrimaryContainer,
                            modifier = Modifier.padding(16.dp)
                        )
                    }
                }

                // Selector: Ruta o Parada
                var expandedUbicacion by remember { mutableStateOf(false) }
                Column(
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text("Ubicación *")
                    Button(
                        onClick = { expandedUbicacion = !expandedUbicacion },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text(
                            if (paradaSeleccionada == null)
                                "Ruta"
                            else
                                "Parada #${paradas.find { it.id == paradaSeleccionada }?.orden ?: paradaSeleccionada}"
                        )
                    }
                    DropdownMenu(
                        expanded = expandedUbicacion,
                        onDismissRequest = { expandedUbicacion = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("Ruta") },
                            onClick = {
                                paradaSeleccionada = null
                                expandedUbicacion = false
                            }
                        )
                        paradas.forEach { parada ->
                            DropdownMenuItem(
                                text = { Text("Parada #${parada.orden} - ${parada.direccion}") },
                                onClick = {
                                    paradaSeleccionada = parada.id
                                    expandedUbicacion = false
                                }
                            )
                        }
                    }
                }

                // Selector de tipo de incidencia
                var expandedTipo by remember { mutableStateOf(false) }
                Column(
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text("Tipo de Incidencia *")
                    Button(
                        onClick = { expandedTipo = !expandedTipo },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        val tiposIncidenciaDisplay = mapOf(
                            "averia" to "Avería",
                            "retraso" to "Retraso",
                            "cliente_ausente" to "Cliente ausente",
                            "otros" to "Otros"
                        )
                        Text(tiposIncidenciaDisplay[tipoIncidencia] ?: tipoIncidencia.replaceFirstChar { it.uppercaseChar() })
                    }
                    DropdownMenu(
                        expanded = expandedTipo,
                        onDismissRequest = { expandedTipo = false }
                    ) {
                        val tiposIncidencia = mapOf(
                            "averia" to "Avería",
                            "retraso" to "Retraso",
                            "cliente_ausente" to "Cliente ausente",
                            "otros" to "Otros"
                        )
                        tiposIncidencia.forEach { (valor, texto) ->
                            DropdownMenuItem(
                                text = { Text(texto) },
                                onClick = {
                                    tipoIncidencia = valor
                                    expandedTipo = false
                                }
                            )
                        }
                    }
                }

                // Descripción
                OutlinedTextField(
                    value = descripcion,
                    onValueChange = { descripcion = it },
                    label = { Text("Descripción *") },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(120.dp),
                    maxLines = 5
                )

                // Botón para tomar foto (solicita permiso CAMERA si hace falta)
                Button(
                    onClick = { tomarFotoIncidencia() },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text("Tomar foto (opcional)")
                }

                // Mostrar foto si existe
                fotoBitmap?.let { bitmap ->
                    Image(
                        bitmap = bitmap.asImageBitmap(),
                        contentDescription = "Foto incidencia",
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                    )
                }

                // Checkbox para cancelar ruta
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Checkbox(
                        checked = cancelarRuta,
                        onCheckedChange = { cancelarRuta = it }
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        "Cancelar ruta después de guardar",
                        fontSize = 14.sp
                    )
                }

                // Botones de acción
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    TextButton(
                        onClick = onDismiss,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Cancelar")
                    }
                    Button(
                        onClick = {
                            if (descripcion.isBlank()) {
                                error = "La descripción es obligatoria"
                            } else {
                                scope.launch {
                                    isLoading = true
                                    error = null
                                    mensajeExito = null
                                    try {
                                        val apiService = authRepository.getApiServiceInstance()

                                        // Preparar partes multipart
                                        val mediaTypeText = "text/plain".toMediaType()
                                        val tipoPart: RequestBody = tipoIncidencia.toRequestBody(mediaTypeText)
                                        val descripcionPart: RequestBody = descripcion.toRequestBody(mediaTypeText)
                                        val cancelarRutaPart: RequestBody = cancelarRuta.toString().toRequestBody(mediaTypeText)

                                        val rutaParadaIdPart: RequestBody? = paradaSeleccionada?.let {
                                            it.toString().toRequestBody(mediaTypeText)
                                        }

                                        // RNF18: compresión de imágenes antes de subir
                                        val fotoParts = archivoFotoActual?.takeIf { it.exists() }?.let { file ->
                                            val compressed = ImageCompression.compressPhotoForUpload(context, file)
                                            val fileToUpload = compressed ?: file
                                            val requestFile = fileToUpload.asRequestBody("image/jpeg".toMediaType())
                                            listOf(
                                                MultipartBody.Part.createFormData(
                                                    "fotos",
                                                    fileToUpload.name,
                                                    requestFile
                                                )
                                            )
                                        } ?: emptyList()

                                        val response = apiService.reportarIncidenciaRuta(
                                            rutaId = rutaId,
                                            tipo = tipoPart,
                                            descripcion = descripcionPart,
                                            rutaParadaId = rutaParadaIdPart,
                                            cancelarRuta = cancelarRutaPart,
                                            fotos = fotoParts
                                        )

                                        if (response.isSuccessful) {
                                            mensajeExito = "Incidencia enviada correctamente"
                                            error = null
                                            // Esperar un momento para que el usuario vea el mensaje
                                            kotlinx.coroutines.delay(1500)
                                            onSuccess()
                                        } else {
                                            mensajeExito = null
                                            val errorBody = response.errorBody()?.string()
                                            val errorMessage = if (errorBody != null && errorBody.isNotBlank()) {
                                                try {
                                                    // Intentar parsear el JSON del error (FastAPI devuelve {"detail": "mensaje"})
                                                    val errorJson = com.google.gson.Gson().fromJson(errorBody, Map::class.java)
                                                    errorJson["detail"]?.toString() ?: errorBody
                                                } catch (e: Exception) {
                                                    errorBody
                                                }
                                            } else {
                                                response.message() ?: "Error al crear incidencia"
                                            }
                                            error = "Error ${response.code()}: $errorMessage"
                                        }
                                    } catch (e: Exception) {
                                        mensajeExito = null
                                        error = e.message ?: "Error al crear incidencia"
                                    } finally {
                                        isLoading = false
                                    }
                                }
                            }
                        },
                        modifier = Modifier.weight(1f),
                        enabled = !isLoading && descripcion.isNotBlank()
                    ) {
                        if (isLoading) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = MaterialTheme.colorScheme.onPrimary
                            )
                        } else {
                            Text(if (cancelarRuta) "Guardar y Cancelar" else "Guardar")
                        }
                    }
                }
            }
        }
    }
}
