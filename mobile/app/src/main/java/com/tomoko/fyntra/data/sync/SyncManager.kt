package com.tomoko.fyntra.data.sync

import android.util.Log
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.repository.IncidenciaRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

class SyncManager(
    private val database: AppDatabase,
    private val networkMonitor: NetworkMonitor,
    private val syncService: SyncService,
    private val incidenciaRepository: IncidenciaRepository
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    fun start() {
        // Observar cambios de red y sincronizar automáticamente
        networkMonitor.isOnline
            .onEach { isOnline ->
                if (isOnline) {
                    Log.d("SyncManager", "Internet disponible, sincronizando...")
                    syncAll()
                } else {
                    Log.d("SyncManager", "Sin conexión a internet")
                }
            }
            .launchIn(scope)
    }

    private suspend fun syncAll() {
        try {
            // Sincronizar operaciones pendientes
            val syncResult = syncService.syncPendingOperations()
            when (syncResult) {
                is SyncResult.Success -> {
                    Log.d("SyncManager", "Sincronización exitosa: ${syncResult.syncedCount} operaciones")
                }
                is SyncResult.NoInternet -> {
                    Log.w("SyncManager", "No hay conexión a internet")
                }
            }
            
            // Refrescar datos desde el servidor
            incidenciaRepository.refreshIncidenciasFromServer()
        } catch (e: Exception) {
            Log.e("SyncManager", "Error en sincronización", e)
        }
    }

    fun stop() {
        // Limpiar recursos si es necesario
    }
}
