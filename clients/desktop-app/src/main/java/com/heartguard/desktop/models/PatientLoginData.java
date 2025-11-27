package com.heartguard.desktop.models;

import com.google.gson.annotations.SerializedName;

/**
 * DTO simplificado para la respuesta de paciente en login
 */
public class PatientLoginData {
    private String id;  // UUID como string
    private String email;
    private String name;
    
    @SerializedName("org_name")
    private String orgName;
    
    @SerializedName("risk_level")
    private String riskLevel;

    // Constructor
    public PatientLoginData() {}

    // Getters y Setters
    public String getId() {
        return id;
    }

    public void setId(String id) {
        this.id = id;
    }

    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public String getOrgName() {
        return orgName;
    }

    public void setOrgName(String orgName) {
        this.orgName = orgName;
    }

    public String getRiskLevel() {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel) {
        this.riskLevel = riskLevel;
    }

    @Override
    public String toString() {
        return "PatientLoginData{" +
                "id=" + id +
                ", email='" + email + '\'' +
                ", name='" + name + '\'' +
                ", orgName='" + orgName + '\'' +
                ", riskLevel='" + riskLevel + '\'' +
                '}';
    }
}
