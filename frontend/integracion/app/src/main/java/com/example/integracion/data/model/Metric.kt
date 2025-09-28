package com.example.integracion.data.model

import java.util.Date

enum class MetricType {
    HEART_RATE,
    SPO2,
    BLOOD_PRESSURE,
    HRV,
    ECG,
    TEMPERATURE // <-- LA LÍNEA QUE FALTABA
}

data class MetricDataPoint(
    val date: Date,
    val value: Float,
    val secondaryValue: Float? = null
)

data class Metric(
    val type: MetricType,
    val title: String,
    val currentValue: String,
    val unit: String,
    val iconResId: Int,
    val iconColor: Int,
    val history: List<MetricDataPoint>,
    val avgValue: Float,
    val minValue: Float,
    val maxValue: Float
)