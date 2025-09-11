package com.example.proyecto.ui.login

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.proyecto.data.model.Result
import com.example.proyecto.data.repo.HeartRepo
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

sealed class LoginState {
    object Idle : LoginState()
    object Success : LoginState()
    data class Error(val msg: String) : LoginState()
}

class LoginViewModel(private val repo: HeartRepo) : ViewModel() {
    private val _state = MutableStateFlow<LoginState>(LoginState.Idle)
    val state = _state.asStateFlow()

    fun login(email: String, pass: String) {
        viewModelScope.launch {
            // Reemplaza el 'if' con un 'when' para que coincida con tu clase Result
            when (val res = repo.login(email, pass)) {
                is Result.Ok -> {
                    _state.value = LoginState.Success
                }
                is Result.Err -> {
                    _state.value = LoginState.Error(res.exception.message ?: "Error desconocido")
                }
            }
        }
    }
}