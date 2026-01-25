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
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.Parada
import com.tomoko.fyntra.data.models.Ruta
import com.tomoko.fyntra.data.repository.AuthRepository

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
    var showConfirmarEntregaDialog by remember { mutableStateOf<Parada?>(null) }

    LaunchedEffect(rutaId) {
        isLoading = true
        try {
            val response = authRepository.getApiServiceInstance().getRuta(rutaId)
            if (response.isSuccessful) {
                ruta = response.body()
            } else {
                error = "Error al cargar la ruta"
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
                title = { Text(ruta?.nombre ?: "Ruta", fontWeight = FontWeight.Bold) },
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
            if (ruta?.estado == "pendiente") {
                FloatingActionButton(
                    onClick = {
                        // Iniciar ruta
                        // TODO: Implementar
                    }
                ) {
                    Icon(
                        imageVector = androidx.compose.material.icons.Icons.Default.PlayArrow,
                        contentDescription = "Iniciar Ruta"
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
                Text(error!!, color = MaterialTheme.colorScheme.error)
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
                            Text("Vehículo: ${ruta!!.vehiculo?.matricula ?: "N/A"}", fontSize = 16.sp)
                            Text("Fecha: ${ruta!!.fecha}", fontSize = 16.sp)
                            Text("Estado: ${ruta!!.estado}", fontSize = 16.sp, fontWeight = FontWeight.Bold)
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
                        onConfirmarEntrega = {
                            showConfirmarEntregaDialog = parada
                        },
                        onReportarIncidencia = {
                            navController.navigate("reportar_incidencia_ruta/${ruta!!.id}/${parada.id}")
                        }
                    )
                }
            }
        }

        // Dialog para confirmar entrega
        showConfirmarEntregaDialog?.let { parada ->
            ConfirmarEntregaDialog(
                parada = parada,
                rutaId = rutaId,
                onDismiss = { showConfirmarEntregaDialog = null },
                authRepository = authRepository
            )
        }
    }
}

@Composable
fun ParadaCard(
    parada: Parada,
    onConfirmarEntrega: () -> Unit,
    onReportarIncidencia: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = "Orden ${parada.orden}",
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Text("Dirección: ${parada.direccion}")
            Text("Cliente: ${parada.pedido?.cliente ?: "N/A"}")
            Text("Estado: ${parada.estado}")
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                if (parada.estado == "pendiente" || parada.estado == "en_camino") {
                    Button(
                        onClick = onConfirmarEntrega,
                        modifier = Modifier.weight(1f)
                    ) {
                        Text("Confirmar Entrega")
                    }
                }
                OutlinedButton(
                    onClick = onReportarIncidencia,
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Reportar Incidencia")
                }
            }
        }
    }
}

@Composable
fun ConfirmarEntregaDialog(
    parada: Parada,
    rutaId: Int,
    onDismiss: () -> Unit,
    authRepository: AuthRepository
) {
    // TODO: Implementar dialog con firma y foto
    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("Confirmar Entrega") },
        text = { Text("Funcionalidad en desarrollo") },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("OK")
            }
        }
    )
}

