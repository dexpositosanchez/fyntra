package com.tomoko.fyntra.ui.screens.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import com.tomoko.fyntra.data.repository.AuthRepository
import com.tomoko.fyntra.data.repository.IncidenciaRepository

class LoginViewModelFactory(
    private val authRepository: AuthRepository,
    private val incidenciaRepository: IncidenciaRepository
) : ViewModelProvider.Factory {
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(LoginViewModel::class.java)) {
            @Suppress("UNCHECKED_CAST")
            return LoginViewModel(authRepository, incidenciaRepository) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

