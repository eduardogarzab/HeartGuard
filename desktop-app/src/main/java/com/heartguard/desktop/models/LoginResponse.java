package com.heartguard.desktop.models;

import com.google.gson.annotations.SerializedName;

/**
 * Modelo que representa la respuesta de login/registro del sistema
 */
public class LoginResponse {
    @SerializedName("access_token")
    private String accessToken;
    
    @SerializedName("refresh_token")
    private String refreshToken;
    
    @SerializedName("token_type")
    private String tokenType;
    
    @SerializedName("expires_in")
    private Integer expiresIn;
    
    private UserLoginData user;
    private PatientLoginData patient;
    
    @SerializedName("account_type")
    private String accountType; // "user" o "patient"

    // Constructores
    public LoginResponse() {
        this.tokenType = "Bearer";
    }

    // Getters y Setters
    public String getAccessToken() {
        return accessToken;
    }

    public void setAccessToken(String accessToken) {
        this.accessToken = accessToken;
    }

    public String getRefreshToken() {
        return refreshToken;
    }

    public void setRefreshToken(String refreshToken) {
        this.refreshToken = refreshToken;
    }

    public String getTokenType() {
        return tokenType;
    }

    public void setTokenType(String tokenType) {
        this.tokenType = tokenType;
    }

    public Integer getExpiresIn() {
        return expiresIn;
    }

    public void setExpiresIn(Integer expiresIn) {
        this.expiresIn = expiresIn;
    }

    public UserLoginData getUser() {
        return user;
    }

    public void setUser(UserLoginData user) {
        this.user = user;
        if (user != null) {
            this.accountType = "user";
        }
    }

    public PatientLoginData getPatient() {
        return patient;
    }

    public void setPatient(PatientLoginData patient) {
        this.patient = patient;
        if (patient != null) {
            this.accountType = "patient";
        }
    }

    public String getAccountType() {
        return accountType;
    }

    public void setAccountType(String accountType) {
        this.accountType = accountType;
    }

    /**
     * Obtiene el nombre completo del usuario o paciente
     */
    public String getFullName() {
        if (user != null) {
            return user.getName();
        } else if (patient != null) {
            return patient.getName();
        }
        return "Unknown";
    }

    /**
     * Obtiene el email del usuario o paciente
     */
    public String getEmail() {
        if (user != null) {
            return user.getEmail();
        } else if (patient != null) {
            return patient.getEmail();
        }
        return null;
    }

    /**
     * Obtiene el ID del paciente (solo para account_type = "patient")
     */
    public String getPatientId() {
        if (patient != null && patient.getId() != null) {
            return patient.getId();
        }
        return null;
    }

    @Override
    public String toString() {
        return "LoginResponse{" +
                "accountType='" + accountType + '\'' +
                ", email='" + getEmail() + '\'' +
                ", fullName='" + getFullName() + '\'' +
                ", hasAccessToken=" + (accessToken != null) +
                '}';
    }
}
