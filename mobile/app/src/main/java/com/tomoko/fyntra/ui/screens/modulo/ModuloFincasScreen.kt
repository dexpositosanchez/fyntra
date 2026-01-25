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
    var shouldLogout by remember { mutableStateOf(false) }
    
    LaunchedEffect(shouldLogout) {
        if (shouldLogout && authRepository != null) {
            authRepository.logout()
            navController?.navigate("login") {
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
        if (navController != null && authRepository != null) {
            AppHeader(
                onLogout = { shouldLogout = true }
            )
        }
        
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
        Image(
            painter = painterResource(id = R.drawable.imagotipo),
            contentDescription = "Fyntra Logo",
            modifier = Modifier.size(150.dp)
        )
        
        Spacer(modifier = Modifier.height(32.dp))
        
        Text(
            text = "Módulo de Administración de Fincas",
            fontSize = 24.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF2F343D),
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(16.dp))
        
        Text(
            text = "Has accedido correctamente al módulo de Administración de Fincas",
            fontSize = 16.sp,
            color = Color(0xFF6F7785),
            textAlign = TextAlign.Center
        )
        
        Spacer(modifier = Modifier.height(8.dp))
        
        Text(
            text = "Aquí podrás gestionar comunidades, propietarios e incidencias",
            fontSize = 14.sp,
            color = Color(0xFF8A94A6),
            textAlign = TextAlign.Center
        )
        }
    }
}
