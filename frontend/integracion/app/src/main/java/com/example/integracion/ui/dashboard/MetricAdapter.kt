package com.example.integracion.ui.dashboard

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.integracion.data.model.Metric
import com.example.integracion.databinding.ItemMetricCardBinding

class MetricAdapter(
    private val metrics: List<Metric>,
    private val onItemClick: (Metric) -> Unit
) : RecyclerView.Adapter<MetricAdapter.MetricViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MetricViewHolder {
        val binding = ItemMetricCardBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return MetricViewHolder(binding)
    }

    override fun onBindViewHolder(holder: MetricViewHolder, position: Int) {
        val metric = metrics[position]
        holder.bind(metric)
        holder.itemView.setOnClickListener { onItemClick(metric) }
    }

    override fun getItemCount(): Int = metrics.size

    class MetricViewHolder(private val binding: ItemMetricCardBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(metric: Metric) {
            binding.metricTitle.text = metric.title
            binding.metricValue.text = metric.currentValue
            binding.metricUnit.text = metric.unit

            // Asigna el ícono y el color desde el modelo de datos
            binding.metricIcon.setImageResource(metric.iconResId)
            binding.metricIcon.setColorFilter(
                itemView.context.getColor(metric.iconColor)
            )
        }
    }
}