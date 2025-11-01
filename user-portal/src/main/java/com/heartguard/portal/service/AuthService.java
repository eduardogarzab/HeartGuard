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
        LoginResponse response = apiClient.login(new LoginRequest(email, password));
        if (response == null || response.user() == null) {
            throw new IllegalStateException("Respuesta de autenticación inválida");
        }
        AuthenticatedUserSession userSession = new AuthenticatedUserSession();
        userSession.setUserId(response.user().id());
        userSession.setName(response.user().name());
        userSession.setEmail(email);
        userSession.setRole(response.user().role() != null ? response.user().role() : "USER");
        userSession.setAccessToken(response.accessToken());
        userSession.setRefreshToken(response.refreshToken());
        sessionUserManager.storeAuthentication(session, userSession);
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
