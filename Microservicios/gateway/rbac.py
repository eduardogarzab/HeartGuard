from typing import Dict, List, Optional

ALLOWED_ROUTES: Dict[str, List[str]] = {
    "/organization": ["admin", "org_admin"],
    "/media": ["admin", "org_admin", "user"],
    "/audit": ["admin", "org_admin"],
    "/timeseries/write": ["device", "system", "admin"],
    "/timeseries/query": ["admin", "org_admin", "user"],
    "/user/me": ["admin", "org_admin", "user"],
}


def _route_matches(path: str, prefix: str) -> bool:
    if prefix.endswith("*"):
        return path.startswith(prefix[:-1])
    return path == prefix or path.startswith(prefix + "/")


def check_access(user_role: Optional[str], request_path: str, jwt_sub: Optional[str], jwt_org_id: Optional[str], extra_context: Optional[Dict] = None) -> bool:
    if user_role == "admin":
        return True

    for prefix, roles in ALLOWED_ROUTES.items():
        if _route_matches(request_path, prefix):
            if user_role in roles:
                if request_path.startswith("/user/me"):
                    if extra_context and extra_context.get("requested_user_id") != jwt_sub and user_role not in {"org_admin"}:
                        return False
                if request_path.startswith("/media") and user_role == "user":
                    # users only access own resources; validations handled downstream using sub
                    return True
                if request_path.startswith("/organization") and user_role not in {"admin", "org_admin"}:
                    return False
                if request_path.startswith("/timeseries/query") and user_role == "user":
                    requested_user = (extra_context or {}).get("user_id")
                    return requested_user in (None, jwt_sub)
                return True
            return False

    # default allow for system/device paths explicitly covered above
    return user_role in {"device", "system"}
