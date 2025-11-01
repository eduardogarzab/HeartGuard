package com.heartguard.portal.controller;

import com.heartguard.portal.model.api.UserProfileDto;
import com.heartguard.portal.service.HeartGuardApiClient;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class ProfileController {

    private final HeartGuardApiClient apiClient;
    private final SessionUserManager sessionUserManager;

    public ProfileController(HeartGuardApiClient apiClient, SessionUserManager sessionUserManager) {
        this.apiClient = apiClient;
        this.sessionUserManager = sessionUserManager;
    }

    @GetMapping("/profile")
    public String profile(HttpSession session, Model model) {
        if (sessionUserManager.getCurrentUser(session) == null) {
            return "redirect:/login";
        }
        UserProfileDto profile = apiClient.getCurrentUser(session);
        model.addAttribute("profile", profile);
        return "profile";
    }
}
