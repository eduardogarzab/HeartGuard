"""Repositorio de acceso a datos para usuarios"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..extensions import get_db_cursor


class UserRepository:
    """Operaciones de base de datos relacionadas con usuarios"""

    @staticmethod
    def get_user_profile(user_id: str) -> Optional[Dict]:
        query = """
            SELECT
                u.id,
                u.name,
                u.email,
                u.role_code,
                u.two_factor_enabled,
                u.profile_photo_url,
                u.created_at,
                u.updated_at,
                us.code AS status_code,
                us.label AS status_label
            FROM users u
            JOIN user_statuses us ON us.id = u.user_status_id
            WHERE u.id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone()

    @staticmethod
    def update_user_profile(user_id: str, updates: Dict) -> Optional[Dict]:
        allowed_columns = {
            'name': 'name',
            'profile_photo_url': 'profile_photo_url',
            'two_factor_enabled': 'two_factor_enabled',
        }
        set_parts: List[str] = []
        values: List[Any] = []

        for field, column in allowed_columns.items():
            if field in updates:
                set_parts.append(f"{column} = %s")
                values.append(updates[field])

        if not set_parts:
            return None

        set_parts.append('updated_at = NOW()')
        query = f"""
            UPDATE users
            SET {', '.join(set_parts)}
            WHERE id = %s
            RETURNING id
        """
        values.append(user_id)

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(values))
            return cursor.fetchone()

    @staticmethod
    def list_memberships(user_id: str) -> List[Dict]:
        query = """
            SELECT
                m.org_id,
                o.code AS org_code,
                o.name AS org_name,
                m.role_code,
                COALESCE(r.label, m.role_code) AS role_label,
                m.joined_at
            FROM user_org_membership m
            JOIN organizations o ON o.id = m.org_id
            LEFT JOIN roles r ON r.code = m.role_code
            WHERE m.user_id = %s
            ORDER BY o.name ASC, m.joined_at DESC
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def get_membership(org_id: str, user_id: str) -> Optional[Dict]:
        query = """
            SELECT
                m.org_id,
                m.user_id,
                m.role_code,
                COALESCE(r.label, m.role_code) AS role_label,
                m.joined_at,
                o.code AS org_code,
                o.name AS org_name
            FROM user_org_membership m
            JOIN organizations o ON o.id = m.org_id
            LEFT JOIN roles r ON r.code = m.role_code
            WHERE m.org_id = %s AND m.user_id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id, user_id))
            return cursor.fetchone()

    @staticmethod
    def get_org_overview(org_id: str) -> Dict[str, Any]:
        query = """
            WITH
            patients_count AS (
                SELECT COUNT(*)::int AS total_patients
                FROM patients
                WHERE org_id = %s
            ),
            care_team_count AS (
                SELECT COUNT(*)::int AS total_care_teams
                FROM care_teams
                WHERE org_id = %s
            ),
            caregiver_count AS (
                SELECT COUNT(DISTINCT cp.user_id)::int AS total_caregivers
                FROM caregiver_patient cp
                JOIN patients p ON p.id = cp.patient_id
                WHERE p.org_id = %s
                  AND (cp.ended_at IS NULL OR cp.ended_at > NOW())
            ),
            alerts_last_7d AS (
                SELECT COUNT(*)::int AS total_alerts_7d
                FROM alerts a
                JOIN patients p ON p.id = a.patient_id
                WHERE p.org_id = %s
                  AND a.created_at >= NOW() - INTERVAL '7 days'
            ),
            alerts_open AS (
                SELECT COUNT(*)::int AS total_open_alerts
                FROM alerts a
                JOIN patients p ON p.id = a.patient_id
                JOIN alert_status ast ON ast.id = a.status_id
                WHERE p.org_id = %s
                  AND lower(ast.code) IN ('created', 'notified')
            ),
            latest_alert AS (
                SELECT MAX(a.created_at) AS latest_alert_at
                FROM alerts a
                JOIN patients p ON p.id = a.patient_id
                WHERE p.org_id = %s
            )
            SELECT
                COALESCE((SELECT total_patients FROM patients_count), 0) AS total_patients,
                COALESCE((SELECT total_care_teams FROM care_team_count), 0) AS total_care_teams,
                COALESCE((SELECT total_caregivers FROM caregiver_count), 0) AS total_caregivers,
                COALESCE((SELECT total_alerts_7d FROM alerts_last_7d), 0) AS alerts_last_7d,
                COALESCE((SELECT total_open_alerts FROM alerts_open), 0) AS open_alerts,
                (SELECT latest_alert_at FROM latest_alert) AS latest_alert_at
        """
        params = (org_id, org_id, org_id, org_id, org_id, org_id)
        with get_db_cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone() or {}
            return dict(row)

    @staticmethod
    def list_org_care_teams(org_id: str) -> List[Dict]:
        query = """
            SELECT
                ct.id AS care_team_id,
                ct.name AS care_team_name,
                ct.created_at,
                ctm.user_id AS member_user_id,
                u.name AS member_name,
                u.email AS member_email,
                tm.code AS member_role_code,
                tm.label AS member_role_label
            FROM care_teams ct
            LEFT JOIN care_team_member ctm ON ctm.care_team_id = ct.id
            LEFT JOIN users u ON u.id = ctm.user_id
            LEFT JOIN team_member_roles tm ON tm.id = ctm.role_id
            WHERE ct.org_id = %s
            ORDER BY ct.name ASC, member_name ASC NULLS LAST
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id,))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def list_org_care_team_patients(org_id: str) -> List[Dict]:
        query = """
            SELECT
                ct.id AS care_team_id,
                ct.name AS care_team_name,
                p.id AS patient_id,
                p.person_name AS patient_name,
                p.email AS patient_email,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label
            FROM care_teams ct
            JOIN patient_care_team pct ON pct.care_team_id = ct.id
            JOIN patients p ON p.id = pct.patient_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            WHERE ct.org_id = %s
            ORDER BY ct.name ASC, patient_name ASC
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id,))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def get_patient(org_id: str, patient_id: str) -> Optional[Dict]:
        query = """
            SELECT
                p.id,
                p.org_id,
                p.person_name,
                p.email,
                p.birthdate,
                p.created_at,
                p.profile_photo_url,
                p.sex_id,
                p.risk_level_id,
                o.name AS org_name,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label,
                sx.code AS sex_code,
                sx.label AS sex_label
            FROM patients p
            JOIN organizations o ON o.id = p.org_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            LEFT JOIN sexes sx ON sx.id = p.sex_id
            WHERE p.org_id = %s AND p.id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id, patient_id))
            return cursor.fetchone()

    @staticmethod
    def get_patient_by_id(patient_id: str) -> Optional[Dict]:
        query = """
            SELECT
                p.id,
                p.org_id,
                p.person_name,
                p.email,
                p.birthdate,
                p.created_at,
                p.profile_photo_url,
                p.sex_id,
                p.risk_level_id,
                o.name AS org_name,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label,
                sx.code AS sex_code,
                sx.label AS sex_label
            FROM patients p
            LEFT JOIN organizations o ON o.id = p.org_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            LEFT JOIN sexes sx ON sx.id = p.sex_id
            WHERE p.id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (patient_id,))
            return cursor.fetchone()

    @staticmethod
    def list_patient_alerts(patient_id: str, limit: int, offset: int) -> List[Dict]:
        query = """
            SELECT
                a.id,
                a.created_at,
                a.description,
                at.code AS alert_type_code,
                at.description AS alert_type_label,
                al.code AS level_code,
                al.label AS level_label,
                ast.code AS status_code,
                ast.description AS status_label
            FROM alerts a
            JOIN alert_types at ON at.id = a.type_id
            JOIN alert_levels al ON al.id = a.alert_level_id
            JOIN alert_status ast ON ast.id = a.status_id
            WHERE a.patient_id = %s
            ORDER BY a.created_at DESC
            LIMIT %s OFFSET %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (patient_id, limit, offset))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def list_patient_notes(patient_id: str, limit: int) -> List[Dict]:
        query = """
            SELECT
                g.id,
                g.patient_id,
                g.event_type_id,
                g.onset,
                g.offset_at,
                g.annotated_by_user_id,
                g.source,
                g.note,
                et.code AS event_code,
                et.description AS event_label,
                u.name AS annotated_by_name
            FROM ground_truth_labels g
            JOIN event_types et ON et.id = g.event_type_id
            LEFT JOIN users u ON u.id = g.annotated_by_user_id
            WHERE g.patient_id = %s
            ORDER BY g.onset DESC
            LIMIT %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (patient_id, limit))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def list_caregiver_patients(user_id: str) -> List[Dict]:
        query = """
            SELECT
                cp.patient_id,
                cp.user_id,
                cp.is_primary,
                cp.started_at,
                cp.ended_at,
                cp.note AS relationship_note,
                crt.code AS relationship_code,
                crt.label AS relationship_label,
                p.person_name AS patient_name,
                p.email AS patient_email,
                p.org_id,
                o.name AS org_name,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label
            FROM caregiver_patient cp
            JOIN patients p ON p.id = cp.patient_id
            LEFT JOIN organizations o ON o.id = p.org_id
            LEFT JOIN caregiver_relationship_types crt ON crt.id = cp.rel_type_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            WHERE cp.user_id = %s
            ORDER BY p.person_name ASC
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def get_caregiver_relationship(user_id: str, patient_id: str) -> Optional[Dict]:
        query = """
            SELECT
                cp.patient_id,
                cp.user_id,
                cp.is_primary,
                cp.started_at,
                cp.ended_at,
                cp.note AS relationship_note,
                crt.code AS relationship_code,
                crt.label AS relationship_label
            FROM caregiver_patient cp
            LEFT JOIN caregiver_relationship_types crt ON crt.id = cp.rel_type_id
            WHERE cp.user_id = %s AND cp.patient_id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id, patient_id))
            return cursor.fetchone()

    @staticmethod
    def create_patient_note(
        *,
        patient_id: str,
        user_id: str,
        event_code: str,
        onset,
        offset_at,
        note: Optional[str],
        source: str,
    ) -> Optional[str]:
        event_query = """
            SELECT id, code, description
            FROM event_types
            WHERE lower(code) = lower(%s)
            LIMIT 1
        """
        insert_query = """
            INSERT INTO ground_truth_labels (
                patient_id,
                event_type_id,
                onset,
                offset_at,
                annotated_by_user_id,
                source,
                note
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """
        with get_db_cursor() as cursor:
            cursor.execute(event_query, (event_code,))
            event_type = cursor.fetchone()
            if not event_type:
                return None
            cursor.execute(
                insert_query,
                (patient_id, event_type['id'], onset, offset_at, user_id, source, note),
            )
            created = cursor.fetchone()
            if not created:
                return None
        return str(created['id'])

    @staticmethod
    def get_patient_note(note_id: str) -> Optional[Dict]:
        query = """
            SELECT
                g.id,
                g.patient_id,
                g.event_type_id,
                g.onset,
                g.offset_at,
                g.annotated_by_user_id,
                g.source,
                g.note,
                et.code AS event_code,
                et.description AS event_label,
                u.name AS annotated_by_name
            FROM ground_truth_labels g
            JOIN event_types et ON et.id = g.event_type_id
            LEFT JOIN users u ON u.id = g.annotated_by_user_id
            WHERE g.id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (note_id,))
            return cursor.fetchone()

    @staticmethod
    def list_care_team_patient_locations(
        user_id: str,
        *,
        org_id: Optional[str],
        care_team_id: Optional[str],
        alert_level: Optional[str],
        updated_after,
        bbox: Optional[Dict[str, float]],
        limit: int,
    ) -> List[Dict]:
        org_clause = ""
        care_team_clause = ""
        params: List[Any] = [user_id]

        if org_id:
            org_clause = " AND ct.org_id = %s"
            params.append(org_id)

        if care_team_id:
            care_team_clause = " AND ct.id = %s"
            params.append(care_team_id)

        location_clauses: List[str] = []
        if updated_after:
            location_clauses.append("pl.ts >= %s")
            params.append(updated_after)

        if bbox:
            location_clauses.append("pl.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)")
            params.extend([
                bbox['min_lng'],
                bbox['min_lat'],
                bbox['max_lng'],
                bbox['max_lat'],
            ])

        location_filter_sql = ""
        if location_clauses:
            location_filter_sql = " AND " + " AND ".join(location_clauses)

        alert_level_clause = ""
        if alert_level:
            alert_level_clause = " AND la.alert_level_code IS NOT NULL AND lower(la.alert_level_code) = %s"
            params.append(alert_level)

        updated_clause = ""
        if updated_after:
            updated_clause = " AND ll.ts IS NOT NULL AND ll.ts >= %s"
            params.append(updated_after)

        bbox_clause = ""
        if bbox:
            bbox_clause = " AND ll.geom IS NOT NULL"

        query = f"""
            WITH user_teams AS (
                SELECT
                    ct.id AS care_team_id,
                    ct.name AS care_team_name,
                    ct.org_id,
                    o.name AS org_name
                FROM care_team_member ctm
                JOIN care_teams ct ON ct.id = ctm.care_team_id
                JOIN organizations o ON o.id = ct.org_id
                WHERE ctm.user_id = %s
                {org_clause}
                {care_team_clause}
            ),
            team_patients AS (
                SELECT
                    up.care_team_id,
                    up.care_team_name,
                    up.org_id,
                    up.org_name,
                    pct.patient_id
                FROM user_teams up
                JOIN patient_care_team pct ON pct.care_team_id = up.care_team_id
            ),
            latest_locations AS (
                SELECT DISTINCT ON (pl.patient_id)
                    pl.patient_id,
                    pl.ts,
                    pl.geom
                FROM patient_locations pl
                JOIN team_patients tp ON tp.patient_id = pl.patient_id
                WHERE 1=1
                {location_filter_sql}
                ORDER BY pl.patient_id, pl.ts DESC
            ),
            latest_alerts AS (
                SELECT DISTINCT ON (a.patient_id)
                    a.patient_id,
                    a.id,
                    a.created_at,
                    at.code AS alert_code,
                    at.description AS alert_label,
                    al.code AS alert_level_code,
                    al.label AS alert_level_label
                FROM alerts a
                JOIN alert_types at ON at.id = a.type_id
                JOIN alert_levels al ON al.id = a.alert_level_id
                JOIN team_patients tp ON tp.patient_id = a.patient_id
                ORDER BY a.patient_id, a.created_at DESC
            )
            SELECT
                tp.patient_id,
                p.person_name AS patient_name,
                p.email AS patient_email,
                tp.care_team_id,
                tp.care_team_name,
                tp.org_id,
                tp.org_name,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label,
                ll.ts AS last_location_at,
                ST_X(ll.geom) AS longitude,
                ST_Y(ll.geom) AS latitude,
                la.id AS alert_id,
                la.created_at AS alert_created_at,
                la.alert_code,
                la.alert_label,
                la.alert_level_code,
                la.alert_level_label
            FROM team_patients tp
            JOIN patients p ON p.id = tp.patient_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            LEFT JOIN latest_locations ll ON ll.patient_id = tp.patient_id
            LEFT JOIN latest_alerts la ON la.patient_id = tp.patient_id
            WHERE 1=1
            {alert_level_clause}
            {updated_clause}
            {bbox_clause}
            ORDER BY ll.ts DESC NULLS LAST, p.person_name ASC
            LIMIT %s
        """.format(
            org_clause=org_clause,
            care_team_clause=care_team_clause,
            location_filter_sql=location_filter_sql,
            alert_level_clause=alert_level_clause,
            updated_clause=updated_clause,
            bbox_clause=bbox_clause,
        )

        params.append(limit)

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def list_care_team_member_locations(
        user_id: str,
        *,
        org_id: Optional[str],
        care_team_id: Optional[str],
        alert_level: Optional[str],
        updated_after,
        bbox: Optional[Dict[str, float]],
        limit: int,
    ) -> List[Dict]:
        org_clause = ""
        care_team_clause = ""
        params: List[Any] = [user_id]

        if org_id:
            org_clause = " AND ct.org_id = %s"
            params.append(org_id)

        if care_team_id:
            care_team_clause = " AND ct.id = %s"
            params.append(care_team_id)

        location_clauses: List[str] = []
        if updated_after:
            location_clauses.append("pl.ts >= %s")
            params.append(updated_after)

        if bbox:
            location_clauses.append("pl.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)")
            params.extend([
                bbox['min_lng'],
                bbox['min_lat'],
                bbox['max_lng'],
                bbox['max_lat'],
            ])

        location_filter_sql = ""
        if location_clauses:
            location_filter_sql = " AND " + " AND ".join(location_clauses)

        filtered_alert_clause = ""
        if alert_level:
            filtered_alert_clause = " AND la.alert_level_code IS NOT NULL AND lower(la.alert_level_code) = %s"
            params.append(alert_level)

        filtered_updated_clause = ""
        if updated_after:
            filtered_updated_clause = " AND ll.ts IS NOT NULL AND ll.ts >= %s"
            params.append(updated_after)

        filtered_bbox_clause = ""
        if bbox:
            filtered_bbox_clause = " AND ll.geom IS NOT NULL"

        has_strict_filters = bool(alert_level or updated_after or bbox)

        query = f"""
            WITH user_teams AS (
                SELECT
                    ct.id AS care_team_id,
                    ct.name AS care_team_name,
                    ct.org_id,
                    o.name AS org_name
                FROM care_team_member ctm
                JOIN care_teams ct ON ct.id = ctm.care_team_id
                JOIN organizations o ON o.id = ct.org_id
                WHERE ctm.user_id = %s
                {org_clause}
                {care_team_clause}
            ),
            team_patients AS (
                SELECT
                    up.care_team_id,
                    up.care_team_name,
                    up.org_id,
                    up.org_name,
                    pct.patient_id
                FROM user_teams up
                JOIN patient_care_team pct ON pct.care_team_id = up.care_team_id
            ),
            latest_locations AS (
                SELECT DISTINCT ON (pl.patient_id)
                    pl.patient_id,
                    pl.ts,
                    pl.geom
                FROM patient_locations pl
                JOIN team_patients tp ON tp.patient_id = pl.patient_id
                WHERE 1=1
                {location_filter_sql}
                ORDER BY pl.patient_id, pl.ts DESC
            ),
            latest_alerts AS (
                SELECT DISTINCT ON (a.patient_id)
                    a.patient_id,
                    al.code AS alert_level_code
                FROM alerts a
                JOIN alert_levels al ON al.id = a.alert_level_id
                JOIN team_patients tp ON tp.patient_id = a.patient_id
                ORDER BY a.patient_id, a.created_at DESC
            ),
            filtered_patients AS (
                SELECT
                    tp.care_team_id,
                    tp.patient_id,
                    ll.geom,
                    ll.ts,
                    la.alert_level_code
                FROM team_patients tp
                LEFT JOIN latest_locations ll ON ll.patient_id = tp.patient_id
                LEFT JOIN latest_alerts la ON la.patient_id = tp.patient_id
                WHERE 1=1
                {filtered_alert_clause}
                {filtered_updated_clause}
                {filtered_bbox_clause}
            ),
            team_centroids AS (
                SELECT
                    fp.care_team_id,
                    CASE
                        WHEN COUNT(fp.geom) > 0 THEN ST_Centroid(ST_Collect(fp.geom))
                        ELSE NULL
                    END AS centroid_geom,
                    MAX(fp.ts) AS last_seen_at
                FROM filtered_patients fp
                WHERE fp.geom IS NOT NULL
                GROUP BY fp.care_team_id
            ),
            teams_with_matches AS (
                SELECT DISTINCT care_team_id
                FROM filtered_patients
            )
            SELECT
                tm.user_id AS member_user_id,
                u.name AS member_name,
                u.email AS member_email,
                role.code AS role_code,
                role.label AS role_label,
                tm.joined_at,
                up.care_team_id,
                up.care_team_name,
                up.org_id,
                up.org_name,
                ST_X(tc.centroid_geom) AS centroid_longitude,
                ST_Y(tc.centroid_geom) AS centroid_latitude,
                tc.last_seen_at
            FROM care_team_member tm
            JOIN user_teams up ON up.care_team_id = tm.care_team_id
            JOIN users u ON u.id = tm.user_id
            LEFT JOIN team_centroids tc ON tc.care_team_id = tm.care_team_id
            LEFT JOIN team_member_roles role ON role.id = tm.role_id
            WHERE tm.user_id <> %s
              AND (%s = FALSE OR up.care_team_id IN (SELECT care_team_id FROM teams_with_matches))
            ORDER BY up.care_team_name ASC, u.name ASC
            LIMIT %s
        """.format(
            org_clause=org_clause,
            care_team_clause=care_team_clause,
            location_filter_sql=location_filter_sql,
            filtered_alert_clause=filtered_alert_clause,
            filtered_updated_clause=filtered_updated_clause,
            filtered_bbox_clause=filtered_bbox_clause,
        )

        params.append(user_id)
        params.append(has_strict_filters)
        params.append(limit)

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def list_caregiver_patient_locations(
        user_id: str,
        *,
        updated_after,
        bbox: Optional[Dict[str, float]],
        risk_level: Optional[str],
        has_active_alerts: Optional[bool],
        include_without_location: bool,
        sort_by: str,
        limit: int,
        offset: int,
    ) -> List[Dict]:
        params: List[Any] = [user_id]

        location_clauses: List[str] = []
        if updated_after:
            location_clauses.append("pl.ts >= %s")
            params.append(updated_after)

        if bbox:
            location_clauses.append("pl.geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)")
            params.extend([
                bbox['min_lng'],
                bbox['min_lat'],
                bbox['max_lng'],
                bbox['max_lat'],
            ])

        location_filter_sql = ""
        if location_clauses:
            location_filter_sql = " AND " + " AND ".join(location_clauses)

        risk_clause = ""
        if risk_level:
            risk_clause = " AND rl.code IS NOT NULL AND lower(rl.code) = %s"
            params.append(risk_level)

        updated_clause = ""
        if updated_after:
            if include_without_location:
                updated_clause = " AND (ll.ts IS NULL OR ll.ts >= %s)"
            else:
                updated_clause = " AND ll.ts IS NOT NULL AND ll.ts >= %s"
            params.append(updated_after)

        bbox_clause = ""
        if bbox:
            bbox_clause = " AND ll.geom IS NOT NULL"

        location_requirement_clause = ""
        if not include_without_location and not bbox_clause:
            location_requirement_clause = " AND ll.geom IS NOT NULL"

        alerts_clause = ""
        if has_active_alerts is True:
            alerts_clause = " AND la.status_code IS NOT NULL AND lower(la.status_code) IN ('created','notified','ack')"
        elif has_active_alerts is False:
            alerts_clause = " AND (la.status_code IS NULL OR lower(la.status_code) NOT IN ('created','notified','ack'))"

        order_clause = "ORDER BY ll.ts DESC NULLS LAST, la.alert_level_weight DESC NULLS LAST, p.person_name ASC"
        if sort_by == 'severity':
            order_clause = "ORDER BY la.alert_level_weight DESC NULLS LAST, ll.ts DESC NULLS LAST, p.person_name ASC"

        query = f"""
            WITH caregiver_patients AS (
                SELECT
                    cp.patient_id
                FROM caregiver_patient cp
                WHERE cp.user_id = %s
            ),
            latest_locations AS (
                SELECT DISTINCT ON (pl.patient_id)
                    pl.patient_id,
                    pl.ts,
                    pl.geom
                FROM patient_locations pl
                JOIN caregiver_patients cp ON cp.patient_id = pl.patient_id
                WHERE 1=1
                {location_filter_sql}
                ORDER BY pl.patient_id, pl.ts DESC
            ),
            latest_alerts AS (
                SELECT DISTINCT ON (a.patient_id)
                    a.patient_id,
                    at.code AS alert_code,
                    at.description AS alert_label,
                    al.code AS alert_level_code,
                    al.label AS alert_level_label,
                    al.weight AS alert_level_weight,
                    ast.code AS status_code
                FROM alerts a
                JOIN alert_types at ON at.id = a.type_id
                JOIN alert_levels al ON al.id = a.alert_level_id
                JOIN alert_status ast ON ast.id = a.status_id
                JOIN caregiver_patients cp ON cp.patient_id = a.patient_id
                ORDER BY a.patient_id, a.created_at DESC
            )
            SELECT
                cp.patient_id,
                p.person_name AS patient_name,
                p.email AS patient_email,
                rl.code AS risk_level_code,
                rl.label AS risk_level_label,
                ll.ts AS last_location_at,
                ST_X(ll.geom) AS longitude,
                ST_Y(ll.geom) AS latitude,
                la.alert_code,
                la.alert_label,
                la.alert_level_code,
                la.alert_level_label,
                la.alert_level_weight,
                la.status_code
            FROM caregiver_patients cp
            JOIN patients p ON p.id = cp.patient_id
            LEFT JOIN risk_levels rl ON rl.id = p.risk_level_id
            LEFT JOIN latest_locations ll ON ll.patient_id = cp.patient_id
            LEFT JOIN latest_alerts la ON la.patient_id = cp.patient_id
            WHERE 1=1
            {risk_clause}
            {updated_clause}
            {bbox_clause}
            {location_requirement_clause}
            {alerts_clause}
            {order_clause}
            LIMIT %s OFFSET %s
        """.format(
            location_filter_sql=location_filter_sql,
            risk_clause=risk_clause,
            updated_clause=updated_clause,
            bbox_clause=bbox_clause,
            location_requirement_clause=location_requirement_clause,
            alerts_clause=alerts_clause,
            order_clause=order_clause,
        )

        params.extend([limit, offset])

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def get_org_metrics(org_id: str) -> Dict[str, Any]:
        query = """
            WITH patient_alerts AS (
                SELECT
                    p.id AS patient_id,
                    COUNT(a.*)::int AS alert_count
                FROM patients p
                LEFT JOIN alerts a ON a.patient_id = p.id
                WHERE p.org_id = %s
                GROUP BY p.id
            )
            SELECT
                COALESCE(SUM(alert_count), 0) AS total_alerts,
                COALESCE(MAX(alert_count), 0) AS max_alerts_by_patient,
                COALESCE(AVG(alert_count), 0) AS avg_alerts_per_patient
            FROM patient_alerts
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id,))
            row = cursor.fetchone() or {}
            return dict(row)

    @staticmethod
    def get_caregiver_metrics(user_id: str) -> Dict[str, Any]:
        query = """
            WITH active_patients AS (
                SELECT cp.patient_id
                FROM caregiver_patient cp
                WHERE cp.user_id = %s
                  AND (cp.ended_at IS NULL OR cp.ended_at > NOW())
            ),
            alerts_window AS (
                SELECT COUNT(*)::int AS recent_alerts
                FROM alerts a
                JOIN active_patients ap ON ap.patient_id = a.patient_id
                WHERE a.created_at >= NOW() - INTERVAL '14 days'
            ),
            patient_count AS (
                SELECT COUNT(*)::int AS patients
                FROM active_patients
            )
            SELECT
                COALESCE((SELECT patients FROM patient_count), 0) AS active_patients,
                COALESCE((SELECT recent_alerts FROM alerts_window), 0) AS alerts_last_14d
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            row = cursor.fetchone() or {}
            return dict(row)

    # ------------------------------------------------------------------
    # Dispositivos clínicos
    # ------------------------------------------------------------------
    @staticmethod
    def get_care_team_membership(org_id: str, care_team_id: str, user_id: str) -> Optional[Dict]:
        query = """
            SELECT
                ct.id AS care_team_id,
                ct.name AS care_team_name,
                ct.org_id,
                o.name AS org_name,
                ctm.user_id,
                ctm.joined_at,
                tm.code AS role_code,
                tm.label AS role_label
            FROM care_team_member ctm
            JOIN care_teams ct ON ct.id = ctm.care_team_id
            JOIN organizations o ON o.id = ct.org_id
            LEFT JOIN team_member_roles tm ON tm.id = ctm.role_id
            WHERE ct.org_id = %s AND ct.id = %s AND ctm.user_id = %s
            LIMIT 1
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (org_id, care_team_id, user_id))
            return cursor.fetchone()

    @staticmethod
    def list_care_team_devices(
        org_id: str,
        care_team_id: str,
        *,
        patient_id: Optional[str],
        active: Optional[bool],
        limit: int,
        offset: int,
    ) -> List[Dict]:
        patient_clause = ""
        active_clause = ""
        params: List[Any] = [care_team_id, org_id]

        if active is not None:
            active_clause = " AND d.active = %s"
            params.append(active)

        if patient_id:
            patient_clause = " AND tp.patient_id = %s"
            params.append(patient_id)

        params.extend([limit, offset])

        query = f"""
            WITH team_patients AS (
                SELECT pct.patient_id
                FROM patient_care_team pct
                WHERE pct.care_team_id = %s
            ),
            latest_streams AS (
                SELECT
                    ss.device_id,
                    MAX(ss.started_at) AS last_started_at,
                    MAX(ss.ended_at) AS last_ended_at,
                    COUNT(*)::int AS total_streams
                FROM signal_streams ss
                GROUP BY ss.device_id
            )
            SELECT
                d.id,
                d.serial,
                d.brand,
                d.model,
                d.active,
                d.registered_at,
                d.owner_patient_id,
                dt.code AS device_type_code,
                dt.label AS device_type_label,
                p.person_name AS patient_name,
                p.email AS patient_email,
                ls.last_started_at,
                ls.last_ended_at,
                ls.total_streams
            FROM devices d
            JOIN team_patients tp ON tp.patient_id = d.owner_patient_id
            JOIN patients p ON p.id = d.owner_patient_id
            JOIN device_types dt ON dt.id = d.device_type_id
            LEFT JOIN latest_streams ls ON ls.device_id = d.id
            WHERE d.org_id = %s
            {active_clause}
            {patient_clause}
            ORDER BY p.person_name ASC, d.serial ASC
            LIMIT %s OFFSET %s
        """

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def get_care_team_device(
        org_id: str,
        care_team_id: str,
        device_id: str,
    ) -> Optional[Dict]:
        params: List[Any] = [care_team_id, device_id, org_id, device_id]

        query = """
            WITH team_patients AS (
                SELECT pct.patient_id
                FROM patient_care_team pct
                WHERE pct.care_team_id = %s
            ),
            latest_streams AS (
                SELECT
                    ss.device_id,
                    MAX(ss.started_at) AS last_started_at,
                    MAX(ss.ended_at) AS last_ended_at,
                    COUNT(*)::int AS total_streams
                FROM signal_streams ss
                WHERE ss.device_id = %s
                GROUP BY ss.device_id
            )
            SELECT
                d.id,
                d.serial,
                d.brand,
                d.model,
                d.active,
                d.registered_at,
                d.owner_patient_id,
                dt.code AS device_type_code,
                dt.label AS device_type_label,
                p.person_name AS patient_name,
                p.email AS patient_email,
                ls.last_started_at,
                ls.last_ended_at,
                ls.total_streams
            FROM devices d
            JOIN team_patients tp ON tp.patient_id = d.owner_patient_id
            JOIN patients p ON p.id = d.owner_patient_id
            JOIN device_types dt ON dt.id = d.device_type_id
            LEFT JOIN latest_streams ls ON ls.device_id = d.id
            WHERE d.org_id = %s
              AND d.id = %s
            LIMIT 1
        """

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchone()

    @staticmethod
    def list_care_team_device_streams(
        org_id: str,
        care_team_id: str,
        device_id: str,
        *,
        limit: int,
        offset: int,
    ) -> List[Dict]:
        params: List[Any] = [care_team_id, org_id, device_id, limit, offset]

        query = """
            WITH team_patients AS (
                SELECT pct.patient_id
                FROM patient_care_team pct
                WHERE pct.care_team_id = %s
            ),
            allowed_devices AS (
                SELECT d.id
                FROM devices d
                JOIN team_patients tp ON tp.patient_id = d.owner_patient_id
                WHERE d.org_id = %s
            )
            SELECT
                ss.id,
                ss.patient_id,
                ss.device_id,
                ss.sample_rate_hz,
                ss.started_at,
                ss.ended_at,
                st.code AS signal_type_code,
                st.label AS signal_type_label
            FROM signal_streams ss
            JOIN allowed_devices ad ON ad.id = ss.device_id
            JOIN signal_types st ON st.id = ss.signal_type_id
            WHERE ss.device_id = %s
            ORDER BY ss.started_at DESC
            LIMIT %s OFFSET %s
        """

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def list_care_team_disconnected_devices(
        org_id: str,
        care_team_id: str,
        *,
        limit: int,
        offset: int,
    ) -> List[Dict]:
        params: List[Any] = [care_team_id, org_id, limit, offset]

        query = """
            WITH team_patients AS (
                SELECT pct.patient_id
                FROM patient_care_team pct
                WHERE pct.care_team_id = %s
            ),
            latest_streams AS (
                SELECT
                    ss.device_id,
                    MAX(ss.started_at) AS last_started_at,
                    MAX(ss.ended_at) AS last_ended_at,
                    COUNT(*)::int AS total_streams
                FROM signal_streams ss
                GROUP BY ss.device_id
            )
            SELECT
                d.id,
                d.serial,
                d.brand,
                d.model,
                d.active,
                d.registered_at,
                d.owner_patient_id,
                dt.code AS device_type_code,
                dt.label AS device_type_label,
                p.person_name AS patient_name,
                p.email AS patient_email,
                ls.last_started_at,
                ls.last_ended_at,
                ls.total_streams
            FROM devices d
            JOIN team_patients tp ON tp.patient_id = d.owner_patient_id
            JOIN patients p ON p.id = d.owner_patient_id
            JOIN device_types dt ON dt.id = d.device_type_id
            LEFT JOIN latest_streams ls ON ls.device_id = d.id
            WHERE d.org_id = %s
              AND d.active = TRUE
              AND (ls.last_started_at IS NULL OR ls.last_started_at <= NOW() - INTERVAL '24 hours')
            ORDER BY ls.last_started_at NULLS FIRST, d.serial ASC
            LIMIT %s OFFSET %s
        """

        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall() or []
            return list(rows)

    # ------------------------------------------------------------------
    # Dispositivos push
    # ------------------------------------------------------------------
    @staticmethod
    def get_platform_by_code(code: str) -> Optional[Dict]:
        query = """
            SELECT id, code, label
            FROM platforms
            WHERE lower(code) = lower(%s)
            LIMIT 1
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (code,))
            return cursor.fetchone()

    @staticmethod
    def list_push_devices(user_id: str) -> List[Dict]:
        query = """
            SELECT
                pd.id,
                pd.user_id,
                pd.platform_id,
                pd.push_token,
                pd.last_seen_at,
                pd.active,
                pf.code AS platform_code,
                pf.label AS platform_label
            FROM push_devices pd
            JOIN platforms pf ON pf.id = pd.platform_id
            WHERE pd.user_id = %s
            ORDER BY pd.last_seen_at DESC
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall() or []
            return list(rows)

    @staticmethod
    def find_push_device_by_token(user_id: str, push_token: str, platform_id: Optional[str]) -> Optional[Dict]:
        platform_clause = ""
        params: List[Any] = [user_id, push_token]

        if platform_id:
            platform_clause = " AND pd.platform_id = %s"
            params.append(platform_id)

        query = f"""
            SELECT
                pd.id,
                pd.user_id,
                pd.platform_id,
                pd.push_token,
                pd.last_seen_at,
                pd.active
            FROM push_devices pd
            WHERE pd.user_id = %s AND pd.push_token = %s{platform_clause}
            ORDER BY pd.last_seen_at DESC
            LIMIT 1
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            return cursor.fetchone()

    @staticmethod
    def get_push_device(user_id: str, device_id: str) -> Optional[Dict]:
        query = """
            SELECT
                pd.id,
                pd.user_id,
                pd.platform_id,
                pd.push_token,
                pd.last_seen_at,
                pd.active,
                pf.code AS platform_code,
                pf.label AS platform_label
            FROM push_devices pd
            JOIN platforms pf ON pf.id = pd.platform_id
            WHERE pd.user_id = %s AND pd.id = %s
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id, device_id))
            return cursor.fetchone()

    @staticmethod
    def create_push_device(
        user_id: str,
        *,
        platform_id: str,
        push_token: str,
        last_seen_at,
        active: bool,
    ) -> Optional[str]:
        query = """
            INSERT INTO push_devices (user_id, platform_id, push_token, last_seen_at, active)
            VALUES (%s, %s, %s, COALESCE(%s, NOW()), %s)
            RETURNING id
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id, platform_id, push_token, last_seen_at, active))
            created = cursor.fetchone()
            if not created:
                return None
            return str(created['id'])

    @staticmethod
    def update_push_device(
        user_id: str,
        device_id: str,
        updates: Dict[str, Any],
    ) -> Optional[str]:
        if not updates:
            return None

        set_parts = [f"{column} = %s" for column in updates.keys()]
        params: List[Any] = list(updates.values())
        params.extend([user_id, device_id])

        query = f"""
            UPDATE push_devices
            SET {', '.join(set_parts)}
            WHERE user_id = %s AND id = %s
            RETURNING id
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, tuple(params))
            updated = cursor.fetchone()
            if not updated:
                return None
            return str(updated['id'])

    @staticmethod
    def delete_push_device(user_id: str, device_id: str) -> bool:
        query = """
            DELETE FROM push_devices
            WHERE user_id = %s AND id = %s
            RETURNING id
        """
        with get_db_cursor() as cursor:
            cursor.execute(query, (user_id, device_id))
            deleted = cursor.fetchone()
            return bool(deleted)
