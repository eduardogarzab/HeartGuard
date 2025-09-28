package com.example.integracion // Asegúrate que el paquete sea el tuyo

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
// No es necesario importar R si está en el mismo paquete

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // La referencia a R.layout.activity_main ahora funcionará
        setContentView(R.layout.activity_main)
    }
}