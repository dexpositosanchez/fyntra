package com.tomoko.fyntra.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.settingsDataStore: DataStore<Preferences> by preferencesDataStore(name = "settings_prefs")

/**
 * RNF18: Preferencia "Sincronizar solo por WiFi" para ahorrar datos móviles.
 */
class SettingsDataStore(private val context: Context) {

    companion object {
        private val SYNC_ONLY_WIFI_KEY = booleanPreferencesKey("sync_only_wifi")
    }

    val syncOnlyWifi: Flow<Boolean> = context.settingsDataStore.data.map { prefs ->
        prefs[SYNC_ONLY_WIFI_KEY] ?: false
    }

    suspend fun setSyncOnlyWifi(enabled: Boolean) {
        context.settingsDataStore.edit { prefs ->
            prefs[SYNC_ONLY_WIFI_KEY] = enabled
        }
    }
}
