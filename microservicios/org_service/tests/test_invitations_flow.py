import importlib
import sys
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_EMAIL = "ana.ruiz@heartguard.com"
ADMIN_PASSWORD = "Demo#2025"


def _load_services():
    auth_dir = REPO_ROOT / "microservicios" / "auth_service"
    org_dir = REPO_ROOT / "microservicios" / "org_service"

    sys.path.insert(0, str(auth_dir))
    auth_app_module = importlib.import_module("app")
    auth_db_module = importlib.import_module("db")
    sys.path.pop(0)

    # Reset generic module names so org_service can import its own versions
    for name in [
        "app",
        "config",
        "db",
        "repository",
        "responses",
        "routes.auth",
        "routes.users",
        "routes.invitations",
        "routes.orgs",
        "token_store",
    ]:
        sys.modules.pop(name, None)

    sys.path.insert(0, str(org_dir))
    org_app_module = importlib.import_module("app")
    sys.path.pop(0)

    return SimpleNamespace(
        auth_app=auth_app_module.create_app(),
        auth_db=auth_db_module,
        org_app=org_app_module.create_app(),
    )


def _fetch_scalar(db_module, sql, params=None):
    conn = db_module.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            row = cur.fetchone()
            return str(row[0]) if row and row[0] is not None else None
    finally:
        db_module.put_conn(conn)


def _cleanup(db_module, *, user_id=None, invitation_id=None, org_id=None):
    if not any([user_id, invitation_id]):
        return
    conn = db_module.get_conn()
    try:
        with conn.cursor() as cur:
            if user_id:
                cur.execute("DELETE FROM refresh_tokens WHERE user_id = %s", (user_id,))
                if org_id:
                    cur.execute(
                        "DELETE FROM user_org_membership WHERE user_id = %s AND org_id = %s",
                        (user_id, org_id),
                    )
                cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
            if invitation_id:
                cur.execute("DELETE FROM org_invitations WHERE id = %s", (invitation_id,))
        conn.commit()
    finally:
        db_module.put_conn(conn)


def _login(app, email, password, org_id):
    client = app.test_client()
    response = client.post(
        "/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-Org-ID": str(org_id)},
    )
    assert response.status_code == 200, response.get_json()
    payload = response.get_json()["data"]
    return payload["access_token"], payload["refresh_token"], payload["user"]


def _register_user(app, *, name, email, password, status_id):
    client = app.test_client()
    response = client.post(
        "/v1/users",
        json={
            "name": name,
            "email": email,
            "password": password,
            "user_status_id": status_id,
        },
    )
    assert response.status_code in (200, 201), response.get_json()
    return response.get_json()["data"]


@pytest.fixture(scope="module")
def services():
    return _load_services()


def test_invitation_acceptance_flow(services):
    auth_app = services.auth_app
    org_app = services.org_app
    db_module = services.auth_db

    family_org_id = _fetch_scalar(
        db_module,
        "SELECT id FROM organizations WHERE code = 'FAM-001' LIMIT 1",
    )
    if not family_org_id:
        pytest.skip("seed FAM-001 organization before running this test")

    active_status_id = _fetch_scalar(
        db_module,
        "SELECT id FROM user_statuses WHERE code = 'active' LIMIT 1",
    )
    if not active_status_id:
        pytest.skip("seed an 'active' entry in user_statuses before running this test")

    admin_access, _, admin_user = _login(
        auth_app,
        ADMIN_EMAIL,
        ADMIN_PASSWORD,
        family_org_id,
    )
    assert admin_user["org_id"] == family_org_id

    org_client = org_app.test_client()

    me_resp = org_client.get(
        "/v1/orgs/me",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert me_resp.status_code == 200
    admin_orgs = me_resp.get_json()["data"]["organizations"]
    assert any(org["id"] == family_org_id for org in admin_orgs)

    detail_resp = org_client.get(
        f"/v1/orgs/{family_org_id}",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert detail_resp.status_code == 200

    invite_email = f"member+{uuid.uuid4().hex[:8]}@heartguard.com"

    invite_resp = org_client.post(
        "/v1/invitations",
        json={"email": invite_email, "org_id": family_org_id, "role_code": "org_user"},
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert invite_resp.status_code == 201
    invitation = invite_resp.get_json()["data"]

    list_resp = org_client.get(
        f"/v1/invitations/org/{family_org_id}",
        headers={"Authorization": f"Bearer {admin_access}"},
    )
    assert list_resp.status_code == 200
    invitation_tokens = {
        entry["token"] for entry in list_resp.get_json()["data"]["invitations"]
    }
    assert invitation["token"] in invitation_tokens

    new_user_data = _register_user(
        auth_app,
        name="Miembro Demo",
        email=invite_email,
        password="Member#2025",
        status_id=active_status_id,
    )

    new_access, _, _ = _login(
        auth_app,
        invite_email,
        "Member#2025",
        family_org_id,
    )

    try:
        accept_resp = org_client.post(
            f"/v1/invitations/{invitation['token']}/accept",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert accept_resp.status_code == 200

        member_orgs_resp = org_client.get(
            "/v1/orgs/me",
            headers={"Authorization": f"Bearer {new_access}"},
        )
        assert member_orgs_resp.status_code == 200
        member_org_ids = {
            org["id"] for org in member_orgs_resp.get_json()["data"]["organizations"]
        }
        assert family_org_id in member_org_ids
    finally:
        _cleanup(
            db_module,
            user_id=new_user_data.get("id"),
            invitation_id=invitation.get("id"),
            org_id=family_org_id,
        )
