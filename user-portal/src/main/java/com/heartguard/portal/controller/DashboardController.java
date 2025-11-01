package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.PatientSummaryDto;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class DashboardController {

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
        List<PatientSummaryDto> patients = apiClient.getAssignedPatients(session);
        int alertsCount = apiClient.getActiveAlertsCount(session);
        if (patients.size() == 1) {
            return "redirect:/patient/" + patients.get(0).id();
        }
        model.addAttribute("patients", patients);
        model.addAttribute("alertsCount", alertsCount);
        return "dashboard";
    }
}
