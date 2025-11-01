package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.AlertDto;
import com.heartguard.portal.model.api.PatientSummaryDto;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;

import java.util.Collections;
import java.util.List;
import java.util.Set;

@Controller
public class AlertsController {

    private final HeartGuardApiClient apiClient;
    private final SessionUserManager sessionUserManager;

    public AlertsController(HeartGuardApiClient apiClient, SessionUserManager sessionUserManager) {
        this.apiClient = apiClient;
        this.sessionUserManager = sessionUserManager;
    }

    @GetMapping("/alerts")
    public String listAlerts(HttpSession session, Model model) {
        var currentUser = sessionUserManager.getCurrentUser(session);
        if (currentUser == null) {
            return "redirect:/login";
        }
        
        // Obtener los pacientes del usuario (para caregivers) o el propio usuario (para pacientes)
        List<PatientSummaryDto> userPatients = apiClient.getAssignedPatients(session);
        Set<String> patientIds = userPatients.stream()
            .map(PatientSummaryDto::id)
            .collect(java.util.stream.Collectors.toSet());
        
        // Obtener todas las alertas y filtrar por los pacientes del usuario
        List<AlertDto> allAlerts = apiClient.getAllAlerts(session);
        List<AlertDto> filteredAlerts = allAlerts.stream()
            .filter(alert -> alert.patientId() != null && patientIds.contains(alert.patientId()))
            .toList();
        
        System.out.println("Usuario: " + currentUser.getName() + " | Pacientes: " + patientIds.size() + " | Alertas filtradas: " + filteredAlerts.size() + " de " + allAlerts.size());
        
        // Agregar información del usuario
        model.addAttribute("userName", currentUser.getName());
        model.addAttribute("userRole", currentUser.getRole());
        model.addAttribute("alerts", filteredAlerts);
        model.addAttribute("patientCount", userPatients.size());
        
        return "alerts";
    }

    @PostMapping("/alerts/{alertId}/ack")
    public String acknowledgeAlert(@PathVariable String alertId, HttpSession session) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        
        try {
            apiClient.acknowledgeAlert(session, alertId, null);
        } catch (Exception ex) {
            // Manejar error silenciosamente
        }
        
        return "redirect:/alerts";
    }
}
