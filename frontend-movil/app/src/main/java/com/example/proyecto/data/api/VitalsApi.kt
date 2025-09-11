package com.example.proyecto.data.api

import com.example.proyecto.data.model.Vital // <-- AÑADE ESTA LÍNEA
import retrofit2.http.GET
import retrofit2.http.Query

interface VitalsApi {
    @GET("api/vitals/latest")
    suspend fun latest(): Vital

    @GET("api/vitals")
    suspend fun list(@Query("limit") limit: Int = 50): List<Vital>
}