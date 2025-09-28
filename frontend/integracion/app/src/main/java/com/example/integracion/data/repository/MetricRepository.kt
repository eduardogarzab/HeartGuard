package com.example.integracion.data.repository

import com.example.integracion.R
import com.example.integracion.data.model.Metric
import com.example.integracion.data.model.MetricDataPoint
import com.example.integracion.data.model.MetricType
import java.util.Date
import kotlin.random.Random

object MetricRepository {

    fun getMetrics(): List<Metric> {
        return listOf(
            Metric(
                type = MetricType.HEART_RATE,
                title = "Frecuencia Cardíaca",
                currentValue = "75",
                unit = "LPM",
                iconResId = R.drawable.ic_heart_rate,
                iconColor = R.color.metric_heart,
                history = generateRandomData(60f, 100f),
                avgValue = 78.5f,
                minValue = 65f,
                maxValue = 92f
            ),
            Metric(
                type = MetricType.SPO2,
                title = "Saturación de Oxígeno",
                currentValue = "98",
                unit = "%",
                iconResId = R.drawable.ic_spo2,
                iconColor = R.color.metric_spo2,
                history = generateRandomData(95f, 99f),
                avgValue = 97.2f,
                minValue = 95f,
                maxValue = 99f
            ),
            Metric(
                type = MetricType.BLOOD_PRESSURE,
                title = "Presión Arterial",
                currentValue = "120/80",
                unit = "mmHg",
                iconResId = R.drawable.ic_blood_pressure,
                iconColor = R.color.metric_bp,
                history = generateRandomData(110f, 130f, 70f, 85f),
                avgValue = 122f,
                minValue = 115f,
                maxValue = 128f
            ),
            // --- NUEVO BLOQUE DE TEMPERATURA AÑADIDO ---
            Metric(
                type = MetricType.TEMPERATURE,
                title = "Temperatura",
                currentValue = "36.8",
                unit = "°C",
                iconResId = R.drawable.ic_temperature,
                iconColor = R.color.metric_temp,
                history = generateRandomData(36.5f, 37.2f),
                avgValue = 36.9f,
                minValue = 36.6f,
                maxValue = 37.1f
            )
            // -------------------------------------------
        )
    }

    private fun generateRandomData(min: Float, max: Float, min2: Float? = null, max2: Float? = null): List<MetricDataPoint> {
        val data = mutableListOf<MetricDataPoint>()
        val now = Date().time
        for (i in 0..10) {
            val date = Date(now - (10 - i) * 3600000) // Datos por hora
            val value = Random.nextFloat() * (max - min) + min
            val secondaryValue = if (min2 != null && max2 != null) Random.nextFloat() * (max2 - min2) + min2 else null
            data.add(MetricDataPoint(date, value, secondaryValue))
        }
        return data
    }
}