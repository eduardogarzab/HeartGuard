package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.DeviceDto;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.Collections;
import java.util.List;

@Controller
public class DevicesController {

    private final HeartGuardApiClient apiClient;
    private final SessionUserManager sessionUserManager;

    public DevicesController(HeartGuardApiClient apiClient, SessionUserManager sessionUserManager) {
        this.apiClient = apiClient;
        this.sessionUserManager = sessionUserManager;
    }

    @GetMapping("/devices")
    public String listDevices(HttpSession session, Model model) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        
        try {
            List<DeviceDto> devices = apiClient.getAllDevices(session);
            model.addAttribute("devices", devices);
        } catch (Exception ex) {
            model.addAttribute("devices", Collections.emptyList());
            model.addAttribute("error", "No se pudieron cargar los dispositivos: " + ex.getMessage());
        }
        
        return "devices";
    }
}
