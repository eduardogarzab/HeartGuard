package com.example.proyecto.data.api

import com.example.proyecto.utils.AuthInterceptor // <-- AÑADE ESTA LÍNEA
import com.google.gson.GsonBuilder
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory

object ApiClient {
    private const val AUTH_BASE = "http://10.0.2.2:8001/"
    private const val VITALS_BASE = "http://10.0.2.2:8002/"

    fun authRetrofit(): Retrofit =
        Retrofit.Builder()
            .baseUrl(AUTH_BASE)
            .addConverterFactory(GsonConverterFactory.create(GsonBuilder().create()))
            .client(
                OkHttpClient.Builder()
                    .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY })
                    .build()
            )
            .build()

    fun vitalsRetrofit(tokenProvider: () -> String?): Retrofit =
        Retrofit.Builder()
            .baseUrl(VITALS_BASE)
            .addConverterFactory(GsonConverterFactory.create(GsonBuilder().create()))
            .client(
                OkHttpClient.Builder()
                    .addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BODY })
                    .addInterceptor(AuthInterceptor(tokenProvider))
                    .build()
            )
            .build()
}