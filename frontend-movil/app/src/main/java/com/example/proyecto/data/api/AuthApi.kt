package com.example.proyecto.data.api

import com.example.proyecto.data.model.TokenResponse
import retrofit2.http.Body
import retrofit2.http.POST

data class LoginRequest(val email: String, val password: String)

interface AuthApi {
    @POST("api/auth/login")
    suspend fun login(@Body body: LoginRequest): TokenResponse
}