package com.tomoko.fyntra.data.models

data class Ruta(
    val id: Int,
    val nombre: String,
    val conductor_id: Int,
    val vehiculo_id: Int,
    val fecha: String,
    val estado: String,
    val conductor: Conductor? = null,
    val vehiculo: Vehiculo? = null,
    val paradas: List<Parada>? = null
)

data class Parada(
    val id: Int,
    val ruta_id: Int,
    val pedido_id: Int,
    val orden: Int,
    val direccion: String,
    val fecha_hora_carga: String? = null,
    val fecha_hora_descarga: String? = null,
    val estado: String,
    val pedido: Pedido? = null
)

data class Pedido(
    val id: Int,
    val cliente: String,
    val direccion: String,
    val estado: String,
    val fecha_entrega: String? = null
)

data class Conductor(
    val id: Int,
    val nombre: String,
    val apellidos: String? = null,
    val email: String? = null
)

data class Vehiculo(
    val id: Int,
    val matricula: String,
    val marca: String? = null,
    val modelo: String? = null
)

