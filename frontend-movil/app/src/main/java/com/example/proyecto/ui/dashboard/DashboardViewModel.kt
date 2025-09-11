package com.example.proyecto.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.proyecto.data.model.Result
import com.example.proyecto.data.model.Vital
import com.example.proyecto.data.repo.HeartRepo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

// Data class para representar una alerta
data class Alert(val title: String, val type: String)

class DashboardViewModel(private val repo: HeartRepo) : ViewModel() {
    private val _vital = MutableStateFlow<Vital?>(null)
    val vital = _vital.asStateFlow()

    private val _alerts = MutableStateFlow<List<Alert>>(emptyList())
    val alerts = _alerts.asStateFlow()

    private val _error = MutableStateFlow<String?>(null)
    val error = _error.asStateFlow()

    fun load() {
        viewModelScope.launch {
            when (val r = repo.latest()) {
                is Result.Ok -> {
                    _vital.value = r.data
                    _alerts.value = generateAlerts(r.data) // Generar alertas con los datos
                }
                is Result.Err -> _error.value = r.message
            }
        }
    }

    // Lógica para generar alertas basadas en los valores de los signos vitales
    private fun generateAlerts(vital: Vital): List<Alert> {
        val alerts = mutableListOf<Alert>()
        if (vital.hr > 100) alerts.add(Alert("Heart Rate Alert", "Ritmo cardíaco alto"))
        if (vital.spo2 < 95) alerts.add(Alert("SpO2 Level Alert", "Nivel de oxígeno bajo"))
        if (vital.sbp > 140 || vital.dbp > 90) alerts.add(Alert("Blood Pressure Alert", "Presión arterial alta"))
        if (vital.temp_c > 38) alerts.add(Alert("Temperature Alert", "Temperatura alta"))
        return alerts
    }
}