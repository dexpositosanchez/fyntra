package com.tomoko.fyntra.data.sync

import android.util.Log
import com.tomoko.fyntra.data.local.SettingsDataStore
import com.tomoko.fyntra.data.local.database.AppDatabase
import com.tomoko.fyntra.data.repository.IncidenciaRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.onEach
import kotlinx.coroutines.launch

/**
 * RNF18: Si "sincronizar solo por WiFi" está activo, solo sincroniza cuando hay WiFi.
 */
class SyncManager(
    private val database: AppDatabase,
    private val networkMonitor: NetworkMonitor,
    private val syncService: SyncService,
    private val incidenciaRepository: IncidenciaRepository,
    private val settingsDataStore: SettingsDataStore
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    fun start() {
        combine(
            networkMonitor.isOnline,
            networkMonitor.isWifi,
            settingsDataStore.syncOnlyWifi
        ) { isOnline, isWifi, syncOnlyWifi ->
            Triple(isOnline, isWifi, syncOnlyWifi)
        }.onEach { (isOnline, isWifi, syncOnlyWifi) ->
            val shouldSync = isOnline && (!syncOnlyWifi || isWifi)
            if (shouldSync) {
                Log.d("SyncManager", "Internet disponible, sincronizando...")
                syncAll()
            } else if (!isOnline) {
                Log.d("SyncManager", "Sin conexión a internet")
            } else if (syncOnlyWifi && !isWifi) {
                Log.d("SyncManager", "Sincronización solo por WiFi activada; conexión no es WiFi")
            }
        }.launchIn(scope)
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
