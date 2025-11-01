package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.AlertDto;
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
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        
        try {
            List<AlertDto> alerts = apiClient.getAllAlerts(session);
            model.addAttribute("alerts", alerts);
        } catch (Exception ex) {
            model.addAttribute("alerts", Collections.emptyList());
            model.addAttribute("error", "No se pudieron cargar las alertas: " + ex.getMessage());
        }
        
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
