package com.heartguard.desktop.models;

import com.google.gson.annotations.SerializedName;

/**
 * DTO simplificado para la respuesta de usuario en login
 */
public class UserLoginData {
    private Long id;
    private String email;
    private String name;
    
    @SerializedName("system_role")
    private String systemRole;
    
    @SerializedName("org_count")
    private Integer orgCount;

    // Constructor
    public UserLoginData() {}

    // Getters y Setters
    public Long getId() {
        return id;
    }

    public void setId(Long id) {
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

    public Integer getOrgCount() {
        return orgCount;
    }

    public void setOrgCount(Integer orgCount) {
        this.orgCount = orgCount;
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
