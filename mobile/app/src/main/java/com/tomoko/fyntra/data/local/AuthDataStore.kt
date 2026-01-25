package com.tomoko.fyntra.data.local

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "auth_prefs")

class AuthDataStore(private val context: Context) {
    companion object {
        private val TOKEN_KEY = stringPreferencesKey("access_token")
        private val USER_ID_KEY = stringPreferencesKey("user_id")
        private val USER_EMAIL_KEY = stringPreferencesKey("user_email")
        private val USER_NOMBRE_KEY = stringPreferencesKey("user_nombre")
        private val USER_ROL_KEY = stringPreferencesKey("user_rol")
    }

    private var cachedToken: String? = null

    val token: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[TOKEN_KEY].also { cachedToken = it }
    }

    val userId: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[USER_ID_KEY]
    }

    val userEmail: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[USER_EMAIL_KEY]
    }

    val userNombre: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[USER_NOMBRE_KEY]
    }

    val userRol: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[USER_ROL_KEY]
    }

    suspend fun saveToken(token: String) {
        cachedToken = token
        context.dataStore.edit { preferences ->
            preferences[TOKEN_KEY] = token
        }
    }

    suspend fun saveUser(userId: String, email: String, nombre: String, rol: String) {
        context.dataStore.edit { preferences ->
            preferences[USER_ID_KEY] = userId
            preferences[USER_EMAIL_KEY] = email
            preferences[USER_NOMBRE_KEY] = nombre
            preferences[USER_ROL_KEY] = rol
        }
    }

    suspend fun clear() {
        cachedToken = null
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }

    suspend fun getToken(): String? {
        return cachedToken ?: token.first()
    }
}

