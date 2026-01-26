package com.tomoko.fyntra.data.local.database

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import com.tomoko.fyntra.data.local.database.dao.IncidenciaDao
import com.tomoko.fyntra.data.local.database.dao.PendingOperationDao
import com.tomoko.fyntra.data.local.database.entities.IncidenciaEntity
import com.tomoko.fyntra.data.local.database.entities.PendingOperationEntity

@Database(
    entities = [
        IncidenciaEntity::class,
        PendingOperationEntity::class
    ],
    version = 2,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {
    abstract fun incidenciaDao(): IncidenciaDao
    abstract fun pendingOperationDao(): PendingOperationDao

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
