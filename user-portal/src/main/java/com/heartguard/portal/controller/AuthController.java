package com.heartguard.portal.controller;

import com.heartguard.portal.service.AuthService;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
@RequestMapping
@Validated
public class AuthController {

    private final AuthService authService;
    private final SessionUserManager sessionUserManager;
    private static final Logger log = LoggerFactory.getLogger(AuthController.class);

    public AuthController(AuthService authService, SessionUserManager sessionUserManager) {
        this.authService = authService;
        this.sessionUserManager = sessionUserManager;
    }

    @GetMapping("/login")
    public String loginPage(HttpSession session, Model model, @RequestParam(value = "error", required = false) String error) {
        if (sessionUserManager.getCurrentUser(session) != null) {
            return "redirect:/dashboard";
        }
        if (error != null) {
            model.addAttribute("error", true);
        }
        return "login";
    }

    @PostMapping("/login")
    public String handleLogin(@RequestParam("email") @Email String email,
                              @RequestParam("password") @NotBlank String password,
                              HttpServletRequest request,
                              Model model) {
        try {
            HttpSession session = request.getSession(true);
            authService.login(email, password, session);
            return "redirect:/dashboard";
        } catch (Exception ex) {
            log.warn("Error al autenticar usuario {}: {}", email, ex.getMessage());
            model.addAttribute("error", true);
            model.addAttribute("errorMessage", "Credenciales inválidas o servicio no disponible");
            return "login";
        }
    }

    @PostMapping("/logout")
    public String logout(HttpServletRequest request) {
        HttpSession session = request.getSession(false);
        if (session != null) {
            authService.logout(session);
        }
        return "redirect:/login?logout";
    }
}
