package com.tomoko.fyntra.ui.screens.conductor

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.Ruta
import com.tomoko.fyntra.data.repository.AuthRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ConductorHomeScreen(
    navController: NavController,
    authRepository: AuthRepository
) {
    var rutas by remember { mutableStateOf<List<Ruta>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showMenu by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        isLoading = true
        try {
            val response = authRepository.getApiServiceInstance().getMisRutas()
            if (response.isSuccessful) {
                rutas = response.body() ?: emptyList()
            } else {
                error = "Error al cargar rutas"
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
                title = { Text("Mis Rutas", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                ),
                actions = {
                    IconButton(onClick = { showMenu = true }) {
                        Icon(Icons.Default.MoreVert, contentDescription = "Menú")
                    }
                    DropdownMenu(
                        expanded = showMenu,
                        onDismissRequest = { showMenu = false }
                    ) {
                        DropdownMenuItem(
                            text = { Text("Cerrar Sesión") },
                            onClick = {
                                scope.launch {
                                    authRepository.logout()
                                    navController.navigate("login") {
                                        popUpTo(0) { inclusive = true }
                                    }
                                }
                            }
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (isLoading) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            } else if (error != null) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text(error!!, color = MaterialTheme.colorScheme.error)
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(onClick = { /* Retry */ }) {
                            Text("Reintentar")
                        }
                    }
                }
            } else if (rutas.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text("No tienes rutas asignadas")
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(rutas) { ruta ->
                        RutaCard(
                            ruta = ruta,
                            onRutaClick = {
                                // TODO: Navegar a detalle de ruta
                            }
                        )
                    }
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
            Text(
                text = ruta.nombre ?: "Ruta #${ruta.id}",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Text("Vehículo: ${ruta.vehiculo?.matricula ?: "N/A"}")
            Text("Fecha: ${ruta.fecha ?: "N/A"}")
            Text("Estado: ${ruta.estado}")
            Text("Paradas: ${ruta.paradas?.size ?: 0}")
        }
    }
}

