package com.heartguard.desktop.models;

import com.google.gson.annotations.SerializedName;

/**
 * DTO simplificado para la respuesta de usuario en login
 */
public class UserLoginData {
    private String id;  // Cambiado a String para manejar UUIDs y evitar NumberFormatException
    private String email;
    private String name;
    
    @SerializedName("system_role")
    private String systemRole;
    
    @SerializedName("org_count")
    private String orgCount;  // Cambiado a String para evitar NumberFormatException en parsing

    // Constructor
    public UserLoginData() {}

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

    public String getSystemRole() {
        return systemRole;
    }

    public void setSystemRole(String systemRole) {
        this.systemRole = systemRole;
    }

    public String getOrgCount() {
        return orgCount;
    }

    public void setOrgCount(String orgCount) {
        this.orgCount = orgCount;
    }
    
    /**
     * Obtiene orgCount como entero, manejando valores no numéricos
     */
    public int getOrgCountAsInt() {
        if (orgCount == null || orgCount.isEmpty()) {
            return 0;
        }
        try {
            return Integer.parseInt(orgCount);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    @Override
    public String toString() {
        return "UserLoginData{" +
                "id=" + id +
                ", email='" + email + '\'' +
                ", name='" + name + '\'' +
                ", systemRole='" + systemRole + '\'' +
                ", orgCount=" + orgCount +
                '}';
    }
}
