package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.PatientSummaryDto;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class DashboardController {

    private static final Logger log = LoggerFactory.getLogger(DashboardController.class);

    private final HeartGuardApiClient apiClient;
    private final SessionUserManager sessionUserManager;

    public DashboardController(HeartGuardApiClient apiClient, SessionUserManager sessionUserManager) {
        this.apiClient = apiClient;
        this.sessionUserManager = sessionUserManager;
    }

    @GetMapping({"/", "/dashboard"})
    public String dashboard(HttpSession session, Model model) {
        System.out.println("\n########## DASHBOARD REQUEST ##########");
        
        var currentUser = sessionUserManager.getCurrentUser(session);
        if (currentUser == null) {
            System.out.println("No hay usuario en sesión, redirigiendo a login");
            return "redirect:/login";
        }
        
        System.out.println("Usuario en sesión OK - Role: " + currentUser.getRole());
        
        log.info("Obteniendo pacientes para el dashboard...");
        System.out.println("Llamando apiClient.getAssignedPatients()...");
        
        List<PatientSummaryDto> patients = apiClient.getAssignedPatients(session);
        
        System.out.println("getAssignedPatients() retornó: " + (patients != null ? patients.size() : "null") + " pacientes");
        log.info("Pacientes obtenidos: {}", patients != null ? patients.size() : 0);
        
        int alertsCount = 0;
        try {
            alertsCount = apiClient.getActiveAlertsCount(session);
            log.info("Alertas activas: {}", alertsCount);
        } catch (Exception ex) {
            log.warn("No se pudieron obtener las alertas: {}", ex.getMessage());
        }
        
        if (patients != null && patients.size() == 1) {
            log.info("Solo 1 paciente, redirigiendo a su detalle");
            return "redirect:/patient/" + patients.get(0).id();
        }
        
        // Pasar información del usuario al template
        model.addAttribute("userName", currentUser.getName());
        model.addAttribute("userRole", currentUser.getRole());
        model.addAttribute("patients", patients != null ? patients : List.of());
        model.addAttribute("alertsCount", alertsCount);
        
        // Mensaje informativo según el rol
        String roleMessage = getRoleMessage(currentUser.getRole(), patients != null ? patients.size() : 0);
        model.addAttribute("roleMessage", roleMessage);
        
        System.out.println("########## DASHBOARD REQUEST COMPLETADO ##########\n");
        
        return "dashboard";
    }
    
    private String getRoleMessage(String role, int patientCount) {
        if (role == null) {
            return "Bienvenido al sistema HeartGuard";
        }
        
        String roleLower = role.toLowerCase();
        
        // Portal para usuarios finales: caregivers y pacientes
        if (roleLower.contains("caregiver")) {
            return "Mis pacientes bajo cuidado (" + patientCount + " " + (patientCount == 1 ? "paciente" : "pacientes") + ")";
        } else if (roleLower.contains("patient")) {
            return "Mi información de salud";
        } else {
            // Roles administrativos no deberían usar este portal
            return "Portal de Usuario - " + patientCount + " pacientes";
        }
    }
}
