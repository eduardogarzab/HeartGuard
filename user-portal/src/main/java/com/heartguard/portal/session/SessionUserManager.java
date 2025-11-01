package com.heartguard.portal.session;

import jakarta.servlet.http.HttpSession;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.stereotype.Component;

@Component
public class SessionUserManager {

    public static final String USER_SESSION_ATTRIBUTE = "AUTHENTICATED_USER";

    public void storeAuthentication(HttpSession session, AuthenticatedUserSession userSession) {
        UserDetails userDetails = User.withUsername(userSession.getEmail())
                .password("")
                .authorities(userSession.getRole())
                .build();
        Authentication authentication = new UsernamePasswordAuthenticationToken(userDetails, null, userDetails.getAuthorities());
        SecurityContext securityContext = SecurityContextHolder.createEmptyContext();
        securityContext.setAuthentication(authentication);
        SecurityContextHolder.setContext(securityContext);
        session.setAttribute(HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY, securityContext);
        session.setAttribute(USER_SESSION_ATTRIBUTE, userSession);
    }

    public AuthenticatedUserSession getCurrentUser(HttpSession session) {
        if (session == null) {
            return null;
        }
        Object attribute = session.getAttribute(USER_SESSION_ATTRIBUTE);
        if (attribute instanceof AuthenticatedUserSession userSession) {
            return userSession;
        }
        return null;
    }

    public void updateAccessToken(HttpSession session, String newAccessToken) {
        AuthenticatedUserSession userSession = getCurrentUser(session);
        if (userSession != null) {
            userSession.setAccessToken(newAccessToken);
            session.setAttribute(USER_SESSION_ATTRIBUTE, userSession);
        }
    }

    public void clear(HttpSession session) {
        if (session != null) {
            session.invalidate();
        }
    }
}
