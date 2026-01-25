package com.tomoko.fyntra.data.models

data class Usuario(
    val id: Int,
    val nombre: String,
    val email: String,
    val rol: String,
    val activo: Boolean,
    val creado_en: String? = null
)

data class LoginRequest(
    val email: String,
    val password: String
)

data class LoginResponse(
    val access_token: String,
    val token_type: String,
    val usuario: Usuario
)

