package com.example.proyecto.ui.history

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.example.proyecto.R
import com.example.proyecto.data.model.Vital

// Elimina (private val items: List<Vital>) del constructor
class VitalAdapter : ListAdapter<Vital, VitalAdapter.ViewHolder>(DiffCallback) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.row_vital, parent, false)
        return ViewHolder(view)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val vital = getItem(position)
        holder.bind(vital)
    }

    class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        private val tvVitalData: TextView = itemView.findViewById(R.id.tvVitalData)
        private val tvTimestamp: TextView = itemView.findViewById(R.id.tvTimestamp)

        fun bind(vital: Vital) {
            tvVitalData.text = "HR ${vital.hr} bpm • SpO2 ${vital.spo2}% • PA ${vital.sbp}/${vital.dbp} mmHg • T ${vital.temp_c}°C"
            tvTimestamp.text = vital.measured_at
        }
    }

    companion object DiffCallback : DiffUtil.ItemCallback<Vital>() {
        override fun areItemsTheSame(oldItem: Vital, newItem: Vital): Boolean {
            return oldItem.measured_at == newItem.measured_at
        }

        override fun areContentsTheSame(oldItem: Vital, newItem: Vital): Boolean {
            return oldItem == newItem
        }
    }
}