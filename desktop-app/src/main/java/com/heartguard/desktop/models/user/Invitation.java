package com.heartguard.desktop.models.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.util.ArrayList;
import java.util.List;

/**
 * Modelo para invitaciones pendientes de organización.
 */
public class Invitation {
    private String id;
    private String organizationName;
    private String organizationCode;
    private String roleLabel;
    private String sentAt;
    private String expiresAt;

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

    public String getOrganizationName() {
        return organizationName;
    }

    public void setOrganizationName(String organizationName) {
        this.organizationName = organizationName;
    }

    public String getOrganizationCode() {
        return organizationCode;
    }

    public void setOrganizationCode(String organizationCode) {
        this.organizationCode = organizationCode;
    }

    public String getRoleLabel() {
        return roleLabel;
    }

    public void setRoleLabel(String roleLabel) {
        this.roleLabel = roleLabel;
    }

    public String getSentAt() {
        return sentAt;
    }

    public void setSentAt(String sentAt) {
        this.sentAt = sentAt;
    }

    public String getExpiresAt() {
        return expiresAt;
    }

    public void setExpiresAt(String expiresAt) {
        this.expiresAt = expiresAt;
    }

    public String getOrganizationLabel() {
        if (organizationName != null && !organizationName.isBlank()) {
            return organizationName;
        }
        if (organizationCode != null && !organizationCode.isBlank()) {
            return organizationCode;
        }
        return "Organización";
    }
}
