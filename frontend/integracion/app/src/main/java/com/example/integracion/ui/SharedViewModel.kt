package com.example.integracion.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.integracion.data.model.Alert
import com.example.integracion.data.model.Metric
import com.example.integracion.data.repository.MetricRepository

class SharedViewModel : ViewModel() {

    // LiveData para la lista completa de métricas
    private val _metrics = MutableLiveData<List<Metric>>()
    val metrics: LiveData<List<Metric>> = _metrics

    // LiveData para la métrica seleccionada que se verá en detalle
    private val _selectedMetric = MutableLiveData<Metric>()
    val selectedMetric: LiveData<Metric> = _selectedMetric

    // LiveData para la lista de alertas
    private val _alerts = MutableLiveData<List<Alert>>()
    val alerts: LiveData<List<Alert>> = _alerts

    // El bloque init se ejecuta cuando se crea el ViewModel por primera vez
    init {
        // Cargar los datos iniciales desde el repositorio
        _metrics.value = MetricRepository.getMetrics()
        _alerts.value = MetricRepository.getAlerts()
    }

    // Función para actualizar la métrica seleccionada cuando el usuario toca una tarjeta
    fun selectMetric(metric: Metric) {
        _selectedMetric.value = metric
    }
}