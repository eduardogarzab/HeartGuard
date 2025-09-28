package com.example.integracion.ui.detail

import android.graphics.Color
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.activityViewModels
import androidx.navigation.fragment.findNavController
import com.example.integracion.R
import com.example.integracion.data.model.Metric
import com.example.integracion.databinding.FragmentDetailBinding
import com.example.integracion.ui.SharedViewModel
import com.github.mikephil.charting.components.XAxis
import com.github.mikephil.charting.data.Entry
import com.github.mikephil.charting.data.LineData
import com.github.mikephil.charting.data.LineDataSet

class DetailFragment : Fragment() {

    private var _binding: FragmentDetailBinding? = null
    private val binding get() = _binding!!

    private val sharedViewModel: SharedViewModel by activityViewModels()

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentDetailBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)

        // Configura el listener del botón para regresar
        binding.backButton.setOnClickListener {
            findNavController().navigateUp()
        }

        // Observa los datos de la métrica seleccionada
        sharedViewModel.selectedMetric.observe(viewLifecycleOwner) { metric ->
            metric?.let {
                binding.detailTitle.text = it.title
                binding.avgStat.text = "Promedio\n${it.avgValue}"
                binding.minStat.text = "Mínimo\n${it.minValue}"
                binding.maxStat.text = "Máximo\n${it.maxValue}"
                setupChart(it)
            }
        }
    }

    private fun setupChart(metric: Metric) {
        val entries = metric.history.mapIndexed { index, dataPoint ->
            Entry(index.toFloat(), dataPoint.value)
        }

        val dataSet = LineDataSet(entries, metric.title).apply {
            mode = LineDataSet.Mode.CUBIC_BEZIER
            color = requireContext().getColor(metric.iconColor)
            highLightColor = requireContext().getColor(metric.iconColor)
            setDrawValues(false)
            lineWidth = 2.5f

            setDrawCircles(true)
            setCircleColor(requireContext().getColor(metric.iconColor))
            circleRadius = 4f
            setDrawCircleHole(false)

            setDrawFilled(true)
            fillDrawable = ContextCompat.getDrawable(requireContext(), R.drawable.chart_gradient)
        }

        binding.metricChart.apply {
            data = LineData(dataSet)
            description.isEnabled = false
            legend.isEnabled = false

            xAxis.setDrawGridLines(false)
            xAxis.position = XAxis.XAxisPosition.BOTTOM
            axisLeft.setDrawGridLines(false)
            axisLeft.axisLineColor = Color.TRANSPARENT
            axisRight.isEnabled = false

            setTouchEnabled(true)
            setPinchZoom(true)

            invalidate()
        }
    }

    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}