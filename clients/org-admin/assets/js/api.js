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
                token: Xml.text(node, "token"),
                expiresAt: Xml.text(node, "expires_at"),
                createdAt: Xml.text(node, "created_at"),
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
        caregiverAssignment(node) {
            return {
                patientId: Xml.text(node, "patient_id"),
                patientName: Xml.text(node, "patient_name"),
                caregiverUserId: Xml.text(node, "caregiver_user_id"),
                caregiverName: Xml.text(node, "caregiver_name"),
                caregiverEmail: Xml.text(node, "caregiver_email"),
                relationshipCode: Xml.text(node, "relationship_type_code"),
                relationshipLabel: Xml.text(node, "relationship_type_label"),
                isPrimary: Xml.bool(node, "is_primary"),
                startedAt: Xml.text(node, "started_at"),
                note: Xml.text(node, "note"),
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
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/dashboard${params}`, { token });
                const statsNode = doc.querySelector("dashboard > stats");
                if (!statsNode) {
                    throw new Error("El dashboard no devolvio estadisticas");
                }
                return {
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
            },
            async listStaff(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/`, { token });
                return Xml.mapNodes(doc, "response > staff_members > staff_member", transform.staffMember);
            },
            async listPatients(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/patients/`, { token });
                return Xml.mapNodes(doc, "response > patients > patient", transform.patient);
            },
            async listCareTeams(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/care-teams/`, { token });
                return Xml.mapNodes(doc, "response > care_teams > care_team", transform.careTeam);
            },
            async listCaregiverAssignments(token, orgId) {
                const doc = await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/caregivers/assignments`, { token });
                return Xml.mapNodes(doc, "response > caregiver_assignments > assignment", transform.caregiverAssignment);
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
            async updateStaffRole(token, orgId, userId, payload) {
                await requestXml(`${cfg.adminBasePath}/organizations/${orgId}/staff/${userId}`, {
                    method: "PATCH",
                    token,
                    body: payload,
                });
                return true;
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
        },
    };
})();
