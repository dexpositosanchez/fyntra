package com.tomoko.fyntra.ui.screens.incidencias

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.tomoko.fyntra.data.local.AuthDataStore
import com.tomoko.fyntra.data.models.Incidencia
import com.tomoko.fyntra.data.repository.IncidenciaRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

data class TabInfo(
    val estado: String,
    val label: String,
    val count: Int
)

data class IncidenciasUiState(
    val loading: Boolean = false,
    val error: String? = null,
    val incidencias: List<Incidencia> = emptyList(),
    val incidenciasFiltradas: List<Incidencia> = emptyList(),
    val tabs: List<TabInfo> = emptyList(),
    val tabActiva: String = "",
    val filtroPrioridad: String? = null
)

class IncidenciasViewModel(
    private val incidenciaRepository: IncidenciaRepository,
    private val authDataStore: AuthDataStore
) : ViewModel() {
    
    private val _uiState = MutableStateFlow(IncidenciasUiState())
    val uiState: StateFlow<IncidenciasUiState> = _uiState.asStateFlow()
    
    private val userRol = authDataStore.userRol
    
    init {
        // Observar cambios en las incidencias del repositorio
        viewModelScope.launch {
            incidenciaRepository.getIncidencias().collect { incidencias ->
                val currentState = _uiState.value
                // Actualizar loading: si estaba cargando y ahora tenemos datos (o lista vacía), dejar de cargar
                val newLoading = if (currentState.loading) {
                    false // Siempre quitar loading cuando recibimos datos del Flow
                } else {
                    currentState.loading
                }
                _uiState.value = currentState.copy(
                    incidencias = incidencias,
                    loading = newLoading
                )
                aplicarFiltros()
            }
        }
        
        // Cargar incidencias al inicializar
        loadIncidencias()
    }
    
    fun loadIncidencias() {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(loading = true, error = null)
            try {
                // Obtener rol del usuario
                val userRol = authDataStore.userRol.first()
                // Refrescar desde el servidor
                incidenciaRepository.refreshIncidenciasFromServer(userRol = userRol)
                // RNF17: El Flow de Room emite al actualizar la BD; no bloquear con delay
                _uiState.value = _uiState.value.copy(loading = false)
            } catch (e: Exception) {
                _uiState.value = _uiState.value.copy(
                    loading = false,
                    error = e.message ?: "Error al cargar incidencias"
                )
            }
        }
    }
    
    fun setFiltroPrioridad(prioridad: String) {
        _uiState.value = _uiState.value.copy(filtroPrioridad = prioridad)
        aplicarFiltros()
    }
    
    fun clearFiltroPrioridad() {
        _uiState.value = _uiState.value.copy(filtroPrioridad = null)
        aplicarFiltros()
    }
    
    fun cambiarTab(estado: String) {
        _uiState.value = _uiState.value.copy(tabActiva = estado)
        aplicarFiltros()
    }
    
    private fun aplicarFiltros() {
        val state = _uiState.value
        var incidenciasFiltradas = state.incidencias
        
        // Primero aplicar filtro de prioridad (si existe)
        if (state.filtroPrioridad != null) {
            incidenciasFiltradas = incidenciasFiltradas.filter { 
                it.prioridad.lowercase() == state.filtroPrioridad.lowercase() 
            }
        }
        
        // Agrupar por estado y crear tabs (usando las incidencias ya filtradas por prioridad)
        val estados = listOf("abierta", "asignada", "en_progreso", "resuelta", "cerrada")
        val incidenciasPorEstado = estados.associateWith { estado ->
            incidenciasFiltradas.filter { it.estado.lowercase() == estado.lowercase() }
        }
        
        val tabs = estados.map { estado ->
            TabInfo(
                estado = estado,
                label = getEstadoLabel(estado),
                count = incidenciasPorEstado[estado]?.size ?: 0
            )
        }.filter { it.count > 0 }
        
        // Establecer tab activa si no hay una o la actual no existe
        var tabActiva = state.tabActiva
        if (tabActiva.isEmpty() || tabs.none { it.estado == tabActiva }) {
            tabActiva = tabs.firstOrNull()?.estado ?: ""
        }
        
        // Ahora filtrar por estado (tab activa) sobre las ya filtradas por prioridad
        if (tabActiva.isNotEmpty()) {
            incidenciasFiltradas = incidenciasFiltradas.filter { 
                it.estado.lowercase() == tabActiva.lowercase() 
            }
        }
        
        _uiState.value = state.copy(
            incidenciasFiltradas = incidenciasFiltradas,
            tabs = tabs,
            tabActiva = tabActiva
        )
    }
    
    private fun getEstadoLabel(estado: String): String {
        return when (estado.lowercase()) {
            "abierta" -> "Abierta"
            "asignada" -> "Asignada"
            "en_progreso" -> "En Progreso"
            "resuelta" -> "Resuelta"
            "cerrada" -> "Cerrada"
            else -> estado
        }
    }
}

class IncidenciasViewModelFactory(
    private val incidenciaRepository: IncidenciaRepository,
    private val authDataStore: AuthDataStore
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(IncidenciasViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return IncidenciasViewModel(incidenciaRepository, authDataStore) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}
