package com.tomoko.fyntra.ui.screens.modulo

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.tomoko.fyntra.R
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.ui.components.AppHeader

@Composable
fun ModuloSelectorScreen(
    navController: NavController,
    authDataStore: AuthDataStore,
    authRepository: AuthRepository
) {
    val userName by authDataStore.userNombre.collectAsState(initial = null)
    
    var shouldLogout by remember { mutableStateOf(false) }
    
    LaunchedEffect(shouldLogout) {
        if (shouldLogout) {
            authRepository.logout()
            navController.navigate("login") {
                popUpTo(0) { inclusive = true }
            }
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F5))
    ) {
        // Header con botón de logout
        AppHeader(
            onLogout = { shouldLogout = true }
        )

        // Welcome section
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                text = "Bienvenido, ${userName ?: "Usuario"}",
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                color = Color(0xFF2F343D),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Selecciona el módulo al que deseas acceder",
                fontSize = 16.sp,
                color = Color(0xFF6F7785),
                textAlign = TextAlign.Center
            )
        }

        // Modules grid
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(24.dp),
            horizontalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Módulo Fincas
            ModuloCard(
                title = "Administración de Fincas",
                description = "Gestión de comunidades, propietarios e incidencias",
                features = listOf("Comunidades", "Incidencias", "Propietarios"),
                icon = R.drawable.isotipo,
                onClick = {
                    navController.navigate("modulo_fincas") {
                        popUpTo("modulo_selector") { inclusive = false }
                    }
                }
            )

            // Módulo Transportes
            ModuloCard(
                title = "ERP de Transportes",
                description = "Gestión de flota, rutas y pedidos",
                features = listOf("Vehículos", "Rutas", "Pedidos"),
                icon = R.drawable.isotipo,
                onClick = {
                    navController.navigate("modulo_transportes") {
                        popUpTo("modulo_selector") { inclusive = false }
                    }
                }
            )
        }
    }
}

@Composable
fun RowScope.ModuloCard(
    title: String,
    description: String,
    features: List<String>,
    icon: Int,
    onClick: () -> Unit
) {
    Card(
        modifier = Modifier
            .weight(1f)
            .height(300.dp)
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp),
        colors = CardDefaults.cardColors(
            containerColor = Color.White
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Image(
                painter = painterResource(id = icon),
                contentDescription = title,
                modifier = Modifier.size(80.dp),
                contentScale = ContentScale.Fit
            )

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                Text(
                    text = title,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFF2F343D),
                    textAlign = TextAlign.Center
                )
                Text(
                    text = description,
                    fontSize = 14.sp,
                    color = Color(0xFF6F7785),
                    textAlign = TextAlign.Center
                )
            }

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                features.forEach { feature ->
                    Surface(
                        shape = RoundedCornerShape(4.dp),
                        color = Color(0xFFE8F5E9)
                    ) {
                        Text(
                            text = feature,
                            fontSize = 12.sp,
                            color = Color(0xFF1B9D8A),
                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                        )
                    }
                }
            }
        }
    }
}
