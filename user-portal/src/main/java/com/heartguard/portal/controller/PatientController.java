package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.AlertAckRequest;
import com.heartguard.portal.model.api.AlertDto;
import com.heartguard.portal.model.api.PatientDetailDto;
import com.heartguard.portal.model.api.StreamResponse;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.constraints.NotBlank;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

import java.util.List;

@Controller
@Validated
public class PatientController {

    private final HeartGuardApiClient apiClient;
    private final SessionUserManager sessionUserManager;

    public PatientController(HeartGuardApiClient apiClient, SessionUserManager sessionUserManager) {
        this.apiClient = apiClient;
        this.sessionUserManager = sessionUserManager;
    }

    @GetMapping("/patient/{patientId}")
    public String patientDashboard(@PathVariable String patientId, HttpSession session, Model model) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        PatientDetailDto patient = apiClient.getPatientDetails(session, patientId);
        List<AlertDto> alerts = apiClient.getActiveAlertsForPatient(session, patientId);
        model.addAttribute("patient", patient);
        model.addAttribute("alerts", alerts);
        model.addAttribute("selectedSignal", "ecg");
        return "patient";
    }

    @GetMapping("/patient/{patientId}/alerts")
    public String patientAlerts(@PathVariable String patientId, HttpSession session, Model model) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        PatientDetailDto patient = apiClient.getPatientDetails(session, patientId);
        List<AlertDto> alerts = apiClient.getAlertsForPatient(session, patientId);
        model.addAttribute("patient", patient);
        model.addAttribute("alerts", alerts);
        return "patient-alerts";
    }

    @PostMapping("/patient/{patientId}/alerts/{alertId}/ack")
    public String acknowledgeAlert(@PathVariable String patientId,
                                   @PathVariable String alertId,
                                   @RequestParam(value = "note", required = false) String note,
                                   HttpSession session) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        apiClient.acknowledgeAlert(session, alertId, new AlertAckRequest(note));
        return "redirect:/patient/" + patientId;
    }

    @GetMapping("/patient/{patientId}/stream")
    @ResponseBody
    public ResponseEntity<StreamResponse> loadStream(@PathVariable String patientId,
                                                     @RequestParam("signal") @NotBlank String signal,
                                                     @RequestParam(value = "duration", defaultValue = "5m") String duration,
                                                     HttpSession session) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return ResponseEntity.status(401).build();
        }
        StreamResponse response = apiClient.getStream(session, patientId, signal, duration);
        return ResponseEntity.ok(response);
    }
}
