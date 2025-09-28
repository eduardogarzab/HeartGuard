package com.example.integracion.data.model

import java.util.Date

// Corresponde a la tabla alert_levels
enum class AlertLevel(val displayName: String) {
    LOW("Bajo"),
    MEDIUM("Medio"),
    HIGH("Alto"),
    CRITICAL("Crítico")
}

// Corresponde a la tabla alert_status
enum class AlertStatus(val displayName: String) {
    CREATED("Nueva"),
    NOTIFIED("Notificada"),
    ACKNOWLEDGED("Revisada"),
    RESOLVED("Resuelta"),
    CLOSED("Cerrada")
}

// Representa un registro de la tabla alerts
data class Alert(
    val id: String,
    val title: String, // Ej. "Arritmia Detectada"
    val description: String,
    val level: AlertLevel,
    val status: AlertStatus,
    val date: Date
)