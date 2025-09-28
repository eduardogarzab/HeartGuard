package com.example.integracion.ui.alerts

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.integracion.R
import com.example.integracion.databinding.FragmentAlertsBinding
import com.example.integracion.ui.SharedViewModel

class AlertsFragment : Fragment() {

    private var _binding: FragmentAlertsBinding? = null
    private val binding get() = _binding!!
    private val sharedViewModel: SharedViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentAlertsBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        sharedViewModel.alerts.observe(viewLifecycleOwner) { alerts ->
            binding.alertsRecyclerView.apply {
                layoutManager = LinearLayoutManager(context)
                // --- CAMBIO: Pasar el listener al adaptador ---
                adapter = AlertAdapter(alerts) { selectedAlert ->
                    // Guardar la alerta seleccionada en el ViewModel
                    sharedViewModel.selectAlert(selectedAlert)
                    // Navegar a la pantalla de detalle
                    findNavController().navigate(R.id.action_alertsFragment_to_alertDetailFragment)
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}