package com.tomoko.fyntra.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.repository.AuthRepository
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.tomoko.fyntra.ui.screens.conductor.ConductorHomeScreen
import com.tomoko.fyntra.ui.screens.incidencia.CrearIncidenciaScreen
import com.tomoko.fyntra.ui.screens.incidencia.IncidenciaDetailScreen
import com.tomoko.fyntra.ui.screens.login.LoginScreen
import com.tomoko.fyntra.ui.screens.modulo.ModuloFincasScreen
import com.tomoko.fyntra.ui.screens.modulo.ModuloSelectorScreen
import com.tomoko.fyntra.ui.screens.modulo.ModuloTransportesScreen
import com.tomoko.fyntra.ui.screens.propietario.PropietarioHomeScreen
import com.tomoko.fyntra.ui.screens.proveedor.ProveedorHomeScreen
import com.tomoko.fyntra.ui.screens.incidencias.IncidenciasScreen
import com.tomoko.fyntra.data.repository.IncidenciaRepository

sealed class Screen(val route: String) {
    object Login : Screen("login")
    object ModuloSelector : Screen("modulo_selector")
    object ModuloFincas : Screen("modulo_fincas")
    object ModuloTransportes : Screen("modulo_transportes")
    object Incidencias : Screen("incidencias")
    object ConductorHome : Screen("conductor_home")
    object PropietarioHome : Screen("propietario_home")
    object ProveedorHome : Screen("proveedor_home")
}

@Composable
fun NavGraph(
    navController: NavHostController = rememberNavController(),
    authDataStore: AuthDataStore,
    authRepository: AuthRepository,
    incidenciaRepository: IncidenciaRepository
) {
    val userRol by authDataStore.userRol.collectAsState(initial = null)
    val isLoggedIn by authDataStore.token.collectAsState(initial = null)
    val userId by authDataStore.userId.collectAsState(initial = null)

    NavHost(
        navController = navController,
        startDestination = if (isLoggedIn != null && userRol != null) {
            when (userRol) {
                "super_admin" -> Screen.ModuloSelector.route
                "admin_fincas", "propietario", "proveedor" -> Screen.ModuloFincas.route
                "admin_transportes", "conductor" -> Screen.ModuloTransportes.route
                else -> Screen.Login.route
            }
        } else {
            Screen.Login.route
        }
    ) {
        composable(Screen.Login.route) {
            LoginScreen(
                onLoginSuccess = { rol ->
                    val destination = when (rol) {
                        "super_admin" -> Screen.ModuloSelector.route
                        "admin_fincas" -> Screen.ModuloFincas.route
                        "propietario" -> Screen.ModuloFincas.route
                        "proveedor" -> Screen.ModuloFincas.route
                        "admin_transportes" -> Screen.ModuloTransportes.route
                        "conductor" -> Screen.ModuloTransportes.route
                        else -> Screen.Login.route
                    }
                    navController.navigate(destination) {
                        popUpTo(Screen.Login.route) { inclusive = true }
                    }
                },
                authRepository = authRepository
            )
        }

        composable(Screen.ModuloSelector.route) {
            ModuloSelectorScreen(
                navController = navController,
                authDataStore = authDataStore,
                authRepository = authRepository
            )
        }

        composable(Screen.ModuloFincas.route) {
            ModuloFincasScreen(
                navController = navController,
                authDataStore = authDataStore,
                authRepository = authRepository
            )
        }

        composable(Screen.ModuloTransportes.route) {
            ModuloTransportesScreen(
                navController = navController,
                authDataStore = authDataStore,
                authRepository = authRepository
            )
        }

        composable(Screen.Incidencias.route) {
            IncidenciasScreen(
                navController = navController,
                authDataStore = authDataStore,
                authRepository = authRepository,
                incidenciaRepository = incidenciaRepository
            )
        }

        composable(Screen.ConductorHome.route) {
            ConductorHomeScreen(navController, authRepository)
        }

        composable(Screen.PropietarioHome.route) {
            PropietarioHomeScreen(navController, authRepository)
        }

        composable(Screen.ProveedorHome.route) {
            ProveedorHomeScreen(navController, authRepository)
        }

        composable("crear_incidencia") {
            CrearIncidenciaScreen(navController, authRepository)
        }

        composable(
            route = "incidencia_detail/{incidenciaId}",
            arguments = listOf(navArgument("incidenciaId") { type = NavType.IntType })
        ) { backStackEntry ->
            val incidenciaId = backStackEntry.arguments?.getInt("incidenciaId") ?: 0
            val userRolValue = userRol ?: ""
            val userIdValue = userId?.toIntOrNull()
            IncidenciaDetailScreen(
                incidenciaId = incidenciaId,
                userRol = userRolValue,
                navController = navController,
                authRepository = authRepository,
                userId = userIdValue
            )
        }
        
        // Rutas para navegar directamente a tabs específicos
        composable(
            route = "incidencia_detail/{incidenciaId}/historial",
            arguments = listOf(navArgument("incidenciaId") { type = NavType.IntType })
        ) { backStackEntry ->
            val incidenciaId = backStackEntry.arguments?.getInt("incidenciaId") ?: 0
            val userRolValue = userRol ?: ""
            val userIdValue = userId?.toIntOrNull()
            IncidenciaDetailScreen(
                incidenciaId = incidenciaId,
                userRol = userRolValue,
                navController = navController,
                authRepository = authRepository,
                userId = userIdValue,
                initialTab = 1
            )
        }
        
        composable(
            route = "incidencia_detail/{incidenciaId}/documentos",
            arguments = listOf(navArgument("incidenciaId") { type = NavType.IntType })
        ) { backStackEntry ->
            val incidenciaId = backStackEntry.arguments?.getInt("incidenciaId") ?: 0
            val userRolValue = userRol ?: ""
            val userIdValue = userId?.toIntOrNull()
            IncidenciaDetailScreen(
                incidenciaId = incidenciaId,
                userRol = userRolValue,
                navController = navController,
                authRepository = authRepository,
                userId = userIdValue,
                initialTab = 2
            )
        }
        
        composable(
            route = "incidencia_detail/{incidenciaId}/chat",
            arguments = listOf(navArgument("incidenciaId") { type = NavType.IntType })
        ) { backStackEntry ->
            val incidenciaId = backStackEntry.arguments?.getInt("incidenciaId") ?: 0
            val userRolValue = userRol ?: ""
            val userIdValue = userId?.toIntOrNull()
            IncidenciaDetailScreen(
                incidenciaId = incidenciaId,
                userRol = userRolValue,
                navController = navController,
                authRepository = authRepository,
                userId = userIdValue,
                initialTab = 3
            )
        }
        
        composable(
            route = "incidencia_detail/{incidenciaId}/actuaciones",
            arguments = listOf(navArgument("incidenciaId") { type = NavType.IntType })
        ) { backStackEntry ->
            val incidenciaId = backStackEntry.arguments?.getInt("incidenciaId") ?: 0
            val userRolValue = userRol ?: ""
            val userIdValue = userId?.toIntOrNull()
            IncidenciaDetailScreen(
                incidenciaId = incidenciaId,
                userRol = userRolValue,
                navController = navController,
                authRepository = authRepository,
                userId = userIdValue,
                initialTab = 4
            )
        }
    }
}

