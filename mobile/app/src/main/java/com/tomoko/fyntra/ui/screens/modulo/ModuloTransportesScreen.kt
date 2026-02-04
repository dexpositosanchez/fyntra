package com.tomoko.fyntra.ui.screens.modulo

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.tomoko.fyntra.R
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.models.Ruta
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.ui.components.AppHeader
import kotlinx.coroutines.launch

@Composable
fun ModuloTransportesScreen(
    navController: NavController? = null,
    authDataStore: AuthDataStore? = null,
    authRepository: AuthRepository? = null
) {
    var shouldLogout by remember { mutableStateOf(false) }
    var rutas by remember { mutableStateOf<List<Ruta>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val userRol by authDataStore?.userRol?.collectAsState(initial = null) ?: remember { mutableStateOf(null) }
    val scope = rememberCoroutineScope()
    
    LaunchedEffect(shouldLogout) {
        if (shouldLogout && authRepository != null) {
            authRepository.logout()
            navController?.navigate("login") {
                popUpTo(0) { inclusive = true }
            }
        }
    }
    
    // Cargar rutas solo si es conductor
    LaunchedEffect(userRol) {
        if (userRol == "conductor" && authRepository != null) {
            isLoading = true
            try {
                val response = authRepository.getApiServiceInstance().getMisRutas()
                if (response.isSuccessful) {
                    rutas = response.body() ?: emptyList()
                    error = null
                } else {
                    val errorBody = response.errorBody()?.string()
                    error = "Error al cargar rutas: ${response.code()} - ${response.message()}\n$errorBody"
                }
            } catch (e: Exception) {
                error = "Error: ${e.message}\n${e.stackTraceToString()}"
            } finally {
                isLoading = false
            }
        }
    }
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F5))
    ) {
        // Header con botón de logout y cambio de módulo
        if (navController != null && authRepository != null) {
            AppHeader(
                onLogout = { shouldLogout = true },
                navController = navController,
                authDataStore = authDataStore,
                moduloActual = "transportes"
            )
        }
        
        when {
            // Super admin y admin transportes: mensaje para usar la web
            userRol == "super_admin" || userRol == "admin_transportes" -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                        modifier = Modifier.padding(24.dp)
                    ) {
        Text(
                            text = "Módulo de Transportes",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF2F343D),
            textAlign = TextAlign.Center
        )
        Spacer(modifier = Modifier.height(16.dp))
        Text(
                            text = "Los administradores deben usar la aplicación web para gestionar rutas",
            fontSize = 16.sp,
            color = Color(0xFF6F7785),
            textAlign = TextAlign.Center
        )
                    }
                }
            }
            
            // Conductor: mostrar rutas
            userRol == "conductor" -> {
                if (isLoading) {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator()
                    }
                } else if (error != null) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = error!!,
                                color = MaterialTheme.colorScheme.error,
                                textAlign = TextAlign.Center
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Button(onClick = {
                                scope.launch {
                                    isLoading = true
                                    try {
                                        val response = authRepository?.getApiServiceInstance()?.getMisRutas()
                                        if (response?.isSuccessful == true) {
                                            rutas = response.body() ?: emptyList()
                                            error = null
                                        }
                                    } catch (e: Exception) {
                                        error = e.message
                                    } finally {
                                        isLoading = false
                                    }
                                }
                            }) {
                                Text("Reintentar")
                            }
                        }
                    }
                } else {
                    // Separar rutas por estado
                    val rutasEnProgreso = rutas.filter { it.estado == "en_curso" }
                    val rutasPlanificadas = rutas.filter { it.estado == "planificada" }
                    val rutasCompletadas = rutas.filter { it.estado == "completada" }
                    
                    // Ordenar: primero En progreso, luego Planificadas
                    val rutasOrdenadas = mutableListOf<Ruta>()
                    rutasOrdenadas.addAll(rutasEnProgreso)
                    rutasOrdenadas.addAll(rutasPlanificadas)
                    rutasOrdenadas.addAll(rutasCompletadas)
                    
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(16.dp),
                        verticalArrangement = Arrangement.spacedBy(16.dp)
                    ) {
                        // Título de sección: En progreso
                        if (rutasEnProgreso.isNotEmpty()) {
                            item {
                                Text(
                                    text = "En Progreso",
                                    fontSize = 20.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(vertical = 8.dp)
                                )
                            }
                            items(rutasEnProgreso) { ruta ->
                                RutaCard(
                                    ruta = ruta,
                                    onRutaClick = {
                                        navController?.navigate("ruta_detail/${ruta.id}")
                                    }
                                )
                            }
                        }
                        
                        // Título de sección: Planificadas
                        if (rutasPlanificadas.isNotEmpty()) {
                            item {
                                Text(
                                    text = "Planificadas",
                                    fontSize = 20.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(vertical = 8.dp)
                                )
                            }
                            items(rutasPlanificadas) { ruta ->
                                RutaCard(
                                    ruta = ruta,
                                    onRutaClick = {
                                        navController?.navigate("ruta_detail/${ruta.id}")
                                    }
                                )
                            }
                        }
                        
                        // Título de sección: Completadas
                        if (rutasCompletadas.isNotEmpty()) {
                            item {
                                Text(
                                    text = "Completadas",
                                    fontSize = 20.sp,
                                    fontWeight = FontWeight.Bold,
                                    modifier = Modifier.padding(vertical = 8.dp)
                                )
                            }
                            items(rutasCompletadas) { ruta ->
                                RutaCard(
                                    ruta = ruta,
                                    onRutaClick = {
                                        navController?.navigate("ruta_detail/${ruta.id}")
                                    }
                                )
                            }
                        }
                        
                        // Mensaje si no hay rutas
                        if (rutas.isEmpty()) {
                            item {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(32.dp),
                                    contentAlignment = Alignment.Center
                                ) {
        Text(
                                        text = "No tienes rutas asignadas",
                                        fontSize = 16.sp,
                                        color = Color(0xFF6F7785),
            textAlign = TextAlign.Center
        )
                                }
                            }
                        }
                    }
                }
            }
            
            // Otros casos
            else -> {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "Acceso no autorizado",
                        fontSize = 18.sp,
                        color = MaterialTheme.colorScheme.error
                    )
                }
            }
        }
    }
}

@Composable
fun RutaCard(
    ruta: Ruta,
    onRutaClick: () -> Unit
) {
    Card(
        onClick = onRutaClick,
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
                    text = "Ruta #${ruta.id}",
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
                // Badge de estado
                Surface(
                    color = when (ruta.estado) {
                        "en_curso" -> Color(0xFFFF9800)
                        "planificada" -> Color(0xFF2196F3)
                        "completada" -> Color(0xFF4CAF50)
                        else -> Color(0xFF9E9E9E)
                    },
                    shape = MaterialTheme.shapes.small
                ) {
                    Text(
                        text = when (ruta.estado) {
                            "en_curso" -> "En Progreso"
                            "planificada" -> "Planificada"
                            "completada" -> "Completada"
                            else -> ruta.estado
                        },
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                        fontSize = 12.sp,
                        color = Color.White,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            
            if (ruta.vehiculo != null) {
                Text("Vehículo: ${ruta.vehiculo.matricula}")
            }
            if (ruta.fecha != null) {
                Text("Fecha: ${ruta.fecha}")
            }
            Text("Paradas: ${ruta.paradas?.size ?: 0}")
            
            // Mostrar paradas completadas vs totales
            val paradasCompletadas = ruta.paradas?.count { it.estado == "entregado" } ?: 0
            val totalParadas = ruta.paradas?.size ?: 0
            if (totalParadas > 0) {
                Text(
                    text = "Progreso: $paradasCompletadas/$totalParadas paradas completadas",
                    fontSize = 14.sp,
                    color = if (paradasCompletadas == totalParadas) Color(0xFF4CAF50) else Color(0xFF6F7785)
                )
            }
        }
    }
}
