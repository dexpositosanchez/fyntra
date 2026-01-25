package com.tomoko.fyntra

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.google.gson.Gson
import com.tomoko.fyntra.data.api.RetrofitModule
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.data.repository.IncidenciaRepository
import com.tomoko.fyntra.data.sync.NetworkMonitor
import com.tomoko.fyntra.data.sync.SyncManager
import com.tomoko.fyntra.data.sync.SyncService
import com.tomoko.fyntra.ui.navigation.NavGraph
import com.tomoko.fyntra.ui.theme.FyntraTheme

class MainActivity : ComponentActivity() {
    private lateinit var database: AppDatabase
    private lateinit var authDataStore: AuthDataStore
    private lateinit var authRepository: AuthRepository
    private lateinit var networkMonitor: NetworkMonitor
    private lateinit var syncService: SyncService
    private lateinit var incidenciaRepository: IncidenciaRepository
    private lateinit var syncManager: SyncManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Inicializar componentes
        initializeComponents()
        
        enableEdgeToEdge()
        setContent {
            FyntraTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    NavGraph(
                        authDataStore = authDataStore,
                        authRepository = authRepository
                    )
                }
            }
        }
    }

    private fun initializeComponents() {
        // Base de datos
        database = AppDatabase.getDatabase(this)
        
        // Auth
        authDataStore = AuthDataStore(this)
        authRepository = AuthRepository(authDataStore)
        
        // Network monitor
        networkMonitor = NetworkMonitor(this)
        
        // API Service
        val apiService = RetrofitModule.createApiServiceWithToken(
            authDataStore,
            null
        )
        
        // Gson
        val gson = Gson()
        
        // Sync Service
        syncService = SyncService(
            database = database,
            apiService = apiService,
            networkMonitor = networkMonitor,
            gson = gson
        )
        
        // Repositorios
        incidenciaRepository = IncidenciaRepository(
            apiService = apiService,
            database = database,
            networkMonitor = networkMonitor,
            syncService = syncService
        )
        
        // Sync Manager
        syncManager = SyncManager(
            database = database,
            networkMonitor = networkMonitor,
            syncService = syncService,
            incidenciaRepository = incidenciaRepository
        )
        
        // Iniciar sincronización automática
        syncManager.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        syncManager.stop()
    }
}
