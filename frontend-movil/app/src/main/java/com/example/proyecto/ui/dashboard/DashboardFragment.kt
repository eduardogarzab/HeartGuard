package com.example.proyecto.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.core.view.isVisible
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.proyecto.R
import com.example.proyecto.data.repo.HeartRepo
import kotlinx.coroutines.flow.collectLatest

class DashboardFragment : Fragment() {
    private val vm: DashboardViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return DashboardViewModel(HeartRepo(requireContext())) as T
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_dashboard, container, false)
        v.findViewById<View>(R.id.btnHistory).setOnClickListener {
            findNavController().navigate(R.id.action_dashboard_to_history)
        }
        return v
    }

    override fun onResume() {
        super.onResume()
        vm.load()
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        val tvVitals = view.findViewById<TextView>(R.id.tvVitals)
        val tvAlertsTitle = view.findViewById<TextView>(R.id.tvAlertsTitle)
        val rvAlerts = view.findViewById<RecyclerView>(R.id.rvAlerts)

        // Configurar el adapter para las alertas
        val alertAdapter = AlertAdapter()
        rvAlerts.layoutManager = LinearLayoutManager(context)
        rvAlerts.adapter = alertAdapter

        viewLifecycleOwner.lifecycleScope.launchWhenStarted {
            vm.vital.collectLatest { v ->
                v?.let {
                    tvVitals.text = "HR ${it.hr} bpm • SpO2 ${it.spo2}%\nPA ${it.sbp}/${it.dbp} mmHg • T ${it.temp_c}°C\n${it.measured_at}"
                }
            }
        }

        // Observar la lista de alertas y actualizar la UI
        viewLifecycleOwner.lifecycleScope.launchWhenStarted {
            vm.alerts.collectLatest { alerts ->
                alertAdapter.submitList(alerts)
                tvAlertsTitle.isVisible = alerts.isNotEmpty()
            }
        }
    }
}