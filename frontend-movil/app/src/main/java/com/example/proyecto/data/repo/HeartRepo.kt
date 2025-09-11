package com.example.proyecto.data.repo

import android.content.Context
import com.example.proyecto.data.model.Result
import com.example.proyecto.data.model.Vital
import kotlinx.coroutines.delay
import java.lang.Exception

// --- YA NO NECESITAMOS LAS IMPORTACIONES DE API ---
// import com.example.proyecto.data.api.ApiClient
// import com.example.proyecto.data.api.AuthApi
// import com.example.proyecto.data.api.LoginRequest
// import com.example.proyecto.data.api.VitalsApi
// import com.example.proyecto.utils.SessionManager

class HeartRepo(private val ctx: Context) {

    /**
     * Simula el inicio de sesión.
     * Ahora, cualquier email y contraseña funcionarán después de un segundo.
     */
    suspend fun login(email: String, pass: String): Result<String> {
        delay(1000) // Simula un pequeño retraso de red
        return Result.Ok("Success")
    }

    /**
     * Simula la obtención del último signo vital.
     * Devuelve siempre el mismo dato inventado.
     */
// ... (dentro de la clase HeartRepo)
    suspend fun latest(): Result<Vital> {
        delay(500)
        return Result.Ok(
            Vital(
                hr = 110, // <-- Valor alto para generar alerta
                spo2 = 98,
                sbp = 120,
                dbp = 80,
                temp_c = 36.5f,
                measured_at = "2023-10-27T10:00:00Z"
            )
        )
    }
// ...

    /**
     * Simula la obtención del historial de signos vitales.
     * Devuelve siempre la misma lista de 4 registros inventados.
     */
    suspend fun list(): Result<List<Vital>> {
        delay(1500) // Simula un pequeño retraso de red
        val dummyList = listOf(
            Vital(hr = 90, spo2 = 99, sbp = 122, dbp = 81, temp_c = 36.8f, measured_at = "2023-10-27T09:45:00Z"),
            Vital(hr = 88, spo2 = 97, sbp = 118, dbp = 79, temp_c = 36.6f, measured_at = "2023-10-27T09:30:00Z"),
            Vital(hr = 92, spo2 = 98, sbp = 125, dbp = 82, temp_c = 37.0f, measured_at = "2023-10-27T09:15:00Z"),
            Vital(hr = 86, spo2 = 99, sbp = 121, dbp = 80, temp_c = 36.7f, measured_at = "2023-10-27T09:00:00Z")
        )
        return Result.Ok(dummyList)
    }

    /**
     * Ya no necesita hacer nada.
     */
    fun clearSession() {
        // No es necesario hacer nada aquí para los datos dummy
    }
}