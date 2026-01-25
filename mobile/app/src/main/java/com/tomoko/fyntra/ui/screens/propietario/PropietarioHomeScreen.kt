package com.tomoko.fyntra.ui.screens.propietario

import androidx.compose.foundation.clickable
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
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.repository.AuthRepository
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PropietarioHomeScreen(
    navController: NavController,
    authRepository: AuthRepository
) {
    var incidencias by remember { mutableStateOf<List<Incidencia>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    var showMenu by remember { mutableStateOf(false) }
    val scope = rememberCoroutineScope()

    LaunchedEffect(Unit) {
        isLoading = true
        try {
            val response = authRepository.getApiServiceInstance().getIncidencias()
            if (response.isSuccessful) {
                incidencias = response.body() ?: emptyList()
            } else {
                error = "Error al cargar incidencias"
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
                title = { Text("Mis Incidencias", fontWeight = FontWeight.Bold) },
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
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { navController.navigate("crear_incidencia") }
            ) {
                Icon(
                    imageVector = androidx.compose.material.icons.Icons.Default.Add,
                    contentDescription = "Nueva Incidencia"
                )
            }
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
            } else if (incidencias.isEmpty()) {
                Box(
                    modifier = Modifier.fillMaxSize(),
                    contentAlignment = Alignment.Center
                ) {
                    Text("No hay incidencias")
                }
            } else {
                LazyColumn(
                    modifier = Modifier.fillMaxSize(),
                    contentPadding = PaddingValues(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(incidencias) { incidencia ->
                        IncidenciaCard(
                            incidencia = incidencia,
                            onIncidenciaClick = {
                                navController.navigate("incidencia_detail/${incidencia.id}")
                            },
                            onHistorialClick = {
                                navController.navigate("incidencia_detail/${incidencia.id}/historial")
                            },
                            onDocumentosClick = {
                                navController.navigate("incidencia_detail/${incidencia.id}/documentos")
                            },
                            onChatClick = {
                                navController.navigate("incidencia_detail/${incidencia.id}/chat")
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
    onIncidenciaClick: () -> Unit,
    onHistorialClick: (() -> Unit)? = null,
    onDocumentosClick: (() -> Unit)? = null,
    onChatClick: (() -> Unit)? = null
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onIncidenciaClick() },
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            Text(
                text = incidencia.titulo,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Text("Estado: ${incidencia.estado}")
            Text("Prioridad: ${incidencia.prioridad}")
            Text("Inmueble: ${incidencia.inmueble?.referencia ?: "N/A"}")
            
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceEvenly
            ) {
                if (onHistorialClick != null) {
                    TextButton(
                        onClick = { onHistorialClick() },
                        modifier = Modifier.weight(1f)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = "Histórico",
                                fontSize = 12.sp
                            )
                            Text(
                                text = "${incidencia.historial?.size ?: 0}",
                                fontSize = 10.sp
                            )
                        }
                    }
                }
                if (onDocumentosClick != null) {
                    TextButton(
                        onClick = { onDocumentosClick() },
                        modifier = Modifier.weight(1f)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = "Docs",
                                fontSize = 12.sp
                            )
                            Text(
                                text = "${incidencia.documentos_count}",
                                fontSize = 10.sp
                            )
                        }
                    }
                }
                if (onChatClick != null) {
                    TextButton(
                        onClick = { onChatClick() },
                        modifier = Modifier.weight(1f)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text(
                                text = "Chat",
                                fontSize = 12.sp
                            )
                            Text(
                                text = "${incidencia.mensajes_count}",
                                fontSize = 10.sp
                            )
                        }
                    }
                }
            }
        }
    }
}

