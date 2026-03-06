package com.tomoko.fyntra.data.sync

import com.tomoko.fyntra.data.models.IncidenciaCreate

/**
 * Payload para poder mapear una incidencia creada offline (ID local temporal)
 * con el ID real asignado por el backend cuando se sincroniza.
 */
data class PendingCreateIncidenciaPayload(
    val localId: Int,
    val incidencia: IncidenciaCreate
)

