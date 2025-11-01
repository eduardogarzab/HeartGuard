package com.heartguard.portal.advice;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.servlet.ModelAndView;

@ControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(HttpClientErrorException.Unauthorized.class)
    public ModelAndView handleUnauthorized(HttpClientErrorException.Unauthorized ex) {
        log.debug("Unauthorized request: {}", ex.getMessage());
        ModelAndView modelAndView = new ModelAndView("redirect:/login?expired");
        modelAndView.setStatus(HttpStatus.TEMPORARY_REDIRECT);
        return modelAndView;
    }

    @ExceptionHandler(HttpClientErrorException.Forbidden.class)
    public ModelAndView handleForbidden(HttpClientErrorException.Forbidden ex) {
        log.warn("Access denied: {}", ex.getMessage());
        ModelAndView modelAndView = new ModelAndView("error/403");
        modelAndView.setStatus(HttpStatus.FORBIDDEN);
        return modelAndView;
    }

    @ExceptionHandler(Exception.class)
    public ModelAndView handleGeneric(Exception ex) {
        log.error("Unexpected error", ex);
        ModelAndView modelAndView = new ModelAndView("error/generic");
        modelAndView.setStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        modelAndView.addObject("message", ex.getMessage());
        return modelAndView;
    }
}
