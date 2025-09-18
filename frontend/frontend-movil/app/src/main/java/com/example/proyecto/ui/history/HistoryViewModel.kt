package com.example.proyecto.ui.history

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.proyecto.data.model.Result
import com.example.proyecto.data.model.Vital
import com.example.proyecto.data.repo.HeartRepo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class HistoryViewModel(private val repo: HeartRepo) : ViewModel() {
    private val _vitals = MutableStateFlow<List<Vital>>(emptyList())
    val vitals = _vitals.asStateFlow()
    private val _error = MutableStateFlow<String?>(null)
    val error = _error.asStateFlow()

    fun load() {
        viewModelScope.launch {
            when (val r = repo.list()) {
                is Result.Ok -> _vitals.value = r.data
                is Result.Err -> _error.value = r.message
            }
        }
    }
}