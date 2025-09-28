package com.example.integracion.data.model // Asegúrate que el paquete sea el tuyo

import java.util.Date

enum class MetricType {
    HEART_RATE,
    SPO2,
    BLOOD_PRESSURE,
    HRV,
    ECG
}

data class MetricDataPoint(
    val date: Date,
    val value: Float,
    val secondaryValue: Float? = null
)

// ... (imports y otras clases)

data class Metric(
    val type: MetricType,
    val title: String,
    val currentValue: String,
    val unit: String,
    val iconResId: Int, // <-- AÑADIDO
    val iconColor: Int, // <-- AÑADIDO
    val history: List<MetricDataPoint>,
    val avgValue: Float,
    val minValue: Float,
    val maxValue: Float
)