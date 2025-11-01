package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.DeviceDto;
import com.heartguard.portal.model.api.PatientSummaryDto;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.Collections;
import java.util.List;
import java.util.Set;

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
        var currentUser = sessionUserManager.getCurrentUser(session);
        if (currentUser == null) {
            return "redirect:/login";
        }
        
        // Obtener los pacientes del usuario
        List<PatientSummaryDto> userPatients = apiClient.getAssignedPatients(session);
        Set<String> patientIds = userPatients.stream()
            .map(PatientSummaryDto::id)
            .collect(java.util.stream.Collectors.toSet());
        
        // Obtener todos los dispositivos y filtrar por los pacientes del usuario
        List<DeviceDto> allDevices = apiClient.getAllDevices(session);
        List<DeviceDto> filteredDevices = allDevices.stream()
            .filter(device -> device.ownerPatientId() != null && patientIds.contains(device.ownerPatientId()))
            .toList();
        
        System.out.println("Usuario: " + currentUser.getName() + " | Pacientes: " + patientIds.size() + " | Dispositivos filtrados: " + filteredDevices.size() + " de " + allDevices.size());
        
        // Agregar información del usuario
        model.addAttribute("userName", currentUser.getName());
        model.addAttribute("userRole", currentUser.getRole());
        model.addAttribute("devices", filteredDevices);
        model.addAttribute("patientCount", userPatients.size());
        
        return "devices";
    }
}
