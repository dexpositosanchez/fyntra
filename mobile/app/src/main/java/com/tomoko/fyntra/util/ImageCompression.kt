package com.tomoko.fyntra.util

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import java.io.File
import java.io.FileOutputStream

/**
 * RNF18: Compresión de imágenes para reducir uso de datos y batería.
 * Redimensiona y comprime fotos/firmas antes de subir al servidor.
 */
object ImageCompression {

    private const val MAX_PHOTO_SIZE_PX = 1024
    private const val PHOTO_JPEG_QUALITY = 80
    private const val MAX_SIGNATURE_SIZE_PX = 800
    private const val SIGNATURE_PNG_QUALITY = 90

    /**
     * Comprime una foto (p. ej. de la cámara) para subir: redimensiona a max 1024px y JPEG 80%.
     * @return Fichero temporal comprimido o null si falla
     */
    fun compressPhotoForUpload(context: Context, sourceFile: File): File? {
        if (!sourceFile.exists()) return null
        return try {
            val opts = BitmapFactory.Options().apply {
                inJustDecodeBounds = true
            }
            BitmapFactory.decodeFile(sourceFile.absolutePath, opts)
            val sampleSize = calculateInSampleSize(opts.outWidth, opts.outHeight, MAX_PHOTO_SIZE_PX)
            val decodeOpts = BitmapFactory.Options().apply {
                inSampleSize = sampleSize
                inJustDecodeBounds = false
            }
            val bitmap = BitmapFactory.decodeFile(sourceFile.absolutePath, decodeOpts) ?: return null
            val scaled = scaleBitmapToMax(bitmap, MAX_PHOTO_SIZE_PX)
            if (scaled != bitmap) bitmap.recycle()
            val outFile = File(context.cacheDir, "compressed_photo_${System.currentTimeMillis()}.jpg")
            FileOutputStream(outFile).use { out ->
                scaled.compress(Bitmap.CompressFormat.JPEG, PHOTO_JPEG_QUALITY, out)
            }
            scaled.recycle()
            outFile
        } catch (e: Exception) {
            null
        }
    }

    /**
     * Comprime un bitmap de firma para subir: redimensiona a max 800px y PNG 90%.
     * @return Fichero temporal comprimido o null si falla
     */
    fun compressSignatureForUpload(context: Context, bitmap: Bitmap): File? {
        return try {
            val scaled = scaleBitmapToMax(bitmap, MAX_SIGNATURE_SIZE_PX)
            val outFile = File(context.cacheDir, "compressed_firma_${System.currentTimeMillis()}.png")
            FileOutputStream(outFile).use { out ->
                scaled.compress(Bitmap.CompressFormat.PNG, SIGNATURE_PNG_QUALITY, out)
            }
            if (scaled != bitmap) scaled.recycle()
            outFile
        } catch (e: Exception) {
            null
        }
    }

    private fun calculateInSampleSize(width: Int, height: Int, maxSize: Int): Int {
        var inSampleSize = 1
        if (width > maxSize || height > maxSize) {
            val halfW = width / 2
            val halfH = height / 2
            while (halfW / inSampleSize >= maxSize && halfH / inSampleSize >= maxSize) {
                inSampleSize *= 2
            }
        }
        return inSampleSize
    }

    private fun scaleBitmapToMax(bitmap: Bitmap, maxSize: Int): Bitmap {
        val w = bitmap.width
        val h = bitmap.height
        if (w <= maxSize && h <= maxSize) return bitmap
        val scale = minOf(maxSize.toFloat() / w, maxSize.toFloat() / h)
        val newW = (w * scale).toInt()
        val newH = (h * scale).toInt()
        val matrix = Matrix().apply { postScale(scale, scale) }
        return Bitmap.createBitmap(bitmap, 0, 0, w, h, matrix, true)
    }
}
