package com.heartguard.portal.service;

import com.heartguard.portal.model.api.LoginRequest;
import com.heartguard.portal.model.api.LoginResponse;
import com.heartguard.portal.session.AuthenticatedUserSession;
import com.heartguard.portal.session.SessionUserManager;
import jakarta.servlet.http.HttpSession;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;
import org.springframework.web.client.HttpClientErrorException;

@Service
public class AuthService {

    private final HeartGuardApiClient apiClient;
    private final SessionUserManager sessionUserManager;

    public AuthService(HeartGuardApiClient apiClient, SessionUserManager sessionUserManager) {
        this.apiClient = apiClient;
        this.sessionUserManager = sessionUserManager;
    }

    public void login(String email, String password, HttpSession session) {
        System.out.println("\n========== LOGIN PROCESS START ==========");
        System.out.println("Email: " + email);
        
        LoginResponse response = apiClient.login(new LoginRequest(email, password));
        if (response == null || response.user() == null) {
            throw new IllegalStateException("Respuesta de autenticación inválida");
        }
        
        System.out.println("Login response received from gateway:");
        System.out.println("  User ID: " + response.user().id());
        System.out.println("  User Name: " + response.user().name());
        System.out.println("  User Role: " + response.user().role());
        System.out.println("  Access Token (primeros 80): " + response.accessToken().substring(0, Math.min(80, response.accessToken().length())));
        System.out.println("  Access Token Length: " + response.accessToken().length());
        
        AuthenticatedUserSession userSession = new AuthenticatedUserSession();
        userSession.setUserId(response.user().id());
        userSession.setName(response.user().name());
        userSession.setEmail(email);
        userSession.setRole(response.user().role() != null ? response.user().role() : "USER");
        userSession.setAccessToken(response.accessToken());
        userSession.setRefreshToken(response.refreshToken());
        
        System.out.println("\nGuardando en sesión...");
        sessionUserManager.storeAuthentication(session, userSession);
        
        System.out.println("Verificando que se guardó correctamente...");
        AuthenticatedUserSession verificacion = sessionUserManager.getCurrentUser(session);
        if (verificacion != null && verificacion.getAccessToken() != null) {
            System.out.println("  ✓ Token guardado OK - Length: " + verificacion.getAccessToken().length());
            System.out.println("  ✓ Token guardado (primeros 80): " + verificacion.getAccessToken().substring(0, Math.min(80, verificacion.getAccessToken().length())));
        } else {
            System.out.println("  ✗ ERROR: Token NO se guardó correctamente!");
        }
        System.out.println("========== LOGIN PROCESS END ==========\n");
    }

    public void logout(HttpSession session) {
        AuthenticatedUserSession userSession = sessionUserManager.getCurrentUser(session);
        if (userSession != null && StringUtils.hasText(userSession.getAccessToken())) {
            try {
                apiClient.logout(userSession.getAccessToken());
            } catch (HttpClientErrorException ex) {
                // ignore errors on logout to avoid blocking the user from signing out
            }
        }
        sessionUserManager.clear(session);
        SecurityContextHolder.clearContext();
    }
}
