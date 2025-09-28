package com.example.integracion.ui.alerts

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.integracion.data.model.AlertLevel
import com.example.integracion.databinding.FragmentAlertDetailBinding
import com.example.integracion.ui.SharedViewModel
import java.text.SimpleDateFormat
import java.util.*

class AlertDetailFragment : Fragment() {

    private var _binding: FragmentAlertDetailBinding? = null
    private val binding get() = _binding!!
    private val sharedViewModel: SharedViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentAlertDetailBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Botón para regresar a la lista de alertas
        binding.backButton.setOnClickListener {
            findNavController().navigateUp()
        }

        // Observar la alerta seleccionada y actualizar la UI
        sharedViewModel.selectedAlert.observe(viewLifecycleOwner) { alert ->
            alert?.let {
                binding.detailAlertTitle.text = it.title
                binding.detailAlertDescription.text = it.description
                binding.detailAlertLevel.text = it.level.displayName

                val sdf = SimpleDateFormat("dd MMM, hh:mm a", Locale.getDefault())
                binding.detailAlertDate.text = sdf.format(it.date)

                // Cambiar el color del nivel de riesgo
                val colorRes = when (it.level) {
                    AlertLevel.CRITICAL -> android.R.color.holo_red_dark
                    AlertLevel.HIGH -> android.R.color.holo_orange_dark
                    AlertLevel.MEDIUM -> android.R.color.holo_orange_light
                    else -> android.R.color.holo_green_light
                }
                binding.detailAlertLevel.setTextColor(requireContext().getColor(colorRes))
            }
        }

        // Lógica del botón de acción (por ahora, un simple mensaje)
        binding.resolveButton.setOnClickListener {
            Toast.makeText(context, "Alerta marcada como resuelta", Toast.LENGTH_SHORT).show()
            findNavController().navigateUp()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}