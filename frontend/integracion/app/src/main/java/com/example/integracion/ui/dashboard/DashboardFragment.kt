package com.example.integracion.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import androidx.recyclerview.widget.LinearLayoutManager
import com.example.integracion.R
import com.example.integracion.databinding.FragmentDashboardBinding
import com.example.integracion.ui.SharedViewModel // Asegúrate que la ruta sea correcta

class DashboardFragment : Fragment() {

    private var _binding: FragmentDashboardBinding? = null
    private val binding get() = _binding!!

    // Usamos el SharedViewModel, no el DashboardViewModel
    private val sharedViewModel: SharedViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentDashboardBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        sharedViewModel.metrics.observe(viewLifecycleOwner) { metrics ->
            binding.metricsRecyclerView.apply {
                layoutManager = LinearLayoutManager(context)
                adapter = MetricAdapter(metrics) { selectedMetric ->
                    sharedViewModel.selectMetric(selectedMetric)
                    // Esta línea ahora funcionará gracias al ID que asignaste
                    findNavController().navigate(R.id.action_dashboardFragment_to_detailFragment)
                }
            }
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}