package com.example.integracion.ui.alerts

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.RecyclerView
import com.example.integracion.data.model.Alert
import com.example.integracion.data.model.AlertLevel
import com.example.integracion.databinding.ItemAlertCardBinding
import java.text.SimpleDateFormat
import java.util.Locale

// --- CAMBIO: Añadir el listener en el constructor ---
class AlertAdapter(
    private val alerts: List<Alert>,
    private val onItemClick: (Alert) -> Unit
) : RecyclerView.Adapter<AlertAdapter.AlertViewHolder>() {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): AlertViewHolder {
        val binding = ItemAlertCardBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return AlertViewHolder(binding)
    }

    override fun onBindViewHolder(holder: AlertViewHolder, position: Int) {
        val alert = alerts[position]
        holder.bind(alert)
        // --- CAMBIO: Asignar el listener al item ---
        holder.itemView.setOnClickListener { onItemClick(alert) }
    }

    override fun getItemCount(): Int = alerts.size

    class AlertViewHolder(private val binding: ItemAlertCardBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(alert: Alert) {
            binding.alertTitle.text = alert.title
            binding.alertStatus.text = alert.status.displayName.uppercase(Locale.ROOT)

            val sdf = SimpleDateFormat("dd MMM, hh:mm a", Locale.getDefault())
            binding.alertDate.text = sdf.format(alert.date)

            val colorRes = when (alert.level) {
                AlertLevel.CRITICAL -> android.R.color.holo_red_dark
                AlertLevel.HIGH -> android.R.color.holo_orange_dark
                AlertLevel.MEDIUM -> android.R.color.holo_orange_light
                else -> android.R.color.holo_green_light
            }
            binding.levelIndicator.setBackgroundColor(itemView.context.getColor(colorRes))
        }
    }
}