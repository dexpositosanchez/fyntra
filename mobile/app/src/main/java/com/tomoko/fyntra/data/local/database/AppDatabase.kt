package com.tomoko.fyntra.data.local.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.tomoko.fyntra.data.local.database.dao.ActuacionDao
import com.tomoko.fyntra.data.local.database.dao.IncidenciaDao
import com.tomoko.fyntra.data.local.database.dao.DocumentoDao
import com.tomoko.fyntra.data.local.database.dao.MensajeDao
import com.tomoko.fyntra.data.local.database.dao.PendingOperationDao
import com.tomoko.fyntra.data.local.database.dao.RutaDao
import com.tomoko.fyntra.data.local.database.entities.ActuacionEntity
import com.tomoko.fyntra.data.local.database.entities.DocumentoEntity
import com.tomoko.fyntra.data.local.database.entities.IncidenciaEntity
import com.tomoko.fyntra.data.local.database.entities.MensajeEntity
import com.tomoko.fyntra.data.local.database.entities.PendingOperationEntity
import com.tomoko.fyntra.data.local.database.entities.RutaCacheEntity

@Database(
    entities = [
        MensajeEntity::class,
        DocumentoEntity::class,
        ActuacionEntity::class,
        IncidenciaEntity::class,
        PendingOperationEntity::class,
        RutaCacheEntity::class
    ],
    version = 5,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun incidenciaDao(): IncidenciaDao
    abstract fun pendingOperationDao(): PendingOperationDao
    abstract fun rutaDao(): RutaDao
    abstract fun mensajeDao(): MensajeDao
    abstract fun documentoDao(): DocumentoDao
    abstract fun actuacionDao(): ActuacionDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getDatabase(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "fyntra_database"
                )
                    .fallbackToDestructiveMigration() // En desarrollo, en producción usar migraciones
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}
