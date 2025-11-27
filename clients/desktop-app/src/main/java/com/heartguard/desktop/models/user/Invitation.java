package com.heartguard.desktop.models.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.List;

/**
 * Modelo para invitaciones pendientes de organización.
 */
public class Invitation {
    private String id;
    private String email;
    private String status;
    
    private Organization organization;
    private Role role;
    
    @SerializedName("invited_by")
    private InvitedBy invitedBy;
    
    @SerializedName("expires_at")
    private String expiresAt;
    
    @SerializedName("created_at")
    private String createdAt;

    public static class Organization {
        private String id;
        private String code;
        private String name;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getCode() {
            return code;
        }

        public void setCode(String code) {
            this.code = code;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }
    }

    public static class Role {
        private String code;
        private String label;

        public String getCode() {
            return code;
        }

        public void setCode(String code) {
            this.code = code;
        }

        public String getLabel() {
            return label;
        }

        public void setLabel(String label) {
            this.label = label;
        }
    }
    
    public static class InvitedBy {
        private String id;
        private String name;
        private String email;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }

        public String getEmail() {
            return email;
        }

        public void setEmail(String email) {
            this.email = email;
        }
    }

    public static List<Invitation> listFrom(JsonArray array) {
        List<Invitation> invitations = new ArrayList<>();
        if (array == null) {
            return invitations;
        }
        for (JsonElement element : array) {
            if (element != null && element.isJsonObject()) {
                invitations.add(fromJson(element.getAsJsonObject()));
            }
        }
        return invitations;
    }

    public static Invitation fromJson(JsonObject object) {
        return com.heartguard.desktop.util.JsonUtils.GSON.fromJson(object, Invitation.class);
    }

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

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public Organization getOrganization() {
        return organization;
    }

    public void setOrganization(Organization organization) {
        this.organization = organization;
    }

    public Role getRole() {
        return role;
    }

    public void setRole(Role role) {
        this.role = role;
    }

    public InvitedBy getInvitedBy() {
        return invitedBy;
    }

    public void setInvitedBy(InvitedBy invitedBy) {
        this.invitedBy = invitedBy;
    }

    public String getExpiresAt() {
        return expiresAt;
    }

    public void setExpiresAt(String expiresAt) {
        this.expiresAt = expiresAt;
    }

    public String getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(String createdAt) {
        this.createdAt = createdAt;
    }

    // Métodos de compatibilidad para InvitationsDialog
    public String getOrganizationName() {
        return organization != null ? organization.getName() : null;
    }

    public String getOrganizationCode() {
        return organization != null ? organization.getCode() : null;
    }

    public String getRoleLabel() {
        return role != null ? role.getLabel() : null;
    }

    public String getSentAt() {
        return createdAt;
    }

    public String getOrganizationLabel() {
        if (organization != null) {
            if (organization.getName() != null && !organization.getName().isBlank()) {
                return organization.getName();
            }
            if (organization.getCode() != null && !organization.getCode().isBlank()) {
                return organization.getCode();
            }
        }
        return "Organización";
    }
}
