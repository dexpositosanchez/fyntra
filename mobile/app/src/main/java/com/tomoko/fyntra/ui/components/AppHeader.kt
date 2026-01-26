package com.tomoko.fyntra.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.navigation.NavController
import com.tomoko.fyntra.R
import com.tomoko.fyntra.data.local.AuthDataStore

@Composable
fun AppHeader(
    onLogout: () -> Unit,
    navController: NavController? = null,
    authDataStore: AuthDataStore? = null,
    mostrarMenuModulos: Boolean = true,
    moduloActual: String? = null, // "fincas" o "transportes"
    modifier: Modifier = Modifier
) {
    val userRol by authDataStore?.userRol?.collectAsState(initial = null) ?: remember { mutableStateOf(null) }
    val esAdmin = userRol == "super_admin" || userRol == "admin_fincas" || userRol == "admin_transportes"
    
    // Determinar el módulo destino
    val moduloDestino = when (moduloActual) {
        "fincas" -> "transportes"
        "transportes" -> "fincas"
        else -> null
    }
    
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Image(
            painter = painterResource(id = R.drawable.logotipo),
            contentDescription = "Fyntra Logo",
            modifier = Modifier.size(120.dp)
        )
        
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            // Botón para cambiar de módulo (solo para admin y solo si mostrarMenuModulos es true)
            if (esAdmin && mostrarMenuModulos && moduloDestino != null && navController != null) {
                IconButton(
                    onClick = {
                        when (moduloDestino) {
                            "transportes" -> navController.navigate("modulo_transportes") {
                                popUpTo(0) { inclusive = false }
                            }
                            "fincas" -> navController.navigate("incidencias") {
                                popUpTo(0) { inclusive = false }
                            }
                        }
                    }
                ) {
                    // Icono según el módulo destino
                    Text(
                        text = when (moduloDestino) {
                            "transportes" -> "🚚"
                            "fincas" -> "🏢"
                            else -> "📦"
                        },
                        fontSize = 24.sp
                    )
                }
            }
            
            IconButton(
                onClick = onLogout
            ) {
                Icon(
                    imageVector = Icons.Filled.ExitToApp,
                    contentDescription = "Cerrar sesión",
                    tint = Color(0xFF1B9D8A),
                    modifier = Modifier.size(24.dp)
                )
            }
        }
    }
}
