package com.heartguard.desktop.models.user;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.annotations.SerializedName;

import java.util.ArrayList;
import java.util.List;

/**
 * Representa la membresía de un usuario en una organización.
 */
public class OrgMembership {
    @SerializedName("org_id")
    private String orgId;
    
    @SerializedName("org_code")
    private String orgCode;
    
    @SerializedName("org_name")
    private String orgName;
    
    @SerializedName("role_code")
    private String roleCode;
    
    @SerializedName("role_label")
    private String roleLabel;
    
    @SerializedName("joined_at")
    private String joinedAt;

    public static List<OrgMembership> listFrom(JsonArray array) {
        List<OrgMembership> memberships = new ArrayList<>();
        if (array == null) {
            return memberships;
        }
        for (JsonElement element : array) {
            if (element != null && element.isJsonObject()) {
                memberships.add(fromJson(element.getAsJsonObject()));
            }
        }
        return memberships;
    }

    public static OrgMembership fromJson(JsonObject object) {
        return com.heartguard.desktop.util.JsonUtils.GSON.fromJson(object, OrgMembership.class);
    }

    public String getOrgId() {
        return orgId;
    }

    public void setOrgId(String orgId) {
        this.orgId = orgId;
    }

    public String getOrgCode() {
        return orgCode;
    }

    public void setOrgCode(String orgCode) {
        this.orgCode = orgCode;
    }

    public String getOrgName() {
        return orgName;
    }

    public void setOrgName(String orgName) {
        this.orgName = orgName;
    }

    public String getRoleCode() {
        return roleCode;
    }

    public void setRoleCode(String roleCode) {
        this.roleCode = roleCode;
    }

    public String getRoleLabel() {
        return roleLabel;
    }

    public void setRoleLabel(String roleLabel) {
        this.roleLabel = roleLabel;
    }

    public String getJoinedAt() {
        return joinedAt;
    }

    public void setJoinedAt(String joinedAt) {
        this.joinedAt = joinedAt;
    }

    @Override
    public String toString() {
        if (orgName != null && !orgName.isBlank()) {
            return orgName;
        }
        if (orgCode != null && !orgCode.isBlank()) {
            return orgCode;
        }
        return orgId;
    }
}
