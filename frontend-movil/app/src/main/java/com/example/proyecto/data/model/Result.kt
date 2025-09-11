package com.example.proyecto.data.model

import java.lang.Exception

sealed class Result<out T : Any> {
    data class Ok<out T : Any>(val data: T) : Result<T>()
    data class Err(val exception: Exception, val message: String? = exception.localizedMessage) : Result<Nothing>()
}