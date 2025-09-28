package com.example.integracion

import android.os.Bundle
import android.view.View
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.fragment.NavHostFragment
import androidx.navigation.ui.setupWithNavController
import com.google.android.material.bottomnavigation.BottomNavigationView

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        val navHostFragment = supportFragmentManager
            .findFragmentById(R.id.nav_host_fragment) as NavHostFragment
        val navController = navHostFragment.navController

        val bottomNavView = findViewById<BottomNavigationView>(R.id.bottomNavView)
        bottomNavView.setupWithNavController(navController)

        // --- LÓGICA AÑADIDA PARA OCULTAR/MOSTRAR EL MENÚ ---
        navController.addOnDestinationChangedListener { _, destination, _ ->
            when (destination.id) {
                // En estas pantallas, el menú es visible
                R.id.dashboardFragment,
                R.id.alertsFragment -> {
                    bottomNavView.visibility = View.VISIBLE
                }
                // En cualquier otra pantalla (como login o detalle), se oculta
                else -> {
                    bottomNavView.visibility = View.GONE
                }
            }
        }
        // ---------------------------------------------------
    }
}