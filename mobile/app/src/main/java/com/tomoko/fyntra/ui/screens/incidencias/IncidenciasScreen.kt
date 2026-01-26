package com.tomoko.fyntra.ui.screens.incidencias

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Search
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavController
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.data.repository.IncidenciaRepository
import com.tomoko.fyntra.ui.components.AppHeader
import kotlinx.coroutines.launch

@Composable
fun IncidenciasScreen(
    navController: NavController,
    authDataStore: AuthDataStore,
    authRepository: AuthRepository,
    incidenciaRepository: IncidenciaRepository,
    viewModel: IncidenciasViewModel = viewModel(
        factory = IncidenciasViewModelFactory(incidenciaRepository, authDataStore)
    )
) {
    val uiState by viewModel.uiState.collectAsState()
    val userRol by authDataStore.userRol.collectAsState(initial = null)
    val scope = rememberCoroutineScope()
    
    var shouldLogout by remember { mutableStateOf(false) }
    
    LaunchedEffect(shouldLogout) {
        if (shouldLogout) {
            authRepository.logout()
            navController.navigate("login") {
                popUpTo(0) { inclusive = true }
            }
        }
    }
    
    LaunchedEffect(Unit) {
        viewModel.loadIncidencias()
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F5))
    ) {
        // Header con botón de logout y cambio de módulo
        AppHeader(
            onLogout = { shouldLogout = true },
            navController = navController,
            authDataStore = authDataStore,
            moduloActual = "fincas"
        )
        
        // Título y botón de crear (solo para admin y propietarios)
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = when (userRol) {
                    "proveedor" -> "Mis Incidencias Asignadas"
                    "propietario" -> "Mis Incidencias"
                    else -> "Incidencias"
                },
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF2F343D)
            )
            
            // Botón crear solo para admin y propietarios
            if (userRol != "proveedor") {
                FloatingActionButton(
                    onClick = { navController.navigate("crear_incidencia") },
                    modifier = Modifier.size(40.dp),
                    containerColor = Color(0xFF1B9D8A),
                    contentColor = Color.White
                ) {
                    Icon(
                        imageVector = Icons.Default.Add,
                        contentDescription = "Nueva incidencia",
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
        
        // Filtro de prioridad
        var mostrarFiltro by remember { mutableStateOf(false) }
        
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            FilterChip(
                selected = uiState.filtroPrioridad != null,
                onClick = { mostrarFiltro = !mostrarFiltro },
                label = {
                    Text(
                        text = uiState.filtroPrioridad?.let { "Prioridad: ${it.capitalize()}" } ?: "Filtrar por prioridad",
                        fontSize = 12.sp
                    )
                },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = Color(0xFF1B9D8A),
                    selectedLabelColor = Color.White
                )
            )
            
            if (uiState.filtroPrioridad != null) {
                TextButton(onClick = { viewModel.clearFiltroPrioridad() }) {
                    Text("Limpiar", fontSize = 12.sp, color = Color(0xFF1B9D8A))
                }
            }
        }
        
        // Dropdown de prioridades
        if (mostrarFiltro) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp, vertical = 8.dp),
                shape = RoundedCornerShape(8.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
            ) {
                Column(
                    modifier = Modifier.padding(8.dp)
                ) {
                    listOf("urgente", "alta", "media", "baja").forEach { prioridad ->
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { 
                                    viewModel.setFiltroPrioridad(prioridad)
                                    mostrarFiltro = false
                                }
                                .padding(12.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            RadioButton(
                                selected = uiState.filtroPrioridad == prioridad,
                                onClick = { 
                                    viewModel.setFiltroPrioridad(prioridad)
                                    mostrarFiltro = false
                                }
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = prioridad.capitalize(),
                                fontSize = 14.sp,
                                color = getPrioridadColor(prioridad)
                            )
                        }
                    }
                }
            }
        }
        
        // Tabs por estado
        if (uiState.tabs.isNotEmpty()) {
            ScrollableTabRow(
                selectedTabIndex = uiState.tabs.indexOfFirst { it.estado == uiState.tabActiva },
                modifier = Modifier.fillMaxWidth(),
                containerColor = Color.White,
                contentColor = Color(0xFF1B9D8A),
                edgePadding = 16.dp
            ) {
                uiState.tabs.forEachIndexed { index, tab ->
                    Tab(
                        selected = uiState.tabActiva == tab.estado,
                        onClick = { viewModel.cambiarTab(tab.estado) },
                        text = {
                            Text(
                                text = "${tab.label} (${tab.count})",
                                fontSize = 12.sp
                            )
                        }
                    )
                }
            }
        }
        
        // Lista de incidencias
        when {
            uiState.loading -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = Color(0xFF1B9D8A))
                }
            }
            uiState.error != null -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Text(
                            text = "Error al cargar incidencias",
                            color = Color(0xFFD32F2F),
                            fontSize = 16.sp
                        )
                        Text(
                            text = uiState.error ?: "",
                            color = Color(0xFF6F7785),
                            fontSize = 14.sp
                        )
                        Button(
                            onClick = { viewModel.loadIncidencias() },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = Color(0xFF1B9D8A)
                            )
                        ) {
                            Text("Reintentar")
                        }
                    }
                }
            }
            uiState.incidenciasFiltradas.isEmpty() -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No hay incidencias",
                        color = Color(0xFF6F7785),
                        fontSize = 16.sp
                    )
                }
            }
            else -> {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(uiState.incidenciasFiltradas) { incidencia ->
                        IncidenciaCard(
                            incidencia = incidencia,
                            userRol = userRol,
                            onClick = {
                                navController.navigate("incidencia_detail/${incidencia.id}")
                            }
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun IncidenciaCard(
    incidencia: Incidencia,
    userRol: String?,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color.White
        )
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Header con prioridad y estado
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = getPrioridadColor(incidencia.prioridad).copy(alpha = 0.1f)
                ) {
                    Text(
                        text = incidencia.prioridad.capitalize(),
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        color = getPrioridadColor(incidencia.prioridad)
                    )
                }
                
                Surface(
                    shape = RoundedCornerShape(4.dp),
                    color = getEstadoColor(incidencia.estado).copy(alpha = 0.1f)
                ) {
                    Text(
                        text = getEstadoLabel(incidencia.estado),
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium,
                        color = getEstadoColor(incidencia.estado)
                    )
                }
            }
            
            // Título
            Text(
                text = incidencia.titulo,
                fontSize = 16.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF2F343D),
                maxLines = 2,
                overflow = TextOverflow.Ellipsis
            )
            
            // Descripción (si existe)
            if (!incidencia.descripcion.isNullOrBlank()) {
                Text(
                    text = incidencia.descripcion,
                    fontSize = 14.sp,
                    color = Color(0xFF6F7785),
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
            }
            
            // Inmueble
            if (incidencia.inmueble != null) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        text = "📍",
                        fontSize = 14.sp
                    )
                    Text(
                        text = "${incidencia.inmueble.referencia} - ${incidencia.inmueble.direccion}",
                        fontSize = 12.sp,
                        color = Color(0xFF6F7785),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            
            // Proveedor (si está asignado)
            if (incidencia.proveedor != null) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(
                        text = "🏢",
                        fontSize = 14.sp
                    )
                    Text(
                        text = incidencia.proveedor.nombre,
                        fontSize = 12.sp,
                        color = Color(0xFF6F7785),
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }
            
            // Fecha
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(
                    text = "📅",
                    fontSize = 14.sp
                )
                Text(
                    text = formatDate(incidencia.fecha_alta),
                    fontSize = 12.sp,
                    color = Color(0xFF6F7785)
                )
            }
            
            // Contadores (actuaciones, documentos)
            if (incidencia.actuaciones_count > 0 || incidencia.documentos_count > 0) {
                Row(
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    if (incidencia.actuaciones_count > 0) {
                        Text(
                            text = "🔧 ${incidencia.actuaciones_count} actuación${if (incidencia.actuaciones_count > 1) "es" else ""}",
                            fontSize = 11.sp,
                            color = Color(0xFF6F7785)
                        )
                    }
                    if (incidencia.documentos_count > 0) {
                        Text(
                            text = "📎 ${incidencia.documentos_count} documento${if (incidencia.documentos_count > 1) "s" else ""}",
                            fontSize = 11.sp,
                            color = Color(0xFF6F7785)
                        )
                    }
                }
            }
        }
    }
}

fun getPrioridadColor(prioridad: String): Color {
    return when (prioridad.lowercase()) {
        "urgente" -> Color(0xFFD32F2F)
        "alta" -> Color(0xFFE67C2F)
        "media" -> Color(0xFFF4C542)
        "baja" -> Color(0xFF2F7D4C)
        else -> Color(0xFF6F7785)
    }
}

fun getEstadoColor(estado: String): Color {
    return when (estado.lowercase()) {
        "abierta" -> Color(0xFF2196F3)
        "asignada" -> Color(0xFF9C27B0)
        "en_progreso" -> Color(0xFFF4C542)
        "resuelta" -> Color(0xFF2F7D4C)
        "cerrada" -> Color(0xFF6F7785)
        else -> Color(0xFF6F7785)
    }
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

fun formatDate(dateString: String): String {
    return try {
        val formatos = listOf(
            "yyyy-MM-dd'T'HH:mm:ss.SSSSSS",
            "yyyy-MM-dd'T'HH:mm:ss",
            "yyyy-MM-dd HH:mm:ss",
            "yyyy-MM-dd"
        )
        var fecha: java.util.Date? = null
        for (formato in formatos) {
            try {
                val sdf = java.text.SimpleDateFormat(formato, java.util.Locale("es", "ES"))
                sdf.timeZone = java.util.TimeZone.getTimeZone("UTC")
                fecha = sdf.parse(dateString)
                if (fecha != null) break
            } catch (e: Exception) {
                continue
            }
        }
        if (fecha != null) {
            val formatoSalida = java.text.SimpleDateFormat("dd/MM/yyyy", java.util.Locale("es", "ES"))
            formatoSalida.format(fecha)
        } else {
            dateString
        }
    } catch (e: Exception) {
        dateString
    }
}
