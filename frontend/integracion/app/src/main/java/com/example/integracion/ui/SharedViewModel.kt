package com.example.integracion.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.integracion.data.model.Alert
import com.example.integracion.data.model.Metric
import com.example.integracion.data.repository.MetricRepository

class SharedViewModel : ViewModel() {

    // ... (código existente de métricas y alertas) ...
    private val _metrics = MutableLiveData<List<Metric>>()
    val metrics: LiveData<List<Metric>> = _metrics

    private val _selectedMetric = MutableLiveData<Metric>()
    val selectedMetric: LiveData<Metric> = _selectedMetric

    private val _alerts = MutableLiveData<List<Alert>>()
    val alerts: LiveData<List<Alert>> = _alerts

    // --- AÑADE ESTAS LÍNEAS ---
    private val _selectedAlert = MutableLiveData<Alert>()
    val selectedAlert: LiveData<Alert> = _selectedAlert
    // -------------------------

    init {
        _metrics.value = MetricRepository.getMetrics()
        _alerts.value = MetricRepository.getAlerts()
    }

    fun selectMetric(metric: Metric) {
        _selectedMetric.value = metric
    }

    // --- AÑADE ESTA NUEVA FUNCIÓN ---
    fun selectAlert(alert: Alert) {
        _selectedAlert.value = alert
    }
    // --------------------------------
}