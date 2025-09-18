package com.example.proyecto.data.model

data class Vital(
    val hr: Int,
    val spo2: Int,
    val sbp: Int,
    val dbp: Int,
    val temp_c: Float,
    val measured_at: String
)