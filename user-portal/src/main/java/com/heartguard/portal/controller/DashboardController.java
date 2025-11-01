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
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        
        try {
            log.info("Obteniendo pacientes para el dashboard...");
            List<PatientSummaryDto> patients = apiClient.getAssignedPatients(session);
            log.info("Pacientes obtenidos: {}", patients != null ? patients.size() : 0);
            
            int alertsCount = apiClient.getActiveAlertsCount(session);
            log.info("Alertas activas: {}", alertsCount);
            
            if (patients != null && patients.size() == 1) {
                log.info("Solo 1 paciente, redirigiendo a su detalle");
                return "redirect:/patient/" + patients.get(0).id();
            }
            
            model.addAttribute("patients", patients != null ? patients : List.of());
            model.addAttribute("alertsCount", alertsCount);
        } catch (Exception ex) {
            // Si hay error al obtener datos del gateway, mostrar dashboard vacío
            log.error("Error al cargar datos del dashboard", ex);
            model.addAttribute("patients", List.of());
            model.addAttribute("alertsCount", 0);
            model.addAttribute("error", "No se pudieron cargar los datos: " + ex.getMessage());
        }
        
        return "dashboard";
    }
}
