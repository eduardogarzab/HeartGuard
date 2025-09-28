package com.example.integracion.ui

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import com.example.integracion.data.model.Metric
import com.example.integracion.data.repository.MetricRepository

class SharedViewModel : ViewModel() {

    private val _metrics = MutableLiveData<List<Metric>>()
    val metrics: LiveData<List<Metric>> = _metrics

    private val _selectedMetric = MutableLiveData<Metric>()
    val selectedMetric: LiveData<Metric> = _selectedMetric

    init {
        // Esta línea usa MetricRepository y Metric, y ahora debería funcionar
        _metrics.value = MetricRepository.getMetrics()
    }

    fun selectMetric(metric: Metric) {
        _selectedMetric.value = metric
    }
}