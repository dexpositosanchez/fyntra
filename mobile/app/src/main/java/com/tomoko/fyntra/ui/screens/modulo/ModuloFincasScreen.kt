package com.tomoko.fyntra.ui.screens.modulo

import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
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
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.ui.components.AppHeader

@Composable
fun ModuloFincasScreen(
    navController: NavController? = null,
    authDataStore: AuthDataStore? = null,
    authRepository: AuthRepository? = null
) {
    // Navegar directamente a incidencias
    LaunchedEffect(Unit) {
        navController?.navigate("incidencias") {
            popUpTo("modulo_fincas") { inclusive = true }
        }
    }
    
    // Mostrar loading mientras navega
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(Color(0xFFF5F5F5)),
        contentAlignment = Alignment.Center
    ) {
        CircularProgressIndicator(color = Color(0xFF1B9D8A))
    }
}
