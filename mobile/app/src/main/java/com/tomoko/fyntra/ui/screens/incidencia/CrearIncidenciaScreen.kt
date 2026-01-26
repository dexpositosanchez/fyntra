package com.tomoko.fyntra.ui.screens.incidencia

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavController
import com.tomoko.fyntra.data.models.IncidenciaCreate
import com.tomoko.fyntra.data.models.InmuebleSimple
import com.tomoko.fyntra.data.api.InmuebleResponse
import com.tomoko.fyntra.data.repository.AuthRepository
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.first

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun CrearIncidenciaScreen(
    navController: NavController,
    authRepository: AuthRepository
) {
    var titulo by remember { mutableStateOf("") }
    var descripcion by remember { mutableStateOf("") }
    var prioridad by remember { mutableStateOf("media") }
    var inmuebleId by remember { mutableStateOf<Int?>(null) }
    var inmuebles by remember { mutableStateOf<List<InmuebleSimple>>(emptyList()) }
    var isLoading by remember { mutableStateOf(false) }
    var error by remember { mutableStateOf<String?>(null) }
    val scope = rememberCoroutineScope()

    val context = LocalContext.current
    val userRol = remember { mutableStateOf<String?>(null) }

    LaunchedEffect(Unit) {
        // Obtener rol del usuario para decidir qué endpoint usar
        val authDataStore = com.tomoko.fyntra.data.local.AuthDataStore(context)
        userRol.value = authDataStore.userRol.first()

        isLoading = true
        try {
            if (userRol.value == "propietario") {
                // Propietarios usan mis-inmuebles
                val response = authRepository.getApiServiceInstance().getMisInmuebles()
                if (response.isSuccessful) {
                    val inmueblesList = response.body()
                    if (inmueblesList != null) {
                        inmuebles = inmueblesList
                        if (inmuebles.isNotEmpty()) {
                            inmuebleId = inmuebles.first().id
                        }
                    }
                } else {
                    error = "Error al cargar inmuebles: ${response.code()} ${response.message()}"
                }
            } else {
                // Admin usa el endpoint general que devuelve todos los inmuebles
                val response = authRepository.getApiServiceInstance().getInmuebles()
                if (response.isSuccessful) {
                    val inmueblesResponse = response.body()
                    if (inmueblesResponse != null) {
                        // Convertir InmuebleResponse a InmuebleSimple
                        inmuebles = inmueblesResponse.map {
                            InmuebleSimple(
                                id = it.id,
                                referencia = it.referencia,
                                direccion = it.direccion ?: ""
                            )
                        }
                        if (inmuebles.isNotEmpty()) {
                            inmuebleId = inmuebles.first().id
                        }
                    }
                } else {
                    error = "Error al cargar inmuebles: ${response.code()} ${response.message()}"
                }
            }
        } catch (e: Exception) {
            error = e.message ?: "Error al cargar inmuebles"
        } finally {
            isLoading = false
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Nueva Incidencia", fontWeight = FontWeight.Bold) },
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
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
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

            OutlinedTextField(
                value = titulo,
                onValueChange = { titulo = it },
                label = { Text("Título *") },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true
            )

            OutlinedTextField(
                value = descripcion,
                onValueChange = { descripcion = it },
                label = { Text("Descripción *") },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(150.dp),
                maxLines = 5
            )

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
                        .menuAnchor()
                )
                ExposedDropdownMenu(
                    expanded = expandedPrioridad,
                    onDismissRequest = { expandedPrioridad = false }
                ) {
                    listOf("baja", "media", "alta", "urgente").forEach { prio ->
                        DropdownMenuItem(
                            text = { Text(prio.replaceFirstChar { it.uppercaseChar() }) },
                            onClick = {
                                prioridad = prio
                                expandedPrioridad = false
                            }
                        )
                    }
                }
            }

            if (inmuebles.isNotEmpty()) {
                var expandedInmueble by remember { mutableStateOf(false) }
                val inmuebleSeleccionado = inmuebles.find { it.id == inmuebleId }
                ExposedDropdownMenuBox(
                    expanded = expandedInmueble,
                    onExpandedChange = { expandedInmueble = !expandedInmueble }
                ) {
                    OutlinedTextField(
                        value = inmuebleSeleccionado?.referencia ?: "Seleccionar inmueble",
                        onValueChange = {},
                        readOnly = true,
                        label = { Text("Inmueble *") },
                        trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expandedInmueble) },
                        modifier = Modifier
                            .fillMaxWidth()
                            .menuAnchor()
                    )
                    ExposedDropdownMenu(
                        expanded = expandedInmueble,
                        onDismissRequest = { expandedInmueble = false }
                    ) {
                        inmuebles.forEach { inmueble ->
                            DropdownMenuItem(
                                text = { Text("${inmueble.referencia} - ${inmueble.direccion}") },
                                onClick = {
                                    inmuebleId = inmueble.id
                                    expandedInmueble = false
                                }
                            )
                        }
                    }
                }
            } else if (!isLoading) {
                Text("No tienes inmuebles disponibles", color = MaterialTheme.colorScheme.error)
            }

            Button(
                onClick = {
                    if (titulo.isNotBlank() && descripcion.isNotBlank() && inmuebleId != null) {
                        scope.launch {
                            isLoading = true
                            error = null
                            try {
                                val nuevaIncidencia = IncidenciaCreate(
                                    titulo = titulo,
                                    descripcion = descripcion,
                                    prioridad = prioridad,
                                    inmueble_id = inmuebleId!!
                                )
                                val response = authRepository.getApiServiceInstance().crearIncidencia(nuevaIncidencia)
                                if (response.isSuccessful) {
                                    navController.popBackStack()
                                } else {
                                    error = response.message() ?: "Error al crear incidencia"
                                }
                            } catch (e: Exception) {
                                error = e.message ?: "Error al crear incidencia"
                            } finally {
                                isLoading = false
                            }
                        }
                    } else {
                        error = "Por favor completa todos los campos"
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                enabled = !isLoading && titulo.isNotBlank() && descripcion.isNotBlank() && inmuebleId != null
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = MaterialTheme.colorScheme.onPrimary
                    )
                } else {
                    Text("Crear Incidencia", fontSize = 16.sp)
                }
            }
        }
    }
}

