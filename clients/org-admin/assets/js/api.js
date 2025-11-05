const Api = (() => {
    const cfg = window.ORG_ADMIN_CONFIG;
    const baseUrl = cfg.gatewayBaseUrl.replace(/\/$/, "");

    const withTimeout = (promise, ms = cfg.requestTimeoutMs) => {
        let timer;
        return Promise.race([
            promise,
            new Promise((_, reject) => {
                timer = window.setTimeout(() => reject(new Error("La solicitud excedió el tiempo máximo")), ms);
            }),
        ]).finally(() => window.clearTimeout(timer));
    };

    const buildUrl = (path) => {
        if (!path.startsWith("/")) {
            path = `/${path}`;
        }
        return `${baseUrl}${path}`;
    };

    const handleJsonError = async (response) => {
        let message = `Error ${response.status}`;
        try {
            const payload = await response.json();
            if (payload?.message) {
                message = payload.message;
            }
        } catch (err) {
            // ignore
        }
        const error = new Error(message);
        error.status = response.status;
        throw error;
    };

    const handleXmlError = async (response) => {
        const text = await response.text();
        try {
            const doc = Xml.parse(text);
            const code = Xml.text(doc, "response > error > code", `error_${response.status}`);
            const message = Xml.text(doc, "response > error > message", `Error ${response.status}`);
            const err = new Error(message);
            err.status = response.status;
            err.code = code;
            throw err;
        } catch (err) {
            if (err instanceof Error && err.message === "No se pudo interpretar la respuesta XML") {
                const fallback = new Error(`Error ${response.status}`);
                fallback.status = response.status;
                throw fallback;
            }
            throw err;
        }
    };

    const requestJson = async (path, { method = "GET", body, token } = {}) => {
        const headers = new Headers({ "Content-Type": "application/json" });
        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }
        const response = await withTimeout(
            fetch(buildUrl(path), {
                method,
                headers,
                body: body ? JSON.stringify(body) : undefined,
            })
        );
        if (!response.ok) {
            await handleJsonError(response);
        }
        return response.json();
    };

    const requestXml = async (path, { method = "GET", body, token, headers: extraHeaders } = {}) => {
        const headers = new Headers(Object.assign({ Accept: "application/xml" }, extraHeaders || {}));
        if (token) {
            headers.set("Authorization", `Bearer ${token}`);
        }
        if (body && !(body instanceof FormData)) {
            headers.set("Content-Type", headers.get("Content-Type") || "application/json");
        }
        const response = await withTimeout(
            fetch(buildUrl(path), {
                method,
                headers,
                body: body ? (body instanceof FormData ? body : JSON.stringify(body)) : undefined,
            })
        );
        const text = await response.text();
        if (!response.ok) {
            const synthetic = new Response(text, {
                status: response.status,
                statusText: response.statusText,
                headers: { "Content-Type": response.headers.get("Content-Type") || "application/xml" },
            });
            await handleXmlError(synthetic);
        }
        return Xml.parse(text);
    };

    const transform = {
        organization(node) {
            return {
                id: Xml.text(node, "id"),
                code: Xml.text(node, "code"),
                name: Xml.text(node, "name"),
                joinedAt: Xml.text(node, "joined_at"),
                createdAt: Xml.text(node, "created_at"),
                roleCode: Xml.text(node, "role_code"),
                roleLabel: Xml.text(node, "role_label"),
            };
        },
        staffMember(node) {
            return {
                userId: Xml.text(node, "user_id"),
                name: Xml.text(node, "name"),
                email: Xml.text(node, "email"),
                roleCode: Xml.text(node, "role_code"),
                roleLabel: Xml.text(node, "role_label"),
                joinedAt: Xml.text(node, "joined_at"),
            };
        },
        invitation(node) {
            return {
                id: Xml.text(node, "id"),
                email: Xml.text(node, "email"),
                roleCode: Xml.text(node, "role_code"),
                roleLabel: Xml.text(node, "role_label"),
                token: Xml.text(node, "token"),
                expiresAt: Xml.text(node, "expires_at"),
                usedAt: Xml.text(node, "used_at"),
                revokedAt: Xml.text(node, "revoked_at"),
                createdAt: Xml.text(node, "created_at"),
                status: Xml.text(node, "status"),
            };
        },
        patient(node) {
            return {
                id: Xml.text(node, "id"),
                name: Xml.text(node, "person_name"),
                email: Xml.text(node, "email"),
                birthdate: Xml.text(node, "birthdate"),
                riskLevelCode: Xml.text(node, "risk_level_code"),
                riskLevelLabel: Xml.text(node, "risk_level_label"),
                createdAt: Xml.text(node, "created_at"),
            };
        },
        careTeam(node) {
            return {
                id: Xml.text(node, "id"),
                name: Xml.text(node, "name"),
                createdAt: Xml.text(node, "created_at"),
            };
        },
        careTeamMember(node) {
            return {
                careTeamId: Xml.text(node, "care_team_id"),
                userId: Xml.text(node, "user_id"),
                name: Xml.text(node, "name"),
                email: Xml.text(node, "email"),
                roleId: Xml.text(node, "role_id"),
                roleCode: Xml.text(node, "role_code"),
                roleLabel: Xml.text(node, "role_label"),
                joinedAt: Xml.text(node, "joined_at"),
            };
        },
        careTeamPatient(node) {
            return {
                careTeamId: Xml.text(node, "care_team_id"),
                patientId: Xml.text(node, "patient_id"),
                name: Xml.text(node, "person_name"),
                email: Xml.text(node, "email"),
            };
        },
        careTeamRole(node) {
            return {
                id: Xml.text(node, "id"),
                code: Xml.text(node, "code"),
                label: Xml.text(node, "label"),
            };
        },
        caregiverAssignment(node) {
            return {
                patientId: Xml.text(node, "patient_id"),
                patientName: Xml.text(node, "patient_name"),
                patientEmail: Xml.text(node, "patient_email"),
                caregiverId: Xml.text(node, "caregiver_id"),
                caregiverName: Xml.text(node, "caregiver_name"),
                caregiverEmail: Xml.text(node, "caregiver_email"),
                relationshipTypeId: Xml.text(node, "rel_type_id"),
                relationshipCode: Xml.text(node, "relationship_code"),
                relationshipLabel: Xml.text(node, "relationship_label"),
                isPrimary: Xml.bool(node, "is_primary"),
                startedAt: Xml.text(node, "started_at"),
                endedAt: Xml.text(node, "ended_at"),
                note: Xml.text(node, "note"),
                careTeamId: Xml.text(node, "care_team_id"),
                careTeamName: Xml.text(node, "care_team_name"),
            };
        },
        alert(node) {
            return {
                id: Xml.text(node, "id"),
                createdAt: Xml.text(node, "created_at"),
                description: Xml.text(node, "description"),
                patientId: Xml.text(node, "patient_id"),
                patientName: Xml.text(node, "patient_name"),
                typeCode: Xml.text(node, "type_code"),
                typeDescription: Xml.text(node, "type_description"),
                levelCode: Xml.text(node, "level_code"),
                levelLabel: Xml.text(node, "level_label"),
                statusCode: Xml.text(node, "status_code"),
                statusDescription: Xml.text(node, "status_description"),
                locationWkt: Xml.text(node, "location_wkt"),
            };
        },
        device(node) {
            return {
                id: Xml.text(node, "id"),
                orgId: Xml.text(node, "org_id"),
                orgName: Xml.text(node, "org_name"),
                serial: Xml.text(node, "serial"),
                brand: Xml.text(node, "brand"),
                model: Xml.text(node, "model"),
                deviceTypeCode: Xml.text(node, "device_type_code"),
                deviceTypeLabel: Xml.text(node, "device_type_label"),
                ownerPatientId: Xml.text(node, "owner_patient_id"),
                ownerPatientName: Xml.text(node, "owner_patient_name"),
                registeredAt: Xml.text(node, "registered_at"),
                active: Xml.bool(node, "active"),
            };
        },
        pushDevice(node) {
            return {
                id: Xml.text(node, "id"),
                userId: Xml.text(node, "user_id"),
                userName: Xml.text(node, "user_name"),
                userEmail: Xml.text(node, "user_email"),
                platformId: Xml.text(node, "platform_id"),
                platformCode: Xml.text(node, "platform_code"),
                platformLabel: Xml.text(node, "platform_label"),
                pushToken: Xml.text(node, "push_token"),
                lastSeenAt: Xml.text(node, "last_seen_at"),
                active: Xml.bool(node, "active"),
            };
        },
        groundTruthLabel(node) {
            return {
                id: Xml.text(node, "id"),
                patientId: Xml.text(node, "patient_id"),
                eventTypeId: Xml.text(node, "event_type_id"),
                eventTypeCode: Xml.text(node, "event_type_code"),
                eventTypeLabel: Xml.text(node, "event_type_label"),
                onset: Xml.text(node, "onset"),
                offsetAt: Xml.text(node, "offset_at"),
                annotatedByUserId: Xml.text(node, "annotated_by_user_id"),
                annotatedByName: Xml.text(node, "annotated_by_name"),
                source: Xml.text(node, "source"),
                note: Xml.text(node, "note"),
            };
        },
        patientLocation(node) {
            return {
                id: Xml.text(node, "id"),
                patientId: Xml.text(node, "patient_id"),
                latitude: Xml.float(node, "latitude"),
                longitude: Xml.float(node, "longitude"),
                source: Xml.text(node, "source"),
                accuracyMeters: Xml.float(node, "accuracy_m"),
                timestamp: Xml.text(node, "ts"),
            };
        },
    };

    return {
        auth: {
            async login(email, password) {
                return requestJson(cfg.authLoginPath, {
                    method: "POST",
                    body: { email: email.trim(), password },
                });
            },
            async me(token) {
                return requestJson(cfg.authMePath, { token });
            },
        },

        admin: {
            async listOrganizations(token) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/`, { token });
                const organizations = Xml.mapNodes(doc, "response > organizations > organization", transform.organization);
                return organizations;
            },
            async organizationSummary(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}`, { token });
                const infoNode = doc.querySelector("response > organization");
                const statsNode = doc.querySelector("response > stats");
                if (!infoNode || !statsNode) {
                    throw new Error("Respuesta inesperada del servicio de administracion");
                }
                return {
                    organization: transform.organization(infoNode),
                    stats: {
                        memberCount: Xml.integer(statsNode, "member_count"),
                        patientCount: Xml.integer(statsNode, "patient_count"),
                        careTeamCount: Xml.integer(statsNode, "care_team_count"),
                        caregiverCount: Xml.integer(statsNode, "caregiver_count"),
                        alertCount: Xml.integer(statsNode, "alert_count"),
                    },
                };
            },
            async dashboard(token, orgId, periodDays) {
                const params = periodDays ? `?period_days=${encodeURIComponent(periodDays)}` : "";
                const url = `${cfg.adminBasePath}/organizations/${orgId}/dashboard/${params}`;
                const doc = await requestXml(url, { token });
                const statsNode = doc.querySelector("dashboard > stats");
                if (!statsNode) {
                    throw new Error("El dashboard no devolvio estadisticas");
                }
                const result = {
                    periodDays: Xml.integer(doc, "dashboard > period_days", 30),
                    stats: {
                        memberCount: Xml.integer(statsNode, "member_count"),
                        patientCount: Xml.integer(statsNode, "patient_count"),
                        careTeamCount: Xml.integer(statsNode, "care_team_count"),
                        caregiverCount: Xml.integer(statsNode, "caregiver_count"),
                        alertCount: Xml.integer(statsNode, "alert_count"),
                    },
                    riskLevels: Xml.mapNodes(doc, "dashboard > risk_levels > risk_level", (node) => ({
                        code: Xml.text(node, "code"),
                        label: Xml.text(node, "label"),
                        count: Xml.integer(node, "count"),
                    })),
                    deviceStatus: Xml.mapNodes(doc, "dashboard > device_status > status", (node) => ({
                        code: Xml.text(node, "code"),
                        label: Xml.text(node, "label"),
                        count: Xml.integer(node, "count"),
                    })),
                    alertOutcomes: Xml.mapNodes(doc, "dashboard > alert_outcomes > alert_outcome", (node) => ({
                        code: Xml.text(node, "code"),
                        label: Xml.text(node, "label"),
                        count: Xml.integer(node, "count"),
                    })),
                    responseStats: {
                        avgAckSeconds: Xml.float(doc, "dashboard > response_stats > avg_ack_seconds"),
                        avgResolveSeconds: Xml.float(doc, "dashboard > response_stats > avg_resolve_seconds"),
                    },
                    alertsCreated: Xml.integer(doc, "dashboard > alerts_created"),
                    invitationStatus: Xml.mapNodes(doc, "dashboard > invitation_status > status", (node) => ({
                        code: Xml.text(node, "code"),
                        label: Xml.text(node, "label"),
                        count: Xml.integer(node, "count"),
                    })),
                };
                return result;
            },
            async listStaff(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/`, { token });
                return Xml.mapNodes(doc, "response > staff_members > staff_member", transform.staffMember);
            },
            async listInvitations(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/invitations`, { token });
                return Xml.mapNodes(doc, "response > invitations > invitation", transform.invitation);
            },
            async listRoles(token) {
                // Only org_admin and org_viewer roles are allowed for org staff
                return [
                    { code: 'org_admin', label: 'Admin de Organización' },
                    { code: 'org_viewer', label: 'Observador de Organización' }
                ];
            },
            async listPatients(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/`, { token });
                return Xml.mapNodes(doc, "response > patients > patient", transform.patient);
            },
            async getPatient(token, orgId, patientId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}`, { token });
                const node = doc.querySelector("response > patient");
                return node ? transform.patient(node) : null;
            },
            async getPatientProfile(token, orgId, patientId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/profile`, { token });
                const root = doc.querySelector("response > patient_profile");
                if (!root) {
                    return null;
                }
                const patientNode = root.querySelector("patient");
                const latestNode = root.querySelector("locations > latest");
                let latestLocation = null;
                if (latestNode && latestNode.children.length) {
                    latestLocation = transform.patientLocation(latestNode);
                }

                return {
                    patient: patientNode ? transform.patient(patientNode) : null,
                    caregivers: Xml.mapNodes(root, "caregivers > caregiver", transform.caregiverAssignment),
                    careTeams: Xml.mapNodes(root, "care_teams > care_team", (node) => {
                        const team = transform.careTeam(node);
                        team.orgId = Xml.text(node, "org_id");
                        team.members = Xml.mapNodes(node, "members > member", transform.careTeamMember);
                        return team;
                    }),
                    devices: Xml.mapNodes(root, "devices > device", transform.device),
                    groundTruthLabels: Xml.mapNodes(root, "ground_truth_labels > ground_truth_label", transform.groundTruthLabel),
                    alerts: Xml.mapNodes(root, "alerts > alert", transform.alert),
                    locations: {
                        latest: latestLocation,
                        recent: Xml.mapNodes(root, "locations > recent > item", transform.patientLocation),
                    },
                };
            },
            async listCareTeams(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/`, { token });
                return Xml.mapNodes(doc, "response > care_teams > care_team", transform.careTeam);
            },
            async listCaregiverAssignments(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/caregivers/assignments`, { token });
                return Xml.mapNodes(doc, "response > assignments > assignment", transform.caregiverAssignment);
            },
            async listAlerts(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/`, { token });
                return Xml.mapNodes(doc, "response > alerts > alert", transform.alert);
            },
            async createStaffInvitation(token, orgId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/invitations`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > invitation");
                return transform.invitation(node);
            },
            async revokeInvitation(token, orgId, invitationId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/invitations/${invitationId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            async updateStaffRole(token, orgId, userId, payload) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/${userId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                return true;
            },
            async getStaffProfile(token, orgId, userId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/${userId}/profile`, { token });
                const root = doc.querySelector("response > staff_profile");
                if (!root) {
                    return null;
                }
                const memberNode = root.querySelector("member");
                const member = memberNode
                    ? {
                        ...transform.staffMember(memberNode),
                        profilePhotoUrl: Xml.text(memberNode, "profile_photo_url"),
                        createdAt: Xml.text(memberNode, "created_at"),
                        updatedAt: Xml.text(memberNode, "updated_at"),
                    }
                    : null;

                const careTeams = Xml.mapNodes(root, "care_teams > care_team", (node) => {
                    const team = transform.careTeam(node);
                    team.orgId = Xml.text(node, "org_id");
                    team.joinedAt = Xml.text(node, "joined_at");
                    team.roleId = Xml.text(node, "role_id");
                    team.roleCode = Xml.text(node, "role_code");
                    team.roleLabel = Xml.text(node, "role_label");
                    team.patients = Xml.mapNodes(node, "patients > patient", (patientNode) => ({
                        careTeamId: Xml.text(patientNode, "care_team_id"),
                        patientId: Xml.text(patientNode, "patient_id"),
                        name: Xml.text(patientNode, "name"),
                        email: Xml.text(patientNode, "email"),
                    }));
                    return team;
                });

                return {
                    member,
                    careTeams,
                    caregiverAssignments: Xml.mapNodes(root, "caregiver_assignments > caregiver_assignment", transform.caregiverAssignment),
                    groundTruthAnnotations: Xml.mapNodes(root, "ground_truth_annotations > ground_truth_annotation", transform.groundTruthLabel),
                    pushDevices: Xml.mapNodes(root, "push_devices > push_device", transform.pushDevice),
                };
            },
            async createPatient(token, orgId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > patient");
                return transform.patient(node);
            },
            async updatePatient(token, orgId, patientId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > patient") || doc.querySelector("response");
                return node ? transform.patient(node) : null;
            },
            async deletePatient(token, orgId, patientId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            async createCareTeam(token, orgId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > care_team");
                return transform.careTeam(node);
            },
            async listCareTeamRoles(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/member-roles`, { token });
                return Xml.mapNodes(doc, "response > member_roles > member_role", transform.careTeamRole);
            },
            async getCareTeam(token, orgId, careTeamId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}`, { token });
                const teamNode = doc.querySelector("response > care_team");
                if (!teamNode) {
                    return null;
                }
                return {
                    team: transform.careTeam(teamNode),
                    members: Xml.mapNodes(doc, "response > members > member", transform.careTeamMember),
                    patients: Xml.mapNodes(doc, "response > patients > patient", transform.careTeamPatient),
                };
            },
            async updateCareTeam(token, orgId, careTeamId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > care_team");
                return node ? transform.careTeam(node) : null;
            },
            async deleteCareTeam(token, orgId, careTeamId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            async addCareTeamMember(token, orgId, careTeamId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}/members`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > member");
                return node ? transform.careTeamMember(node) : null;
            },
            async removeCareTeamMember(token, orgId, careTeamId, userId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}/members/${userId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            async addCareTeamPatient(token, orgId, careTeamId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}/patients`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > patient");
                return node ? transform.careTeamPatient(node) : null;
            },
            async removeCareTeamPatient(token, orgId, careTeamId, patientId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/${careTeamId}/patients/${patientId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            async listCaregiverRelationshipTypes(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/caregivers/relationship-types`, { token });
                return Xml.mapNodes(doc, "response > relationship_types > relationship_type", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    label: Xml.text(node, "label"),
                }));
            },
            async createCaregiverAssignment(token, orgId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/caregivers/assignments`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > assignment");
                return node ? transform.caregiverAssignment(node) : null;
            },
            async updateCaregiverAssignment(token, orgId, patientId, caregiverId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/caregivers/assignments/${patientId}/${caregiverId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > assignment");
                return node ? transform.caregiverAssignment(node) : null;
            },
            async deleteCaregiverAssignment(token, orgId, patientId, caregiverId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/caregivers/assignments/${patientId}/${caregiverId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            async ackAlert(token, orgId, alertId, payload) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/${alertId}/ack`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                return true;
            },
            async resolveAlert(token, orgId, alertId, payload) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/${alertId}/resolve`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                return true;
            },
            
            // Alerts CRUD
            async getAlert(token, orgId, alertId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/${alertId}`, { token });
                const alertNode = doc.querySelector("response > alert");
                return alertNode ? transform.alert(alertNode) : null;
            },
            async createAlert(token, orgId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > alert");
                return transform.alert(node);
            },
            async updateAlert(token, orgId, alertId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/${alertId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > alert");
                return node ? transform.alert(node) : null;
            },
            async deleteAlert(token, orgId, alertId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/${alertId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },

            async listAlertTypes(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/types`, { token });
                return Xml.mapNodes(doc, "response > alert_types > alert_type", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    description: Xml.text(node, "description"),
                    severity_min_id: Xml.text(node, "severity_min_id"),
                    severity_max_id: Xml.text(node, "severity_max_id"),
                }));
            },

            async listAlertLevels(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/levels`, { token });
                return Xml.mapNodes(doc, "response > alert_levels > alert_level", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    label: Xml.text(node, "label"),
                    weight: Xml.text(node, "weight"),
                }));
            },

            async listAlertStatuses(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/alerts/statuses`, { token });
                return Xml.mapNodes(doc, "response > alert_statuses > alert_status", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    description: Xml.text(node, "description"),
                }));
            },
            
            // Devices
            async listDeviceTypes(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/devices/types`, { token });
                return Xml.mapNodes(doc, "response > device_types > device_type", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    label: Xml.text(node, "label"),
                }));
            },
            async listDevices(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/devices/`, { token });
                return Xml.mapNodes(doc, "response > devices > device", transform.device);
            },
            async getDevice(token, orgId, deviceId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/devices/${deviceId}`, { token });
                const node = doc.querySelector("response > device");
                return node ? transform.device(node) : null;
            },
            async createDevice(token, orgId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/devices/`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > device");
                return transform.device(node);
            },
            async updateDevice(token, orgId, deviceId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/devices/${deviceId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > device");
                return node ? transform.device(node) : null;
            },
            async deleteDevice(token, orgId, deviceId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/devices/${deviceId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            
            // Push Devices
            async listPushPlatforms(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/push-devices/platforms`, { token });
                return Xml.mapNodes(doc, "response > platforms > platform", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    label: Xml.text(node, "label"),
                }));
            },
            async listPushDevices(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/push-devices/`, { token });
                return Xml.mapNodes(doc, "response > push_devices > push_device", transform.pushDevice);
            },
            async togglePushDevice(token, orgId, pushDeviceId, isActive) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/push-devices/${pushDeviceId}`, {
                    method: "PATCH",
                    token,
                    body: { active: isActive },
                });
                const node = doc.querySelector("response > push_device");
                return node ? transform.pushDevice(node) : null;
            },
            async deletePushDevice(token, orgId, pushDeviceId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/push-devices/${pushDeviceId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            
            // Ground Truth Labels
            async listGroundTruthEventTypes(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/ground-truth/event-types`, { token });
                return Xml.mapNodes(doc, "response > event_types > event_type", (node) => ({
                    id: Xml.text(node, "id"),
                    code: Xml.text(node, "code"),
                    description: Xml.text(node, "description"),
                }));
            },
            async listGroundTruthLabels(token, orgId, patientId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/ground-truth`, { token });
                return Xml.mapNodes(doc, "response > ground_truth_labels > ground_truth_label", transform.groundTruthLabel);
            },
            async getGroundTruthLabel(token, orgId, patientId, labelId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/ground-truth/${labelId}`, { token });
                const node = doc.querySelector("response > ground_truth_label");
                return node ? transform.groundTruthLabel(node) : null;
            },
            async createGroundTruthLabel(token, orgId, patientId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/ground-truth/`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > ground_truth_label");
                return transform.groundTruthLabel(node);
            },
            async updateGroundTruthLabel(token, orgId, patientId, labelId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/ground-truth/${labelId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > ground_truth_label");
                return node ? transform.groundTruthLabel(node) : null;
            },
            async deleteGroundTruthLabel(token, orgId, patientId, labelId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/ground-truth/${labelId}`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
            
            // Patient Locations
            async listPatientLocations(token, orgId, patientId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/locations/`, { token });
                return Xml.mapNodes(doc, "response > locations > location", transform.patientLocation);
            },
            async createPatientLocation(token, orgId, patientId, payload) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/locations/`, {
                    method: "POST",
                    token,
                    body: payload,
                });
                const node = doc.querySelector("response > location");
                return transform.patientLocation(node);
            },
            async deletePatientLocation(token, orgId, patientId, locationId) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/${patientId}/locations/${locationId}/`, {
                    method: "DELETE",
                    token,
                });
                return true;
            },
        },
    };
})();
